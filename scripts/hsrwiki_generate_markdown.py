import os
import logging
import sys
import re
import json
import shutil
from typing import List, Dict, Any
from pathlib import Path
from collections import defaultdict

# --- Path Setup ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Use the new CacheService and Formatters
from hsrwiki_data_parser.services.cache_service import CacheService
from hsrwiki_data_parser.formatters.character_formatter import CharacterFormatter
from hsrwiki_data_parser.formatters.relic_formatter import RelicFormatter
from hsrwiki_data_parser.formatters.book_formatter import BookFormatter
from hsrwiki_data_parser.formatters.material_formatter import MaterialFormatter
from hsrwiki_data_parser.formatters.quest_formatter import QuestFormatter
from hsrwiki_data_parser.formatters.outfit_formatter import OutfitFormatter
from hsrwiki_data_parser.formatters.rogue_event_formatter import RogueEventFormatter
from hsrwiki_data_parser.formatters.message_formatter import MessageFormatter
from hsrwiki_data_parser.formatters.rogue_magic_scepter_formatter import RogueMagicScepterFormatter

# --- Config ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
CACHE_FILE_PATH = "hsrwiki_data_parser/cache/hsrwiki_data.cache.gz"
MARKDOWN_OUTPUT_DIR = "web/docs-site/public/domains/hsr/docs"
JSON_OUTPUT_DIR = "web/docs-site/public/domains/hsr/metadata"

# --- Helper Functions (from original script) ---


def clean_filename(name: str) -> str:
    if not isinstance(name, str):
        name = str(name)
    name = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9_-]", "", name)
    name = name.replace(" ", "-")
    name = name.strip()
    return name.lower()


def save_file(file_path: Path, content: str):
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        logging.debug(f"Saved file: {file_path}")
    except Exception as e:
        logging.error(f"Error saving file {file_path}: {e}")
        raise


# --- Export Logic ---


def export_all_to_markdown(cache: CacheService, output_dir_str: str):
    logging.info(f"Exporting all HSR-Wiki data to Markdown files...")
    output_dir = Path(output_dir_str)

    category_map = {
        "messages": {
            "attr": "messages",
            "formatter": MessageFormatter(),
            "sub_cat_func": lambda item: "短信",
        },
        "characters": {
            "attr": "characters",
            "formatter": CharacterFormatter(),
            "sub_cat_func": lambda item: "角色",
        },
        "relics": {
            "attr": "relics",
            "formatter": RelicFormatter(),
            "sub_cat_func": lambda item: "遗器",
        },
        "books": {
            "attr": "books",
            "formatter": BookFormatter(),
            "sub_cat_func": lambda item: "书籍",
        },
        "materials": {
            "attr": "materials",
            "formatter": MaterialFormatter(),
            "sub_cat_func": lambda item: (
                item.metadata.type if item.metadata else "材料"
            ),
        },
        "quests": {
            "attr": "quests",
            "formatter": QuestFormatter(),
            "sub_cat_func": lambda item: (
                item.metadata.task_type if item.metadata else "任务"
            ),
        },
        "outfits": {
            "attr": "outfits",
            "formatter": OutfitFormatter(),
            "sub_cat_func": lambda item: (
                item.metadata.type if item.metadata else "装扮"
            ),
        },
        "rogue_events": {
            "attr": "rogue_events",
            "formatter": RogueEventFormatter(),
            "sub_cat_func": lambda item: "模拟宇宙事件",
        },
        "rogue_magic_scepters": {
            "attr": "rogue_magic_scepters",
            "formatter": RogueMagicScepterFormatter(),
            "sub_cat_func": lambda item: "奇物",
        },
    }

    for cat_name, config in category_map.items():
        logging.info(f"  Processing category: {cat_name}...")
        items = getattr(cache, config["attr"], [])
        formatter = config["formatter"]
        sub_cat_func = config["sub_cat_func"]

        if not items:
            logging.warning(f"  No items found for category {cat_name}.")
            continue

        for item in items:
            try:
                item_id = item.id
                # Use 'name' attribute if available, otherwise use 'title' attribute
                item_name = getattr(item, 'name', getattr(item, 'title', '')) or f"{cat_name}-{item_id}"
                sub_category = sub_cat_func(item) or "Uncategorized"

                markdown_content = formatter.format(item)
                if not markdown_content:
                    logging.warning(
                        f"    Skipping {cat_name} ID '{item_id}' ({item_name}) due to empty markdown content."
                    )
                    continue

                cleaned_sub_cat = clean_filename(sub_category)
                cleaned_item_name = clean_filename(item_name)

                if cat_name in ["materials", "quests"]:
                    file_path = (
                        output_dir
                        / cat_name
                        / cleaned_sub_cat
                        / f"{cleaned_item_name}-{item_id}.md"
                    )
                else:
                    file_path = (
                        output_dir / cat_name / f"{cleaned_item_name}-{item_id}.md"
                    )

                save_file(file_path, markdown_content)
            except Exception as e:
                logging.error(
                    f"    Error processing {cat_name} item {getattr(item, 'id', 'N/A')}: {e}",
                    exc_info=True,
                )

    logging.info("Markdown export complete!")


