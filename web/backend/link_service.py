"""链接匹配服务：根据文件标题返回最可能的 wiki 链接"""

import json
import logging
import re
import threading
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import unquote

try:
    from config import SUPPORTED_LINK_DOMAINS, get_link_dir
except ImportError:  # pragma: no cover - 兼容包导入
    from .config import SUPPORTED_LINK_DOMAINS, get_link_dir

logger = logging.getLogger(__name__)

_link_cache: dict[str, dict[str, Any]] = {}
_link_cache_lock = threading.RLock()


def _compute_dir_mtime(root_dir: Path) -> float:
    latest = root_dir.stat().st_mtime
    for entry in root_dir.rglob("*.json"):
        try:
            mtime = entry.stat().st_mtime
        except FileNotFoundError:
            continue
        if mtime > latest:
            latest = mtime
    return latest


def _normalize_text(value: str) -> str:
    if not isinstance(value, str):
        return ""
    text = value.strip().lower()
    text = re.sub(
        r"[\uff01-\uff5e]",
        lambda ch: chr(ord(ch.group(0)) - 0xFEE0),
        text,
    )
    text = text.replace("\u3000", " ")
    text = re.sub(r'["\u201c\u201d\u2018\u2019]', '"', text)
    return text.strip()


def _collapse_text(value: str) -> str:
    normalized = _normalize_text(value)
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", normalized)


def _strip_bracket_suffix(value: str) -> str:
    text = value.strip()
    return re.sub(r"[\(\（\[\【].*?[\)\）\]\】]\s*$", "", text).strip()


def _extract_lookup_title(raw_title: str) -> str:
    if not isinstance(raw_title, str):
        return ""

    title = unquote(raw_title.strip())
    if not title:
        return ""

    title = title.replace("\\", "/")
    title = title.split("?")[0].split("#")[0].strip()
    title = title.split("/")[-1].strip()

    # 兼容诸如 "path/file.md:12:3" 的行号后缀
    title = re.sub(r":\d+(?::\d+)?$", "", title)
    title = re.sub(r"\.[A-Za-z0-9]+$", "", title)
    title = re.sub(r"[-_]\d+$", "", title)

    return title.strip()


def _build_domain_entries(domain: str) -> list[dict[str, str]]:
    link_dir = get_link_dir(domain)
    if not link_dir.exists():
        logger.warning("链接目录不存在: %s", link_dir)
        return []

    entries: list[dict[str, str]] = []
    for file_path in sorted(link_dir.glob("*.json")):
        if file_path.name == "categories.json":
            continue
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("加载链接文件失败: %s (%s)", file_path, exc)
            continue

        if not isinstance(payload, list):
            continue

        for item in payload:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            url = str(item.get("url", "")).strip()
            if not name or not url:
                continue
            entries.append(
                {
                    "id": str(item.get("id", "")).strip(),
                    "name": name,
                    "url": url,
                }
            )
    return entries


def _get_domain_entries(domain: str) -> list[dict[str, str]]:
    link_dir = get_link_dir(domain)
    if not link_dir.exists():
        return []

    current_mtime = _compute_dir_mtime(link_dir)
    with _link_cache_lock:
        cached = _link_cache.get(domain)
        if cached:
            cached_mtime = cached.get("mtime")
            cached_entries = cached.get("entries")
            if isinstance(cached_mtime, (int, float)) and cached_mtime >= current_mtime and isinstance(cached_entries, list):
                return cached_entries

        entries = _build_domain_entries(domain)
        _link_cache[domain] = {"mtime": current_mtime, "entries": entries}
        return entries


def _score_candidate(query: str, entry_name: str) -> float:
    query_norm = _normalize_text(query)
    name_norm = _normalize_text(entry_name)
    if not query_norm or not name_norm:
        return -1.0

    query_plain = _collapse_text(query_norm)
    name_plain = _collapse_text(name_norm)
    if not query_plain or not name_plain:
        return -1.0

    query_stripped = _collapse_text(_strip_bracket_suffix(query_norm))
    name_stripped = _collapse_text(_strip_bracket_suffix(name_norm))

    score = 0.0
    if name_norm == query_norm:
        score += 100.0
    if name_plain == query_plain:
        score += 95.0
    if query_stripped and name_stripped and name_stripped == query_stripped:
        score += 90.0
    if name_norm.startswith(query_norm):
        score += 70.0
    if query_norm in name_norm:
        score += 55.0
    if name_plain.startswith(query_plain):
        score += 45.0
    if query_plain in name_plain:
        score += 35.0

    ratio = SequenceMatcher(None, query_plain, name_plain).ratio()
    score += ratio * 20.0
    return score


def resolve_best_link(
    domain: str,
    raw_title: str,
    top_k: int = 3,
    min_score: float = 100.0,
) -> dict[str, Any]:
    if domain not in SUPPORTED_LINK_DOMAINS:
        return {
            "found": False,
            "domain": domain,
            "query": raw_title,
            "message": f"链接解析仅支持 {', '.join(SUPPORTED_LINK_DOMAINS)}",
        }

    lookup_title = _extract_lookup_title(raw_title)
    if not lookup_title:
        return {
            "found": False,
            "domain": domain,
            "query": raw_title,
            "message": "标题为空或无效",
        }

    entries = _get_domain_entries(domain)
    if not entries:
        return {
            "found": False,
            "domain": domain,
            "query": raw_title,
            "lookupTitle": lookup_title,
            "message": "链接数据库为空或未找到",
        }

    if top_k < 1:
        top_k = 1

    ranked: list[dict[str, Any]] = []
    for entry in entries:
        score = _score_candidate(lookup_title, entry["name"])
        ranked.append(
            {
                "id": entry.get("id", ""),
                "name": entry.get("name", ""),
                "url": entry.get("url", ""),
                "score": round(score, 3),
            }
        )

    ranked.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)
    high_conf = [item for item in ranked if float(item.get("score", 0.0)) >= float(min_score)]
    selected = high_conf[:top_k]
    enough = len(selected) >= top_k

    if not selected:
        return {
            "found": False,
            "domain": domain,
            "query": raw_title,
            "lookupTitle": lookup_title,
            "k": top_k,
            "minScore": min_score,
            "message": "未找到高置信度链接",
        }

    top1 = selected[0]
    return {
        "found": enough,
        "domain": domain,
        "query": raw_title,
        "lookupTitle": lookup_title,
        "k": top_k,
        "minScore": min_score,
        "enoughCandidates": enough,
        "matchedCount": len(selected),
        "matched": top1,
        "url": top1.get("url", ""),
        "matches": selected,
    }
