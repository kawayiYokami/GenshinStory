#!/usr/bin/env python3
"""本地搜索调试脚本：不依赖 HTTP，直接调用 search_service。"""

from __future__ import annotations

import argparse
import json
from typing import Any

from config import SUPPORTED_DOMAINS
from indexer import build_index_for_domain
from search_service import search_catalog, search_docs, invalidate_index


def _print_catalog(results: list[dict[str, Any]], limit: int) -> None:
    print(f"命中数量: {len(results)}")
    for idx, item in enumerate(results[:limit], start=1):
        print(
            f"{idx:>2}. [{item.get('score', 0):.3f}] "
            f"{item.get('name', '')} "
            f"(type={item.get('type', '')}, path={item.get('path', '')})"
        )


def _print_docs(result: dict[str, Any], limit: int) -> None:
    docs = result.get("results", []) or []
    print(f"命中数量: {len(docs)}")
    if result.get("message"):
        print(f"提示: {result['message']}")
    for idx, item in enumerate(docs[:limit], start=1):
        print(
            f"{idx:>2}. path={item.get('path', '')}, "
            f"hitCount={item.get('hitCount', 0)}, "
            f"totalLines={item.get('totalLines', 0)}"
        )
        hits = item.get("hits", []) or []
        for h in hits[:3]:
            print(f"    - L{h.get('line', '?')}: {h.get('snippet', '')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="调试 Tantivy 搜索（本地直连）")
    parser.add_argument("--domain", default="gi", choices=SUPPORTED_DOMAINS, help="域名")
    parser.add_argument("--query", default="派蒙", help="查询词")
    parser.add_argument(
        "--mode",
        default="catalog",
        choices=["catalog", "docs"],
        help="搜索模式",
    )
    parser.add_argument("--max-results", type=int, default=20, help="最大结果数")
    parser.add_argument("--doc-path", default=None, help="docs 模式下的路径过滤")
    parser.add_argument(
        "--generate-summary",
        action="store_true",
        help="docs 模式下启用摘要",
    )
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="执行搜索前先重建该域索引并清理缓存",
    )
    parser.add_argument(
        "--raw-json",
        action="store_true",
        help="输出原始 JSON",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=10,
        help="最多预览前 N 条结果",
    )
    args = parser.parse_args()

    if args.rebuild_index:
        print(f"[debug] 重建索引: {args.domain}")
        build_index_for_domain(args.domain)
        invalidate_index(args.domain)
        print("[debug] 索引重建完成，已清理缓存")

    if args.mode == "catalog":
        results = search_catalog(
            args.domain,
            args.query,
            max_results=args.max_results,
        )
        if args.raw_json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
            return
        _print_catalog(results, args.preview)
        return

    result = search_docs(
        args.domain,
        args.query,
        doc_path=args.doc_path,
        max_results=args.max_results,
        generate_summary=args.generate_summary,
    )
    if args.raw_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    _print_docs(result, args.preview)


if __name__ == "__main__":
    main()
