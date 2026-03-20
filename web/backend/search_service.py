"""搜索服务：基于 Tantivy 的全文搜索"""

import re
import logging
import threading
from pathlib import Path
from typing import Optional

import tantivy

from config import get_index_dir, get_docs_dir, SUPPORTED_DOMAINS

logger = logging.getLogger(__name__)

# 域 -> {"index": Index, "mtime": float} 的缓存
_index_cache: dict[str, dict[str, object]] = {}
_index_cache_lock = threading.RLock()

# 双通道融合权重（可按线上效果调整）
FUSION_WEIGHT_EXACT = 1.0
FUSION_WEIGHT_CJK2 = 1.0


def _compute_index_mtime(index_dir: Path) -> float:
    """计算索引目录及其内容的最新 mtime，用于缓存失效。"""
    latest = index_dir.stat().st_mtime
    for entry in index_dir.rglob("*"):
        try:
            mtime = entry.stat().st_mtime
        except FileNotFoundError:
            continue
        if mtime > latest:
            latest = mtime
    return latest


def invalidate_index(domain: Optional[str] = None) -> None:
    """失效缓存。domain 为 None 时清空全部缓存。"""
    with _index_cache_lock:
        if domain is None:
            _index_cache.clear()
            return
        _index_cache.pop(domain, None)


def _get_index(domain: str) -> tantivy.Index:
    """获取或创建指定域的 Tantivy Index 实例（带缓存）"""
    index_dir = get_index_dir(domain)
    if not index_dir.exists():
        raise FileNotFoundError(f"索引目录不存在: {index_dir}，请先运行 indexer.py")
    current_mtime = _compute_index_mtime(index_dir)

    with _index_cache_lock:
        cached = _index_cache.get(domain)
        if cached:
            cached_mtime = cached.get("mtime")
            if isinstance(cached_mtime, (int, float)) and cached_mtime >= current_mtime:
                cached_index = cached.get("index")
                if isinstance(cached_index, tantivy.Index):
                    return cached_index

        from indexer import build_schema, build_index_for_domain
        schema = build_schema()
        try:
            index = tantivy.Index(schema, path=str(index_dir))
        except ValueError as exc:
            # 典型场景：代码升级后 schema 变化，但磁盘仍是旧索引。
            if "schema does not match" not in str(exc).lower():
                raise
            logger.warning("域 %s 索引 schema 不匹配，尝试自动重建索引", domain)
            build_index_for_domain(domain)
            current_mtime = _compute_index_mtime(index_dir)
            index = tantivy.Index(schema, path=str(index_dir))
        index.reload()
        _index_cache[domain] = {"index": index, "mtime": current_mtime}
        return index


def _normalize_query(query: str) -> str:
    """规范化搜索查询"""
    if not isinstance(query, str):
        return ""
    result = query.strip().lower()
    # 全角转半角
    result = re.sub(
        r"[\uff01-\uff5e]",
        lambda ch: chr(ord(ch.group(0)) - 0xFEE0),
        result,
    )
    result = result.replace("\u3000", " ")  # 全角空格
    result = re.sub(r'["\u201c\u201d\u2018\u2019]', '"', result)
    result = re.sub(r'^"+|"+$', "", result)
    return result.strip()


def _tokenize_query_native(query: str) -> str:
    normalized = _normalize_query(query)
    if not normalized:
        return ""
    # 不做人工分词，仅做基础切分用于构造 AND 查询。
    fallback = re.split(r"[^\w\u4e00-\u9fff]+", normalized.lower())
    tokens = [token for token in fallback if token]
    return " ".join(tokens)


def _escape_query_term(term: str) -> str:
    """转义 Tantivy query parser 中的保留字符。"""
    escaped = term.replace("\\", "\\\\").replace('"', '\\"')
    escaped = re.sub(r"([+\-!(){}\[\]^~*?:/])", r"\\\1", escaped)
    return escaped


def _build_all_terms_query(tokenized_query: str) -> str:
    """构建“所有词都必须命中”的查询串。"""
    terms = [t for t in tokenized_query.split() if t]
    if not terms:
        return ""
    return " ".join(f'+{_escape_query_term(term)}' for term in terms)


def _build_any_terms_query(tokenized_query: str) -> str:
    """构建“任一词命中即可”的查询串（用于 CJK2 召回通道）。"""
    terms = [t for t in tokenized_query.split() if t]
    if not terms:
        return ""
    return " ".join(_escape_query_term(term) for term in terms)


def _tokenize_query_cjk2(query: str) -> str:
    """将查询转换为 CJK bigram token 串。"""
    normalized = _normalize_query(query)
    if not normalized:
        return ""

    tokens: list[str] = []
    seen: set[str] = set()
    parts = re.findall(r"[\u4e00-\u9fff]+|[a-z0-9_]+", normalized)
    for part in parts:
        if re.search(r"[\u4e00-\u9fff]", part):
            if len(part) <= 1:
                if part not in seen:
                    seen.add(part)
                    tokens.append(part)
                continue
            for i in range(len(part) - 1):
                bg = part[i:i + 2]
                if bg not in seen:
                    seen.add(bg)
                    tokens.append(bg)
        else:
            if part not in seen:
                seen.add(part)
                tokens.append(part)
    return " ".join(tokens)


