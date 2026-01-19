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

# --- 差值编码函数 ---
def delta_encode(sorted_ids):
    """差值编码：将排序ID转换为相邻差值"""
    if not sorted_ids or len(sorted_ids) == 0:
        return []

    deltas = [sorted_ids[0]]  # 第一个ID保持原值
    for i in range(1, len(sorted_ids)):
        deltas.append(sorted_ids[i] - sorted_ids[i-1])
    return deltas

from hsrwiki_data_parser.formatters.quest_formatter import QuestFormatter
from hsrwiki_data_parser.formatters.outfit_formatter import OutfitFormatter
from hsrwiki_data_parser.formatters.rogue_event_formatter import RogueEventFormatter
from hsrwiki_data_parser.formatters.message_formatter import MessageFormatter
from hsrwiki_data_parser.formatters.rogue_magic_scepter_formatter import RogueMagicScepterFormatter
from hsrwiki_data_parser.formatters.rogue_miracle_formatter import RogueMiracleFormatter
from hsrwiki_data_parser.formatters.lightcone_formatter import LightconeFormatter

# --- Config ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
CACHE_FILE_PATH = os.path.join(project_root, "hsrwiki_data_parser", "cache", "hsrwiki_data.cache.gz")
MARKDOWN_OUTPUT_DIR = "web/docs-site/public/domains/hsr/docs"
JSON_OUTPUT_DIR = "web/docs-site/public/domains/hsr/metadata"
LINK_DATA_DIR = "hsr_wiki_scraper/output/link"

# 分类规则映射：缓存属性名 -> 标签字段名（基于分析结果）
CLASSIFICATION_MAP = {
    "characters": "命途",     # 8个值：毁灭、同谐、丰饶、巡猎、智识、虚无、存护、记忆
    "lightcones": "命途",     # 8个值：与角色相同路径
    "quests": "类型",         # 6个值：活动任务、同行任务、开拓任务、冒险任务、日常任务、委托
    "materials": "复合分类",   # 特殊处理：类型 > 稀有度 > 用途
    "relics": "套装种类",     # 2个值：四件套空间站遗器、二件套连结绳
    "books": "地区",         # 5个值：雅利洛-VI、仙舟「罗浮」、匹诺康尼、空间站「黑塔」、翁法罗斯
    "outfits": "分类",       # 6个值：头饰、外套、饰品库、套机车、机甲、娱
}

# --- Helper Functions ---

def load_link_tags_data() -> Dict[str, Dict[str, Any]]:
    """
    从link目录加载标签数据

    Returns:
        分类ID到标签数据的映射，格式: {分类ID: {item_id: tags_dict}}
    """
    link_path = Path(LINK_DATA_DIR)
    if not link_path.exists():
        logging.warning(f"Link数据目录不存在: {LINK_DATA_DIR}")
        return {}

    tags_data = {}

    for json_file in link_path.glob("*.json"):
        if json_file.name == "categories.json":
            continue

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            category_id = json_file.stem  # 去掉.json后缀
            category_tags = {}

            for item in data:
                item_id = str(item.get('id', ''))
                tags = item.get('tags', {})
                if item_id:
                    category_tags[item_id] = tags

            tags_data[category_id] = category_tags
            logging.info(f"加载分类 {category_id} 的标签数据: {len(category_tags)} 条")

        except Exception as e:
            logging.error(f"加载标签文件 {json_file} 时出错: {e}")
            continue

    return tags_data


def get_tag_based_classification(item: Any, category_name: str) -> str:
    """
    根据标签获取分类值

    Args:
        item: 数据项
        category_name: 分类名称（如 "characters", "quests" 等）

    Returns:
        分类值字符串
    """
    if category_name not in CLASSIFICATION_MAP:
        return "未分类"

    classification_field = CLASSIFICATION_MAP[category_name]

    # 特殊处理 materials 的复合分类
    if classification_field == "复合分类":
        return get_materials_classification(item)

    # 优先使用对象的 tags 字段（从缓存中加载）
    tags = getattr(item, 'tags', None)

    # 如果对象没有 tags 字段，尝试从 GlobalTagManager 获取
    if not tags:
        from hsrwiki_data_parser.models._core import GlobalTagManager
        item_id = str(getattr(item, 'id', ''))
        tags = GlobalTagManager.get_tags(item_id)

    if not tags:
        return "未分类"

    # 获取分类字段值
    classification_value = tags.get(classification_field)
    if classification_value and str(classification_value).strip():
        return str(classification_value).strip()

    return "未分类"


