#!/usr/bin/env python3
"""
根据 link/13_背包.json 中的“任务道具”标签，删除 structured_data/13_背包 下对应 JSON。

默认 dry-run，仅打印；传入 --apply 后执行删除。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Set


def collect_ids(link_json_path: Path) -> Set[str]:
    payload = json.loads(link_json_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"link 文件结构异常，应为 list: {link_json_path}")

    result: Set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        tags = item.get("tags") or {}
        if not isinstance(tags, dict):
            continue
        if str(tags.get("道具类型", "")).strip() != "任务道具":
            continue
        item_id = str(item.get("id", "")).strip()
        if item_id:
            result.add(item_id)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="删除 13_背包 中属于任务道具的 structured_data JSON。")
    parser.add_argument(
        "--link-json",
        default="gi_wiki_scraper/output/link/13_背包.json",
        help="link 文件路径",
    )
    parser.add_argument(
        "--structured-dir",
        default="gi_wiki_scraper/output/structured_data/13_背包",
        help="structured_data 目录路径",
    )
    parser.add_argument("--apply", action="store_true", help="执行删除（默认仅预览）")
    args = parser.parse_args()

    link_json = Path(args.link_json)
    structured_dir = Path(args.structured_dir)
    if not link_json.exists():
        raise SystemExit(f"link 文件不存在: {link_json}")
    if not structured_dir.exists() or not structured_dir.is_dir():
        raise SystemExit(f"structured_data 目录不存在: {structured_dir}")

    ids = collect_ids(link_json)
    targets = [structured_dir / f"{item_id}.json" for item_id in sorted(ids)]
    existing = [path for path in targets if path.exists()]
    missing = [path for path in targets if not path.exists()]

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] link={link_json}")
    print(f"[{mode}] structured_dir={structured_dir}")
    print(f"任务道具ID数: {len(ids)}")
    print(f"命中现有文件: {len(existing)}")
    print(f"缺失文件: {len(missing)}")

    for path in existing:
        if args.apply:
            path.unlink(missing_ok=True)
            print(f"deleted: {path}")
        else:
            print(f"would_delete: {path}")

    for path in missing:
        print(f"not_found: {path}")


if __name__ == "__main__":
    main()

