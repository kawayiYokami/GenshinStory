import os
import logging
import sys
import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

# 在导入我们自己的模块之前设置好路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from giwiki_data_parser.main import GiWikiDataParser

# --- 差值编码函数 ---
def delta_encode(sorted_ids):
    """差值编码：将排序ID转换为相邻差值"""
    if not sorted_ids or len(sorted_ids) == 0:
        return []

    deltas = [sorted_ids[0]]  # 第一个ID保持原值
    for i in range(1, len(sorted_ids)):
        deltas.append(sorted_ids[i] - sorted_ids[i-1])
    return deltas

# --- 配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
CACHE_FILE_PATH = "giwiki_data_parser/cache/giwiki_data.cache.gz"
MARKDOWN_OUTPUT_DIR = "web/docs-site/public/domains/gi/docs"
JSON_OUTPUT_DIR = "web/docs-site/public/domains/gi/metadata"

# 分类规则映射：数据类型 -> 标签字段名
CLASSIFICATION_MAP = {
    "211_装扮": "装扮分类",
    "25_角色": "地区",
    "5_武器": "武器类型",
    "218_圣遗物": "星级",
    "6_敌人": "元素",
    "49_动物": "动物类型",
    "13_背包": "道具类型",
    "20_NPC&商店": "地区",
    "255_组织": "地区",
    "261_角色逸闻": "地区",
    "251_地图文本": "地区",
    "21_食物": "食物类型",
    "54_秘境": "秘境类型",
    "43_任务": "任务类型",
    "55_冒险家协会": "委托类型",
    "68_书籍": "书籍类型",
}

def clean_filename(name: str) -> str:
    """清理字符串，使其适合作为文件路径的一部分（目录名或文件名）。"""
    if not isinstance(name, str):
        name = str(name)
    # 将所有非法字符（包括&符号、空格等）替换为中划线
    name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9_-]+', '-', name)
    name = name.strip('-')  # 移除首尾可能出现的中划线
    return name

def save_file(file_path: Path, content: str):
    """
    将内容保存到指定路径的文件中，并确保目录存在。
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        logging.debug(f"已保存文件: {file_path}")
    except Exception as e:
        logging.error(f"保存文件 {file_path} 时出错: {e}")
        raise

def load_cache_data(cache_path: str) -> Dict[str, Any]:
    """从缓存文件加载数据。"""
    if not os.path.exists(cache_path):
        raise FileNotFoundError(f"缓存文件不存在: {cache_path}")

    # 使用 pickle 从 gzip 压缩文件加载缓存对象
    import pickle
    from giwiki_data_parser.services.cache_service import CacheService

    cache_service = CacheService.load(cache_path)

    # 将缓存服务对象转换为字典格式以兼容现有代码
    cache_data = {
        'parser_cache': {
            'characters': cache_service.characters,
            'quests': cache_service.quests,
            'books': cache_service.books,
            'weapons': cache_service.weapons,
            'artifacts': cache_service.artifacts,
            'enemies': cache_service.enemies,
            'animals': cache_service.animals,
            'inventory_items': cache_service.inventory_items,
            'npc_shops': cache_service.npc_shops,
            'organizations': cache_service.organizations,
            'character_stories': cache_service.character_stories,
            'map_texts': cache_service.map_texts,
            'adventurer_guild_tasks': cache_service.adventurer_guild_tasks,
            'food': cache_service.foods,
            'domains': cache_service.domains,
            'outfits': cache_service.outfits,
        },
        'search_index': cache_service._search_index
    }

    return cache_data

def get_cache_type_mapping() -> Dict[str, str]:
    """获取缓存类型名到标准数据类型名的映射"""
    return {
        'characters': '25_角色',
        'quests': '43_任务',
        'books': '68_书籍',
        'weapons': '5_武器',
        'artifacts': '218_圣遗物',
        'enemies': '6_敌人',
        'animals': '49_动物',
        'inventory_items': '13_背包',
        'npc_shops': '20_NPC&商店',
        'organizations': '255_组织',
        'character_stories': '261_角色逸闻',
        'map_texts': '251_地图文本',
        'adventurer_guild_tasks': '55_冒险家协会',
        'food': '21_食物',
        'domains': '54_秘境',
        'outfits': '211_装扮',
    }

def export_all_to_markdown_from_cache(cache_data: Dict[str, Any], output_dir: str, classification_map: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    完全基于缓存数据生成markdown文件（修复版本）

    Args:
        cache_data: 缓存数据字典
        output_dir: 输出目录
        classification_map: 分类映射表

    Returns:
        元数据索引列表
    """
    logging.info("开始基于缓存数据导出所有数据到Markdown文件")
    metadata_index = []
    type_mapping = get_cache_type_mapping()

    # 遍历所有缓存的数据类型
    for cache_type, data_type in type_mapping.items():
        items = cache_data['parser_cache'].get(cache_type, [])
        if not items:
            logging.info(f"  跳过空的数据类型: {data_type} ({cache_type})")
            continue

        # 去除 data_type 开头的数字和下划线，得到干净的分类名，并清理非法字符
        clean_data_type = clean_filename(re.sub(r'^\d+_', '', data_type))
        logging.info(f"  正在处理数据类型: {data_type} (cleaned: {clean_data_type}), 共 {len(items)} 项")

        # 创建输出子目录
        output_subdir = Path(output_dir) / clean_data_type

        for item in items:
            try:
                # 从缓存项目生成markdown内容
                markdown_content = generate_markdown_from_cache_item(item, data_type)
                if not markdown_content:
                    logging.warning(f"    项目 {item.id} 生成markdown失败")
                    continue

                # 确定文件名和路径
                item_name = getattr(item, 'name', None) or getattr(item, 'title', None) or str(item.id)
                cleaned_name = clean_filename(item_name)
                file_name_without_ext = f"{cleaned_name}-{item.id}"
                file_name = f"{file_name_without_ext}.md"

                # 获取二级分类
                sub_category_name = None
                if data_type in classification_map:
                    field_name = classification_map[data_type]
                    # 从标签字典中获取分类字段值
                    if hasattr(item, 'tags') and item.tags and field_name in item.tags:
                        sub_category_name = item.tags[field_name]

                # 如果没有获取到分类或分类为空，则设置为 "未分类"
                if not sub_category_name or str(sub_category_name).strip() == "":
                    sub_category_name = "未分类"

                # 确定输出路径
                if data_type in classification_map:
                    cleaned_sub_category = clean_filename(str(sub_category_name))
                    final_output_dir = output_subdir / cleaned_sub_category
                    output_path = final_output_dir / file_name
                    frontend_path = f"/v2/gi/category/{clean_data_type}/{cleaned_sub_category}/{file_name_without_ext}"
                    display_category = str(sub_category_name)
                else:
                    output_path = output_subdir / file_name
                    frontend_path = f"/v2/gi/category/{clean_data_type}/{file_name_without_ext}"
                    display_category = clean_data_type

                # 保存Markdown文件
                save_file(output_path, markdown_content)

                # 添加到元数据索引
                metadata_index.append({
                    "id": item.id,
                    "name": item_name,
                    "type": clean_data_type,
                    "category": display_category,
                    "path": frontend_path
                })

                logging.debug(f"    已生成: {output_path}")

            except Exception as e:
                logging.error(f"    处理缓存项目 {item.id} 时出错: {e}")
                continue

    logging.info(f"基于缓存的Markdown导出完成，共处理 {len(metadata_index)} 个文件")
    return metadata_index

