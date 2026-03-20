from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


REPO_ROOT = Path(__file__).resolve().parents[1]
MEME_ROOT = REPO_ROOT / "web" / "docs-site" / "public" / "meme"
MEME_DATA_PATH = MEME_ROOT / "memes_data.json"
OUTPUT_PATH = MEME_ROOT / "meme_index.json"
AGENTS_ROOT = MEME_ROOT / "agents"
DEFAULT_MEMES_ROOT = MEME_ROOT / "memes"

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
PRESET_ROLE_IDS = [
    "gi_nahida_role",
    "gi_mona_role",
    "gi_zhongli_role",
    "gi_furina_role",
    "hsr_ruanmei_role",
    "hsr_herta_role",
    "hsr_sparkle_role",
    "hsr_march7th_role",
]


def to_public_path(path: Path) -> str:
    relative = path.relative_to(MEME_ROOT.parent).as_posix()
    return f"/{relative}"


def load_emote_names() -> List[str]:
    if not MEME_DATA_PATH.exists():
        raise FileNotFoundError(f"未找到 {MEME_DATA_PATH}")

    data = json.loads(MEME_DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("memes_data.json 必须是对象结构")

    return list(data.keys())


def collect_files(folder: Path) -> List[str]:
    if not folder.exists() or not folder.is_dir():
        return []

    results: List[str] = []
    for item in sorted(folder.iterdir(), key=lambda x: x.name):
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
            results.append(to_public_path(item))
    return results


def collect_default_index(emote_names: List[str]) -> Dict[str, List[str]]:
    index: Dict[str, List[str]] = {}
    for emote in emote_names:
        files = collect_files(DEFAULT_MEMES_ROOT / emote)
        if files:
            index[emote] = files
    return index


def collect_agent_index(emote_names: List[str]) -> Dict[str, Dict[str, List[str]]]:
    agent_index: Dict[str, Dict[str, List[str]]] = {}
    for role_id in PRESET_ROLE_IDS:
        role_root = AGENTS_ROOT / role_id
        role_data: Dict[str, List[str]] = {}
        for emote in emote_names:
            files = collect_files(role_root / emote)
            if files:
                role_data[emote] = files
        agent_index[role_id] = role_data
    return agent_index


def main() -> None:
    emote_names = load_emote_names()
    output = {
        "version": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "emoteNames": emote_names,
        "default": collect_default_index(emote_names),
        "agents": collect_agent_index(emote_names),
    }

    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] 已生成: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
