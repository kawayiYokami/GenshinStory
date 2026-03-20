#!/usr/bin/env python3
"""
GI/HSR 文档运维刷新脚本（Linux 服务器友好）

用途：
1) 手动更新 web/docs-site/public/domains/gi/docs 后，重建前端目录/索引元数据
2) 触发后端 GI/HSR Tantivy 重建索引

默认行为（无参数）：
  - 运行 scripts/generate_all_catalog_trees.py
  - 触发 GI/HSR 索引重建（优先本机 API，失败回退到本地直调）

示例：
  python3 scripts/ops_refresh_gi_docs.py
  python3 scripts/ops_refresh_gi_docs.py --skip-catalog
  python3 scripts/ops_refresh_gi_docs.py --skip-backend-reindex
  python3 scripts/ops_refresh_gi_docs.py --reindex-mode local
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_generate_catalog() -> None:
    script_path = PROJECT_ROOT / "scripts" / "generate_all_catalog_trees.py"
    if not script_path.exists():
        raise FileNotFoundError(f"未找到脚本: {script_path}")

    print(f"[STEP] 生成 catalog/index: {script_path}")
    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(PROJECT_ROOT),
        check=True,
    )


TARGET_DOMAINS = ("gi", "hsr")


def rebuild_index_via_api(api_base: str, domain: str) -> None:
    url = f"{api_base.rstrip('/')}/api/debug/local-command"
    payload = {
        "action": "rebuild_index",
        "domain": domain,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    print(f"[STEP] 通过本机 API 触发索引重建({domain.upper()}): {url}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        if resp.status >= 400:
            raise RuntimeError(f"API 返回异常状态: {resp.status}, body={raw}")
        print(f"[OK] API 重建完成: {raw[:300]}")


def rebuild_index_local(domain: str) -> None:
    print(f"[STEP] 本地直调重建 {domain.upper()} 索引（不依赖后端进程）")
    backend_dir = PROJECT_ROOT / "web" / "backend"
    if not backend_dir.exists():
        raise FileNotFoundError(f"后端目录不存在: {backend_dir}")

    inline = (
        "from indexer import build_index_for_domain\n"
        "from search_service import invalidate_index\n"
        f"build_index_for_domain('{domain}')\n"
        f"invalidate_index('{domain}')\n"
        f"print('{domain} local rebuild done')\n"
    )
    subprocess.run(
        [sys.executable, "-c", inline],
        cwd=str(backend_dir),
        check=True,
    )


def rebuild_backend_index(mode: str, api_base: str) -> None:
    if mode == "api":
        for domain in TARGET_DOMAINS:
            rebuild_index_via_api(api_base, domain)
        return
    if mode == "local":
        for domain in TARGET_DOMAINS:
            rebuild_index_local(domain)
        return

    # auto: 优先 API，失败后回退本地
    for domain in TARGET_DOMAINS:
        try:
            rebuild_index_via_api(api_base, domain)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError) as exc:
            print(f"[WARN] {domain.upper()} API 触发失败，回退本地重建: {exc}")
            rebuild_index_local(domain)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GI/HSR 文档刷新运维脚本：重建目录树并触发后端索引重建。"
    )
    parser.add_argument(
        "--skip-catalog",
        action="store_true",
        help="跳过 generate_all_catalog_trees.py",
    )
    parser.add_argument(
        "--skip-backend-reindex",
        action="store_true",
        help="跳过后端索引重建（GI+HSR）",
    )
    parser.add_argument(
        "--reindex-mode",
        choices=["auto", "api", "local"],
        default="auto",
        help="索引重建模式：auto(默认)/api/local",
    )
    parser.add_argument(
        "--api-base",
        default="http://127.0.0.1:8000",
        help="后端 API 基地址（仅 api/auto 模式使用）",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if not args.skip_catalog:
            run_generate_catalog()
        else:
            print("[SKIP] 已跳过 catalog/index 生成")

        if not args.skip_backend_reindex:
            rebuild_backend_index(args.reindex_mode, args.api_base)
        else:
            print("[SKIP] 已跳过后端 GI 索引重建")

        print("[DONE] GI+HSR 运维刷新完成")
        return 0
    except Exception as exc:
        print(f"[ERROR] 执行失败: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