def _name_match_bonus(name_raw: str, normalized_query: str) -> float:
    name = str(name_raw or "").lower()
    query = str(normalized_query or "").lower()
    if not name or not query:
        return 0.0
    bonus = 0.0
    if name == query:
        bonus += 2.0
    if name.startswith(query):
        bonus += 1.0
    if query in name:
        bonus += 0.6
    return bonus


def _build_fused_candidates(index: tantivy.Index, query: str, hit_limit: int) -> list[dict]:
    """并行融合 exact 与 cjk2 两个通道的召回结果。"""
    normalized = _normalize_query(query)
    tokenized_exact = _tokenize_query_native(normalized)
    tokenized_cjk2 = _tokenize_query_cjk2(normalized)
    if not tokenized_exact and not tokenized_cjk2:
        return []

    searcher = index.searcher()
    merged: dict[str, dict] = {}

    def _upsert_channel_hits(hits, channel: str) -> None:
        for score, doc_address in hits:
            doc = searcher.doc(doc_address)
            path = str(_doc_first(doc, "path", "") or "")
            if not path:
                continue
            item = merged.get(path)
            if item is None:
                item = {
                    "path": path,
                    "doc": doc,
                    "exact_score": 0.0,
                    "cjk2_score": 0.0,
                    "final_score": 0.0,
                }
                merged[path] = item
            if channel == "exact":
                item["exact_score"] = max(float(item["exact_score"]), float(score))
            else:
                item["cjk2_score"] = max(float(item["cjk2_score"]), float(score))

    if tokenized_exact:
        parsed_exact = index.parse_query(
            _build_all_terms_query(tokenized_exact),
            ["name", "content", "path_terms"],
        )
        search_result_exact = searcher.search(parsed_exact, limit=hit_limit)
        _upsert_channel_hits(search_result_exact.hits, "exact")

    if tokenized_cjk2:
        parsed_cjk2 = index.parse_query(
            _build_any_terms_query(tokenized_cjk2),
            ["name_cjk2", "content_cjk2", "path_terms_cjk2"],
        )
        search_result_cjk2 = searcher.search(parsed_cjk2, limit=hit_limit)
        _upsert_channel_hits(search_result_cjk2.hits, "cjk2")

    for item in merged.values():
        doc = item["doc"]
        name_raw = str(_doc_first(doc, "name_raw", "") or "")
        bonus = _name_match_bonus(name_raw, normalized)
        item["final_score"] = (
            float(item["exact_score"]) * FUSION_WEIGHT_EXACT
            + float(item["cjk2_score"]) * FUSION_WEIGHT_CJK2
            + bonus
        )

    candidates = list(merged.values())
    candidates.sort(
        key=lambda item: (
            float(item.get("final_score", 0.0)),
            float(item.get("exact_score", 0.0)),
            float(item.get("cjk2_score", 0.0)),
        ),
        reverse=True,
    )
    return candidates


def _extract_snippets(
    content: str, query: str, max_snippets: int = 3, snippet_max_len: int = 80
) -> list[dict]:
    """从文档内容中提取匹配的代码片段"""
    lines = content.split("\n")
    snippets = []
    query_lower = query.lower()

    for i, line in enumerate(lines):
        if query_lower in line.lower():
            snippet_text = line.strip()
            if len(snippet_text) > snippet_max_len:
                snippet_text = snippet_text[:snippet_max_len] + "..."
            snippets.append({"line": i + 1, "snippet": snippet_text})
            if len(snippets) >= max_snippets:
                break

    return snippets


def _doc_first(doc: tantivy.Document, field: str, default: object = ""):
    """安全读取 Tantivy Document 字段的第一个值。"""
    try:
        values = doc[field]
    except (KeyError, TypeError):
        return default
    if isinstance(values, list) and values:
        return values[0]
    return default


