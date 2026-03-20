"""文档读取服务：读取 Markdown 文件并返回内容"""

import re
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from config import get_docs_dir, SUPPORTED_DOMAINS

logger = logging.getLogger(__name__)


def _normalize_path(raw_path: str, domain: str) -> str:
    """规范化文档路径，剥离已知前缀"""
    if not raw_path:
        return ""

    path = raw_path.strip()
    path = path.replace("\\", "/")
    # 去除 query/hash
    path = path.split("?")[0].split("#")[0]

    # 剥离各种已知前缀
    prefixes = [
        f"web/docs-site/public/domains/{domain}/docs/",
        f"public/domains/{domain}/docs/",
        f"domains/{domain}/docs/",
        f"/domains/{domain}/docs/",
        f"v2/{domain}/category/",
        f"/v2/{domain}/category/",
    ]
    for prefix in prefixes:
        if path.lower().startswith(prefix.lower()):
            path = path[len(prefix):]
            break
        idx = path.lower().find(prefix.lower())
        if idx >= 0:
            path = path[idx + len(prefix):]
            break

    # 去掉首尾斜杠
    path = path.strip("/")

    # URL 解码
    path = unquote(path)

    # 确保 .md 后缀
    if path and not path.lower().endswith(".md"):
        path = f"{path}.md"

    return path


def _resolve_safe_doc_path(docs_dir: Path, normalized_path: str) -> Optional[Path]:
    """将规范化路径解析为绝对路径，并阻止越界访问 docs 目录。"""
    docs_root = docs_dir.resolve()
    md_file = (docs_dir / normalized_path).resolve()
    try:
        md_file.relative_to(docs_root)
    except ValueError:
        return None
    return md_file


def _apply_line_ranges(content: str, line_ranges: list[str]) -> str:
    """应用行范围选择"""
    if not line_ranges:
        return content

    lines = content.split("\n")
    selected = set()

    for r in line_ranges:
        parts = r.split("-")
        if len(parts) == 2:
            try:
                start, end = int(parts[0]), int(parts[1])
                if start > len(lines):
                    continue
                for i in range(max(1, start), min(len(lines), end) + 1):
                    selected.add(i)
            except ValueError:
                continue

    if not selected:
        return "[通知] 指定的行号范围无效或完全超出文件范围。"

    sorted_lines = sorted(selected)
    return "\n".join(f"{ln} | {lines[ln - 1]}" for ln in sorted_lines)


def _strip_markdown(text: str) -> str:
    """简单的 Markdown 剥离"""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"#+\s?", "", text)
    text = re.sub(r"(\*\*|__)(.*?)(\*\*|__)", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)(\*|_)", r"\2", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text


def read_doc(
    domain: str,
    path: str,
    line_ranges: Optional[list[str]] = None,
    preserve_markdown: bool = False,
) -> dict:
    """读取文档并返回内容"""
    if domain not in SUPPORTED_DOMAINS:
        return {"path": path, "error": f"不支持的域: {domain}"}

    normalized = _normalize_path(path, domain)
    if not normalized:
        return {"path": path, "error": "路径无效"}

    docs_dir = get_docs_dir(domain)
    md_file = _resolve_safe_doc_path(docs_dir, normalized)
    if md_file is None:
        return {"path": path, "error": "路径无效"}

    if not md_file.exists():
        return {"path": path, "error": f"文档不存在: {normalized}"}

    try:
        full_content = md_file.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"读取文件失败 {md_file}: {e}")
        return {"path": path, "error": "读取失败"}

    lines = full_content.split("\n")
    total_lines = len(lines)
    total_tokens = len(full_content) // 2  # 粗略估算 token 数

    result: dict = {
        "path": normalized,
        "totalLines": total_lines,
        "totalTokens": total_tokens,
    }

    if line_ranges:
        content = _apply_line_ranges(full_content, line_ranges)
        result["content"] = content
        actual_lines = [l for l in content.split("\n") if l.strip()]
        if actual_lines:
            import re as _re
            first = _re.match(r"^(\d+)\s*\|", actual_lines[0])
            last = _re.match(r"^(\d+)\s*\|", actual_lines[-1])
            if first and last:
                result["lineRange"] = f"{first.group(1)}-{last.group(1)}"
        result["returnedTokens"] = len(content) // 2
        result["remainingTokens"] = max(0, total_tokens - result["returnedTokens"])
    else:
        if preserve_markdown:
            content = full_content
        else:
            content = _strip_markdown(full_content)
        result["content"] = content
        result["returnedTokens"] = len(content) // 2
        result["remainingTokens"] = max(0, total_tokens - result["returnedTokens"])

    return result


def read_raw_markdown(domain: str, path: str) -> str:
    """读取原始 Markdown 内容（用于前端 fetchMarkdownContent 替代）"""
    if domain not in SUPPORTED_DOMAINS:
        raise FileNotFoundError(f"不支持的域: {domain}")

    normalized = _normalize_path(path, domain)
    if not normalized:
        raise FileNotFoundError(f"路径无效: {path}")

    docs_dir = get_docs_dir(domain)
    md_file = _resolve_safe_doc_path(docs_dir, normalized)
    if md_file is None:
        raise FileNotFoundError(f"路径无效: {path}")

    if not md_file.exists():
        raise FileNotFoundError(f"文档不存在: {normalized}")

    return md_file.read_text(encoding="utf-8")