def get_materials_classification(item: Any) -> str:
    """
    Materials 复合分类：优先级 类型 > 稀有度 > 用途

    Args:
        item: 材料数据项

    Returns:
        分类值字符串
    """
    # 从 GlobalTagManager 直接获取标签
    from hsrwiki_data_parser.models._core import GlobalTagManager
    item_id = str(getattr(item, 'id', ''))
    tags = GlobalTagManager.get_tags(item_id) or {}

    # 优先级顺序：类型 > 稀有度 > 用途
    for field in ["类型", "稀有度", "用途"]:
        value = tags.get(field)
        if value and str(value).strip():
            return str(value).strip()

    return "未分类"


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
            "sub_cat_func": lambda item: get_tag_based_classification(item, "characters"),
        },
        "lightcones": {
            "attr": "lightcones",
            "formatter": LightconeFormatter(),
            "sub_cat_func": lambda item: get_tag_based_classification(item, "lightcones"),
        },
        "relics": {
            "attr": "relics",
            "formatter": RelicFormatter(),
            "sub_cat_func": lambda item: get_tag_based_classification(item, "relics"),
        },
        "books": {
            "attr": "books",
            "formatter": BookFormatter(),
            "sub_cat_func": lambda item: get_tag_based_classification(item, "books"),
        },
        "materials": {
            "attr": "materials",
            "formatter": MaterialFormatter(),
            "sub_cat_func": lambda item: get_tag_based_classification(item, "materials"),
        },
        "quests": {
            "attr": "quests",
            "formatter": QuestFormatter(),
            "sub_cat_func": lambda item: get_tag_based_classification(item, "quests"),
        },
        "outfits": {
            "attr": "outfits",
            "formatter": OutfitFormatter(),
            "sub_cat_func": lambda item: get_tag_based_classification(item, "outfits"),
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
        "rogue_miracles": {
            "attr": "rogue_miracles",
            "formatter": RogueMiracleFormatter(),
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

                # 根据是否有分类来决定目录结构
                if cat_name in CLASSIFICATION_MAP and sub_category != "未分类":
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
            "sub_cat_func": lambda item: get_tag_based_classification(item, "characters"),
        },
        "lightcones": {
            "attr": "lightcones",
            "formatter": LightconeFormatter(),
            "sub_cat_func": lambda item: get_tag_based_classification(item, "lightcones"),
        },
        "relics": {
            "attr": "relics",
            "sub_cat_func": lambda item: get_tag_based_classification(item, "relics")
        },
        "books": {
            "attr": "books",
            "sub_cat_func": lambda item: get_tag_based_classification(item, "books")
        },
        "materials": {
            "attr": "materials",
            "sub_cat_func": lambda item: get_tag_based_classification(item, "materials"),
        },
        "quests": {
            "attr": "quests",
            "sub_cat_func": lambda item: get_tag_based_classification(item, "quests"),
        },
        "outfits": {
            "attr": "outfits",
            "sub_cat_func": lambda item: get_tag_based_classification(item, "outfits"),
        },
        "rogue_events": {
            "attr": "rogue_events",
            "sub_cat_func": lambda item: "模拟宇宙事件",
        },
        "rogue_magic_scepters": {
            "attr": "rogue_magic_scepters",
            "sub_cat_func": lambda item: "奇物",
        },
        "rogue_miracles": {
            "attr": "rogue_miracles",
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

                # 根据是否有分类来决定路径结构
                if cat_name in CLASSIFICATION_MAP and sub_category != "未分类":
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


def main():
    if not os.path.exists(CACHE_FILE_PATH):
        logging.error(
            f"Cache file '{CACHE_FILE_PATH}' not found. Please run hsrwiki_create_cache.py first."
        )
        sys.exit(1)

    # 初始化全局标签管理器
    from hsrwiki_data_parser.models._core import GlobalTagManager
    logging.info("Initializing GlobalTagManager...")
    GlobalTagManager.initialize(LINK_DATA_DIR)

    logging.info(f"Loading CacheService from '{CACHE_FILE_PATH}'...")
    cache_service = CacheService.load(CACHE_FILE_PATH)

    if not cache_service:
        logging.error("Failed to load CacheService from cache file.")
        sys.exit(1)

    logging.info("CacheService loaded successfully.")

    export_all_to_markdown(cache_service, MARKDOWN_OUTPUT_DIR)
    export_catalog_index(cache_service, JSON_OUTPUT_DIR)

    logging.info("Markdown files and catalog index generated successfully.")
    logging.info(f"  - Markdown: {Path(MARKDOWN_OUTPUT_DIR).resolve()}")
    logging.info(f"  - JSON Index: {Path(JSON_OUTPUT_DIR) / 'index.json'}")
    logging.info("Note: Search index will be generated by generate_all_catalog_trees.py")


if __name__ == "__main__":
    main()