def export_catalog_index(cache: CacheService, output_dir_str: str):
    logging.info("Exporting HSR-Wiki catalog index...")
    output_dir = Path(output_dir_str)
    catalog = []

    category_map = {
        "messages": {
            "attr": "messages",
            "formatter": MessageFormatter(),
            "sub_cat_func": lambda item: item.name,
        },
        "characters": {
            "attr": "characters",
            "formatter": CharacterFormatter(),
            "sub_cat_func": lambda item: (
                item.metadata.city_state
                if item.metadata and item.metadata.city_state
                else "未知阵营"
            ),
        },
        "relics": {"attr": "relics", "sub_cat_func": lambda item: "遗器"},
        "books": {"attr": "books", "sub_cat_func": lambda item: "书籍"},
        "materials": {
            "attr": "materials",
            "sub_cat_func": lambda item: (
                item.metadata.type if item.metadata else "材料"
            ),
        },
        "quests": {
            "attr": "quests",
            "sub_cat_func": lambda item: (
                item.metadata.task_type if item.metadata else "任务"
            ),
        },
        "outfits": {
            "attr": "outfits",
            "sub_cat_func": lambda item: (
                item.metadata.type if item.metadata else "装扮"
            ),
        },
        "rogue_events": {
            "attr": "rogue_events",
            "sub_cat_func": lambda item: "模拟宇宙事件",
        },
        "rogue_magic_scepters": {
            "attr": "rogue_magic_scepters",
            "sub_cat_func": lambda item: "奇物",
        },
    }

    for cat_name, config in category_map.items():
        items = getattr(cache, config["attr"], [])
        sub_cat_func = config["sub_cat_func"]

        for item in items:
            try:
                item_id = item.id
                # Use 'name' attribute if available, otherwise use 'title' attribute
                item_name = getattr(item, 'name', getattr(item, 'title', '')) or f"{cat_name}-{item_id}"
                sub_category = sub_cat_func(item) or "Uncategorized"

                cleaned_sub_cat = clean_filename(sub_category)
                cleaned_item_name = clean_filename(item_name)

                if cat_name in ["materials", "quests"]:
                    path = f"/v2/hsr/category/{cat_name}/{cleaned_sub_cat}/{cleaned_item_name}-{item_id}"
                    key = f"{cat_name}-{cleaned_sub_cat}-{item_id}"
                else:
                    path = f"/v2/hsr/category/{cat_name}/{cleaned_item_name}-{item_id}"
                    key = f"{cat_name}-{item_id}"

                cat_display_name = sub_category

                catalog.append(
                    {
                        "id": item_id,
                        "name": item_name,
                        "type": cat_name.capitalize(),
                        "category": cat_display_name,
                        "path": path,
                        "key": key,
                    }
                )
            except Exception as e:
                logging.error(
                    f"    Error processing catalog item {cat_name} {getattr(item, 'id', 'N/A')}: {e}",
                    exc_info=True,
                )

    output_path = output_dir / "index.json"
    save_file(output_path, json.dumps(catalog, ensure_ascii=False, indent=2))
    logging.info(f"Catalog index saved to: {output_path}")


def export_search_index_chunked(cache: CacheService, base_output_dir_str: str):
    """导出HSR-Wiki分片后的搜索索引 (修复版，与 hsr 版本结构一致)。"""
    logging.info("Exporting HSR-Wiki chunked search index...")
    base_output_dir = Path(base_output_dir_str)

    if not cache._search_index:
        logging.error("Search index is empty. Cannot export.")
        return

    # 使用 set 来自动处理重复的 ID
    chunked_index = defaultdict(lambda: defaultdict(set))
    full_index = cache._search_index

    for keyword, results in full_index.items():
        if not keyword: continue
        first_char = keyword[0]
        for item in results:
            # 核心改动：只提取 item['id']
            chunked_index[first_char][keyword].add(item['id'])

    output_chunk_dir = base_output_dir / "search"
    if output_chunk_dir.exists():
        shutil.rmtree(output_chunk_dir)
    output_chunk_dir.mkdir(parents=True, exist_ok=True)

    logging.info(f"Found {len(chunked_index)} chunks. Writing to files...")
    for char, chunk_data in chunked_index.items():
        # 核心改动：将 set 转换为 list
        final_chunk_data = {k: list(v) for k, v in chunk_data.items()}
        chunk_file_path = output_chunk_dir / f"{char}.json"
        save_file(
            chunk_file_path,
            json.dumps(final_chunk_data, ensure_ascii=False, separators=(",", ":")),
        )

    logging.info(f"Chunked search index saved to: {output_chunk_dir.resolve()}")


def main():
    if not os.path.exists(CACHE_FILE_PATH):
        logging.error(
            f"Cache file '{CACHE_FILE_PATH}' not found. Please run hsrwiki_create_cache.py first."
        )
        sys.exit(1)

    logging.info(f"Loading CacheService from '{CACHE_FILE_PATH}'...")
    cache_service = CacheService.load(CACHE_FILE_PATH)

    if not cache_service:
        logging.error("Failed to load CacheService from cache file.")
        sys.exit(1)

    logging.info("CacheService loaded successfully.")

    md_output_path = Path(MARKDOWN_OUTPUT_DIR)
    if md_output_path.exists():
        shutil.rmtree(md_output_path)

    export_all_to_markdown(cache_service, MARKDOWN_OUTPUT_DIR)
    export_catalog_index(cache_service, JSON_OUTPUT_DIR)
    export_search_index_chunked(cache_service, JSON_OUTPUT_DIR)

    logging.info(f"All HSR-Wiki files generated successfully.")


if __name__ == "__main__":
    main()