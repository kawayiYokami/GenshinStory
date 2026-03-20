#!/usr/bin/env python3
"""Tantivy 索引构建器：从 Markdown 文档构建全文搜索索引"""

import json
import re
import sys
import logging
import shutil
import uuid
from pathlib import Path

import tantivy

from config import (
    SUPPORTED_DOMAINS,
    get_docs_dir,
    get_metadata_dir,
    get_index_dir,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def clean_markdown(text: str) -> str:
    """清洗 Markdown，移除标记保留纯文本"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"#+\s?", "", text)
    text = re.sub(r"(\*\*|__)(.*?)(\*\*|__)", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)(\*|_)", r"\2", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"---+", "", text)
    text = re.sub(r"\|", " ", text)
    return text.strip()


def get_physical_path(item: dict, domain: str) -> str | None:
    """从索引条目的 frontend path 推导出相对文档路径（相对于 docs 目录）"""
    frontend_path = item.get("path", "")
    parts = frontend_path.split("/")
    # 格式: /v2/{domain}/category/{category}/.../{name}
    if len(parts) < 5:
        return None
    relative_path = "/".join(parts[4:])
    return f"{relative_path}.md"


def build_schema() -> tantivy.Schema:
    """构建 Tantivy schema"""
    builder = tantivy.SchemaBuilder()
    # name/content 采用“预分词后空格拼接”的文本，交给默认 tokenizer 按空白分词
    builder.add_text_field("name", stored=True, tokenizer_name="default")
    builder.add_text_field("name_cjk2", stored=False, tokenizer_name="default")
    builder.add_text_field("name_raw", stored=True, tokenizer_name="raw")
    builder.add_text_field("name_display", stored=True, tokenizer_name="raw")
    builder.add_text_field("content", stored=False, tokenizer_name="default")
    builder.add_text_field("content_cjk2", stored=False, tokenizer_name="default")
    builder.add_text_field("path_terms", stored=False, tokenizer_name="default")
    builder.add_text_field("path_terms_cjk2", stored=False, tokenizer_name="default")
    builder.add_text_field("path", stored=True, tokenizer_name="raw")
    builder.add_text_field("physical_path", stored=True, tokenizer_name="raw")
    builder.add_text_field("category", stored=True, tokenizer_name="raw")
    builder.add_text_field("doc_type", stored=True, tokenizer_name="raw")
    builder.add_unsigned_field("doc_id", stored=True, indexed=True)
    return builder.build()


def prepare_text_for_index(text: str) -> str:
    """索引前轻量规范化：不做人工分词，交给 Tantivy 原生 tokenizer。"""
    normalized = str(text or "").strip()
    if not normalized:
        return ""
    normalized = normalized.lower()
    normalized = re.sub(
        r"[\uff01-\uff5e]",
        lambda ch: chr(ord(ch.group(0)) - 0xFEE0),
        normalized,
    )
    normalized = normalized.replace("\u3000", " ")
    return normalized


def _iter_cjk2_tokens(text: str) -> list[str]:
    """为中文检索生成二元组 token（bigram）。"""
    normalized = prepare_text_for_index(text)
    if not normalized:
        return []

    tokens: list[str] = []
    seen: set[str] = set()
    # 中文连续串或英数串
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
    return tokens


def prepare_cjk2_text_for_index(text: str) -> str:
    """将文本转换为以空格连接的 CJK bigram token。"""
    return " ".join(_iter_cjk2_tokens(text))

def prepare_path_terms_for_index(relative_path: str) -> str:
    """
    从 docs 相对路径提取路径词条文本：
    仅使用目录段 + 文件名（去掉 .md）进行索引，不包含 docs 之前前缀。
    """
    normalized = str(relative_path or "").replace("\\", "/").strip("/")
    if not normalized:
        return ""

    segments = [seg for seg in normalized.split("/") if seg]
    if not segments:
        return ""

    segments[-1] = re.sub(r"\.md$", "", segments[-1], flags=re.IGNORECASE)
    return prepare_text_for_index(" ".join(segments))


# 内容长度上限，避免超大文档导致 writer 线程崩溃
MAX_CONTENT_LENGTH = 100_000


def build_index_for_domain(domain: str) -> None:
    """为指定域构建 Tantivy 索引"""
    docs_dir = get_docs_dir(domain)
    metadata_dir = get_metadata_dir(domain)
    index_dir = get_index_dir(domain)

    index_json_path = metadata_dir / "index.json"
    if not index_json_path.exists():
        logging.error(f"索引文件不存在: {index_json_path}")
        return

    with open(index_json_path, "r", encoding="utf-8") as f:
        index_data = json.load(f)

    logging.info(f"[{domain.upper()}] 加载了 {len(index_data)} 个索引条目")

    # 清理旧索引，重新创建目录
    if index_dir.exists():
        try:
            shutil.rmtree(index_dir)
        except PermissionError:
            # Try to fix permissions and retry
            def _on_error(func, path, exc_info):
                import os
                try:
                    os.chmod(path, 0o700)
                    func(path)
                except Exception as chmod_exc:
                    logging.error(f"无法修改权限并删除 {path}: {chmod_exc}")
            try:
                shutil.rmtree(index_dir, onerror=_on_error)
            except Exception as retry_exc:
                logging.error(f"重试删除索引目录失败: {retry_exc}")
        except OSError as e:
            logging.error(f"删除索引目录失败: {e}")
    index_dir.mkdir(parents=True, exist_ok=True)

    schema = build_schema()
    index = tantivy.Index(schema, path=str(index_dir))

    # 分配 256MB heap 给 writer
    writer = index.writer(heap_size=256 * 1024 * 1024)

    indexed_count = 0
    skipped_count = 0
    error_count = 0

    for item in index_data:
        item_id = item.get("id")
        item_name = item.get("name", "")
        item_type = item.get("type", "")
        item_category = item.get("category", "")

        relative_path = get_physical_path(item, domain)
        if not relative_path:
            skipped_count += 1
            continue

        md_file = docs_dir / relative_path
        if not md_file.exists():
            skipped_count += 1
            continue

        try:
            raw_content = md_file.read_text(encoding="utf-8")
        except Exception as e:
            logging.warning(f"读取文件失败 {md_file}: {e}")
            skipped_count += 1
            continue

        cleaned_content = clean_markdown(raw_content)
        if not cleaned_content:
            skipped_count += 1
            continue

        # 截断过长内容
        if len(cleaned_content) > MAX_CONTENT_LENGTH:
            cleaned_content = cleaned_content[:MAX_CONTENT_LENGTH]

        logical_path = relative_path
        try:
            doc_id_val = int(item_id) if item_id is not None else 0
        except (ValueError, TypeError):
            # Generate unique fallback ID to avoid duplicates
            doc_id_val = int(uuid.uuid4().int % (2**32))
            logging.warning(f"无法解析 item_id '{item_id}'，使用回退 ID {doc_id_val} (文档: {relative_path})")

        try:
            doc = tantivy.Document()
            normalized_name = prepare_text_for_index(item_name.replace("-", " "))
            normalized_content = prepare_text_for_index(cleaned_content)
            normalized_name_cjk2 = prepare_cjk2_text_for_index(item_name.replace("-", " "))
            normalized_content_cjk2 = prepare_cjk2_text_for_index(cleaned_content)
            normalized_path_terms = prepare_path_terms_for_index(relative_path)
            normalized_path_terms_cjk2 = prepare_cjk2_text_for_index(normalized_path_terms)
            doc.add_text("name", normalized_name)
            doc.add_text("name_cjk2", normalized_name_cjk2)
            doc.add_text("name_raw", str(item_name or "").strip().lower())
            doc.add_text("name_display", str(item_name or "").strip())
            doc.add_text("content", normalized_content)
            doc.add_text("content_cjk2", normalized_content_cjk2)
            doc.add_text("path_terms", normalized_path_terms)
            doc.add_text("path_terms_cjk2", normalized_path_terms_cjk2)
            doc.add_text("path", logical_path)
            doc.add_text("physical_path", relative_path)
            doc.add_text("category", item_category)
            doc.add_text("doc_type", item_type)
            doc.add_unsigned("doc_id", doc_id_val)
            writer.add_document(doc)
            indexed_count += 1
        except Exception as e:
            logging.warning(f"索引文档失败 {relative_path}: {e}")
            error_count += 1

    writer.commit()
    index.reload()

    logging.info(
        f"[{domain.upper()}] 索引构建完成: "
        f"已索引 {indexed_count}, 跳过 {skipped_count}, 失败 {error_count}"
    )


def main():
    domains = []
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.lower() in SUPPORTED_DOMAINS:
                domains.append(arg.lower())
    else:
        domains = list(SUPPORTED_DOMAINS)

    if not domains:
        logging.error(f"未指定有效的域。可用: {', '.join(SUPPORTED_DOMAINS)}")
        sys.exit(1)

    logging.info(f"将为以下域构建索引: {', '.join(d.upper() for d in domains)}")

    for domain in domains:
        logging.info(f"\n{'='*50}")
        logging.info(f"开始构建 {domain.upper()} 索引")
        logging.info(f"{'='*50}")
        build_index_for_domain(domain)

    logging.info("所有索引构建完成！")


if __name__ == "__main__":
    main()
