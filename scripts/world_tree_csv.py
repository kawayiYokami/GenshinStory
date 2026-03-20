#!/usr/bin/env python3
"""世界树记忆 CSV 导入/导出脚本。"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable, List


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "web" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from world_tree_service import world_tree_memory_service  # noqa: E402


CSV_COLUMNS = [
    "id",
    "judgment",
    "reasoning",
    "keywords",
    "metadata",
    "createdAt",
    "updatedAt",
]


def _safe_text(value: object) -> str:
    return str(value or "").strip()


def _parse_keywords(value: str) -> List[str]:
    text = _safe_text(value)
    if not text:
        return []
    normalized = text.replace("，", "|").replace(",", "|").replace("\n", "|")
    parts = [part.strip() for part in normalized.split("|")]
    return [part for part in parts if part]


def _format_keywords(values: Iterable[str]) -> str:
    keywords = [_safe_text(v) for v in values]
    return "|".join([k for k in keywords if k])


def _parse_metadata(value: str) -> dict:
    text = _safe_text(value)
    if not text:
        return {}
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    return {}


def export_csv(output_path: Path) -> None:
    records = world_tree_memory_service.list_records()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in records:
            writer.writerow(
                {
                    "id": _safe_text(row.get("id")),
                    "judgment": _safe_text(row.get("judgment")),
                    "reasoning": _safe_text(row.get("reasoning")),
                    "keywords": _format_keywords(row.get("keywords", [])),
                    "metadata": json.dumps(row.get("metadata", {}), ensure_ascii=False),
                    "createdAt": _safe_text(row.get("createdAt")),
                    "updatedAt": _safe_text(row.get("updatedAt")),
                }
            )
    print(f"[export] done, records={len(records)}, file={output_path}")


def import_csv(input_path: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"CSV 文件不存在: {input_path}")

    imported = 0
    skipped = 0
    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            record_id = _safe_text(row.get("id"))
            judgment = _safe_text(row.get("judgment"))
            if not record_id or not judgment:
                skipped += 1
                continue
            payload = {
                "id": record_id,
                "judgment": judgment,
                "reasoning": _safe_text(row.get("reasoning")),
                "keywords": _parse_keywords(_safe_text(row.get("keywords"))),
                "metadata": _parse_metadata(_safe_text(row.get("metadata"))),
                "createdAt": _safe_text(row.get("createdAt")) or None,
                "updatedAt": _safe_text(row.get("updatedAt")) or None,
                "memoryType": "world_tree",
            }
            world_tree_memory_service.upsert(payload)
            imported += 1
    print(f"[import] done, imported={imported}, skipped={skipped}, file={input_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="世界树记忆 CSV 导入/导出")
    sub = parser.add_subparsers(dest="cmd", required=True)

    export_p = sub.add_parser("export", help="导出世界树记忆到 CSV")
    export_p.add_argument("--file", required=True, help="输出 CSV 路径")

    import_p = sub.add_parser("import", help="从 CSV 导入世界树记忆")
    import_p.add_argument("--file", required=True, help="输入 CSV 路径")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        csv_file = Path(args.file).resolve()
        if args.cmd == "export":
            export_csv(csv_file)
        elif args.cmd == "import":
            import_csv(csv_file)
        else:
            parser.error(f"未知命令: {args.cmd}")
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