def search_catalog(
    domain: str,
    query: str,
    max_results: int = 100,
) -> list[dict]:
    """目录搜索：返回匹配的目录条目（用于 SearchView UI）"""
    if domain not in SUPPORTED_DOMAINS:
        return []

    query = _normalize_query(query)
    if not query:
        return []
    tokenized_query = _tokenize_query_native(query)
    tokenized_cjk2 = _tokenize_query_cjk2(query)
    if not tokenized_query and not tokenized_cjk2:
        return []

    try:
        index = _get_index(domain)
    except FileNotFoundError:
        logger.error(f"域 {domain} 的索引未构建")
        return []

    candidates = _build_fused_candidates(index, query, hit_limit=max_results * 8)

    results = []
    for candidate in candidates:
        doc = candidate["doc"]
        name_raw = _doc_first(doc, "name_raw", "")
        display_name = _doc_first(doc, "name_display", "") or _doc_first(doc, "name", "")
        path = _doc_first(doc, "path", "")

        exact_name = str(name_raw or "").lower() == query.lower()
        prefix_name = str(name_raw or "").lower().startswith(query.lower())
        contains_name = query.lower() in str(name_raw or "").lower()
        results.append({
            "id": _doc_first(doc, "doc_id", 0),
            "name": display_name,
            "type": _doc_first(doc, "doc_type", ""),
            "path": path,
            "category": _doc_first(doc, "category", ""),
            "score": float(candidate.get("final_score", 0.0)),
            "_exact_name": exact_name,
            "_prefix_name": prefix_name,
            "_contains_name": contains_name,
        })

    results.sort(
        key=lambda item: (
            item.get("_exact_name", False),
            item.get("_prefix_name", False),
            item.get("_contains_name", False),
            float(item.get("score", 0.0)),
        ),
        reverse=True,
    )
    trimmed = results[:max_results]
    for item in trimmed:
        item.pop("_exact_name", None)
        item.pop("_prefix_name", None)
        item.pop("_contains_name", None)
    return trimmed


def search_docs(
    domain: str,
    query: str,
    doc_path: Optional[str] = None,
    max_results: int = 50,
    generate_summary: bool = False,
) -> dict:
    """深度文档搜索：返回匹配的文档及代码片段（用于 Agent 工具）"""
    if domain not in SUPPORTED_DOMAINS:
        return {
            "tool": "search_docs",
            "query": query,
            "message": f"不支持的域: {domain}",
        }

    normalized = _normalize_query(query)
    if not normalized:
        return {
            "tool": "search_docs",
            "query": query,
            "message": "请输入有效的查询词",
        }
    tokenized_query = _tokenize_query_native(normalized)
    tokenized_cjk2 = _tokenize_query_cjk2(normalized)
    if not tokenized_query and not tokenized_cjk2:
        return {
            "tool": "search_docs",
            "query": query,
            "message": "请输入有效的查询词",
        }

    try:
        index = _get_index(domain)
    except FileNotFoundError:
        return {
            "tool": "search_docs",
            "query": query,
            "message": f"域 {domain} 的索引未构建",
        }

    candidates = _build_fused_candidates(index, normalized, hit_limit=max_results * 10)

    docs_dir = get_docs_dir(domain)
    grouped: dict[str, dict] = {}

    snippet_terms: list[str] = []
    if normalized:
        snippet_terms.append(normalized)
    for term in tokenized_query.split():
        if term and term not in snippet_terms:
            snippet_terms.append(term)
    if not snippet_terms:
        snippet_terms = [query]

    for candidate in candidates:
        doc = candidate["doc"]
        path = _doc_first(doc, "path", "")
        physical_path = _doc_first(doc, "physical_path", "")
        name_raw = str(_doc_first(doc, "name_raw", "") or "")

        # 路径过滤
        if doc_path:
            filter_lower = doc_path.lower()
            if filter_lower not in path.lower():
                continue

        if path in grouped:
            continue

        # 读取原文件提取 snippets
        md_file = docs_dir / physical_path
        total_lines = 0
        total_tokens = 0
        hits = []
        content = ""

        if md_file.exists():
            try:
                content = md_file.read_text(encoding="utf-8")
                lines = content.split("\n")
                total_lines = len(lines)
                total_tokens = len(content) // 2  # 粗略估算

                for term in snippet_terms:
                    hits.extend(_extract_snippets(content, term))
                # 去重
                seen = set()
                unique_hits = []
                for h in hits:
                    key = h["line"]
                    if key not in seen:
                        seen.add(key)
                        unique_hits.append(h)
                hits = unique_hits[:3]
            except Exception as e:
                logger.exception("读取搜索命中文档失败: domain=%s file=%s err=%s", domain, md_file, e)

        hit_count = len(hits)
        contains_in_path = normalized in path.lower()
        contains_in_name = normalized in name_raw.lower()
        if not hits and not contains_in_path and not contains_in_name:
            continue

        grouped[path] = {
            "path": path,
            "totalLines": total_lines,
            "totalTokens": total_tokens,
            "hits": hits,
            "hitCount": hit_count,
            "score": float(candidate.get("final_score", 0.0)),
        }

        if len(grouped) >= max_results:
            break

    results = list(grouped.values())
    # 先按 hitCount，再按融合分
    results.sort(key=lambda r: (r["hitCount"], float(r.get("score", 0.0))), reverse=True)

    response: dict = {
        "tool": "search_docs",
        "query": query,
        "results": results,
        "grouped": True,
    }

    if doc_path:
        response["docPath"] = doc_path

    if generate_summary and results:
        top_files = ", ".join(
            r["path"].split("/")[-1] for r in results[:3]
        )
        response["message"] = f"找到 {len(results)} 个相关文件，主要包括：{top_files}等。"

    if not results:
        response["message"] = "在指定路径中未找到相关内容" if doc_path else "未找到相关文档"

    return response