def generate_markdown_from_cache_item(item: Any, data_type: str) -> str:
    """
    从缓存项目生成markdown内容

    Args:
        item: 缓存中的数据模型对象
        data_type: 数据类型

    Returns:
        Markdown格式的内容
    """
    try:
        # 初始化解析器（只需要用于格式化，不需要数据加载）
        parser = GiWikiDataParser()  # 不传入data_dir，因为我们不从文件加载数据

        # 使用解析器的格式化功能
        markdown_content = parser.format_to_markdown(item, data_type)
        return markdown_content

    except Exception as e:
        logging.error(f"生成markdown失败: {e}")
        return ""


def export_catalog_index(metadata_index: List[Dict[str, Any]], output_dir: str):
    """
    导出编目索引到JSON文件。
    """
    logging.info("开始导出编目索引...")

    output_path = Path(output_dir) / "index.json"
    save_file(output_path, json.dumps(metadata_index, ensure_ascii=False, indent=2))
    logging.info(f"编目索引已保存到: {output_path}")

def main():
    """主执行函数（修复版本，完全基于缓存）"""
    # --- 1. 检查缓存文件 ---
    if not os.path.exists(CACHE_FILE_PATH):
        logging.error(f"缓存文件 '{CACHE_FILE_PATH}' 不存在。请先运行 `scripts/giwiki_create_cache.py`。")
        sys.exit(1)

    # --- 2. 从缓存加载数据 ---
    logging.info(f"正在从缓存 '{CACHE_FILE_PATH}' 加载数据...")
    try:
        cache_data = load_cache_data(CACHE_FILE_PATH)
        logging.info("缓存数据加载成功")

        # 检查缓存数据完整性
        if 'parser_cache' not in cache_data:
            logging.error("缓存数据中缺少 parser_cache")
            sys.exit(1)

        # 统计缓存数据
        total_items = sum(len(items) for items in cache_data['parser_cache'].values())
        logging.info(f"缓存中总共有 {total_items} 个数据项")

    except Exception as e:
        logging.error(f"加载缓存数据失败: {e}")
        sys.exit(1)

    # --- 3. 基于缓存执行导出 ---
    try:
        metadata_index = export_all_to_markdown_from_cache(cache_data, MARKDOWN_OUTPUT_DIR, CLASSIFICATION_MAP)
        export_catalog_index(metadata_index, JSON_OUTPUT_DIR)

        logging.info("Markdown 文件和目录索引已生成。")
        logging.info(f"  - Markdown: {Path(MARKDOWN_OUTPUT_DIR).resolve()}")
        logging.info(f"  - JSON Index: {Path(JSON_OUTPUT_DIR) / 'index.json'}")
        logging.info("注意：搜索索引将由 generate_all_catalog_trees.py 生成")

    except Exception as e:
        logging.error(f"导出过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()