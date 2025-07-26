import os
import logging
import sys
import re
from typing import List, Dict, Any, Optional

# 在导入我们自己的模块之前设置好路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from game_data_parser.api import GameDataAPI

# --- 配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DATA_ROOT_DIR = "AnimeGameData"  # 原始游戏数据根目录
MARKDOWN_OUTPUT_DIR = "docs/generated_md" # 生成Markdown文件的输出目录

def clean_filename(name: str) -> str:
    """清理字符串，使其适合作为文件名。"""
    name = re.sub(r'[\\/:*?"<>|]', '', name) # 移除非法字符
    name = name.replace(' ', '_') # 将空格替换为下划线
    name = name.strip() # 移除首尾空格
    return name

def save_markdown_file(file_path: str, content: str):
    """
    将Markdown内容保存到指定路径的文件中，并确保目录存在。
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logging.debug(f"已保存文件: {file_path}")

def export_all_to_markdown(api: GameDataAPI, output_dir: str):
    """
    将所有游戏数据导出为Markdown文件。
    """
    logging.info(f"开始导出所有数据到Markdown文件，输出目录: {output_dir}")

    # --- 1. 处理通用服务 ---
    # 定义需要处理的通用服务及其Markdown生成函数和树状结构获取函数
    generic_services = [
        {"name": "Character", "tree_func": api.character.get_tree, "markdown_func": api.character.get_character_as_markdown},
        {"name": "Weapon", "tree_func": api.weapon.get_tree, "markdown_func": api.weapon.get_weapon_as_markdown},
        {"name": "RelicSet", "tree_func": api.relic.get_tree, "markdown_func": api.relic.get_relic_set_as_markdown},
        {"name": "Material", "tree_func": api.material.get_tree, "markdown_func": api.material.get_material_as_markdown},
        {"name": "Book", "tree_func": api.book.list_book_series, "markdown_func": api.book.get_book_series_as_markdown}, # Book特殊处理，list_book_series返回的是系列列表
    ]

    for service_info in generic_services:
        service_name = service_info['name']
        logging.info(f"  正在处理通用服务: {service_name}...")
        service_output_dir = os.path.join(output_dir, service_name)
        
        try:
            tree_data = service_info["tree_func"]()
            
            if service_name in ["Character", "Weapon", "Material"]:
                for category_node in tree_data:
                    category_name = clean_filename(category_node.get("title") or "未知分类")
                    category_path = os.path.join(service_output_dir, category_name)
                    if "children" in category_node and category_node["children"]:
                        for item_node in category_node["children"]:
                            item_id_str = item_node.get("id")
                            item_name = clean_filename(item_node.get("title") or item_node.get("name") or str(item_id_str))
                            if not item_id_str or not item_name: continue
                            
                            try:
                                # 关键修复：将从JSON树中获取的字符串ID转换为整数
                                item_id = int(item_id_str)
                                markdown_content = service_info["markdown_func"](item_id)
                            except (ValueError, TypeError):
                                logging.warning(f"    ID '{item_id_str}' 无法转换为整数，已跳过。")
                                continue

                            file_path = os.path.join(category_path, f"{item_name}.md")
                            save_markdown_file(file_path, markdown_content)
                            logging.info(f"    已生成 {service_name}/{category_name}/{item_name}.md")

            elif service_name in ["RelicSet", "Book"]:
                # RelicSet 和 Book (系列) 直接处理列表
                for item_node in tree_data:
                    item_id = item_node.id if hasattr(item_node, 'id') else item_node.get('id')
                    item_name = clean_filename(item_node.name if hasattr(item_node, 'name') else item_node.get('name') or item_node.get('title') or str(item_id))
                    if not item_id or not item_name: continue
                    
                    markdown_content = service_info["markdown_func"](item_id)
                    file_path = os.path.join(service_output_dir, f"{item_name}.md")
                    save_markdown_file(file_path, markdown_content)
                    logging.info(f"    已生成 {service_name}/{item_name}.md")

        except Exception as e:
            logging.error(f"  处理 {service_name} 时发生错误: {e}", exc_info=True)

    # --- 2. 特殊处理任务(Quest)服务 ---
    logging.info("  正在处理特殊服务: Quest...")
    quest_output_dir = os.path.join(output_dir, "Quest")
    try:
        quest_tree = api.quest.get_quest_tree()
        for category_node in quest_tree:
            category_id = category_node.get("id")
            category_title = clean_filename(category_node.get("title") or "未知分类")
            category_path = os.path.join(quest_output_dir, category_title)
            logging.info(f"    正在处理任务分类: {category_title}...")

            if category_id == "ORPHAN_MISC":
                # 零散任务，深入一层获取真正的任务列表
                if category_node.get("children"):
                    intermediate_node = category_node["children"][0]
                    quest_nodes = intermediate_node.get("children", [])
                else:
                    quest_nodes = []
                
                for node in quest_nodes:
                    item_id = node.get("id")
                    item_name = clean_filename(node.get("title") or node.get("name") or str(item_id))
                    if not item_id or not item_name: continue
                    markdown_content = api.quest.get_quest_as_markdown(item_id)
                    file_path = os.path.join(category_path, f"{item_name}.md")
                    save_markdown_file(file_path, markdown_content)
                    logging.info(f"      已生成 Quest/{category_title}/{item_name}.md")
            else:
                # 章节任务
                chapter_nodes = category_node.get("children", [])
                for node in chapter_nodes:
                    item_id = node.get("id")
                    item_name = clean_filename(node.get("title") or str(item_id))
                    if not item_id or not item_name: continue
                    markdown_content = api.quest.get_chapter_as_markdown(item_id)
                    file_path = os.path.join(category_path, f"{item_name}.md")
                    save_markdown_file(file_path, markdown_content)
                    logging.info(f"      已生成 Quest/{category_title}/{item_name}.md")

    except Exception as e:
        logging.error(f"  处理 Quest 时发生错误: {e}", exc_info=True)

    # --- 3. 特殊处理 Readable (世界文本) 服务 ---
    logging.info("  正在处理特殊服务: Readable (世界文本)...")
    readable_output_dir = os.path.join(output_dir, "World") # 世界是平铺的，直接放在World目录下
    try:
        world_texts = api.readable.list_world_texts()
        for item in world_texts:
            item_id = item.get('id')
            item_name = clean_filename(item.get('name') or str(item_id))
            if not item_id or not item_name: continue
            
            markdown_content = api.readable.get_readable_as_markdown(item_id)
            if markdown_content is None:
                logging.warning(f"    无法为 Readable ID '{item_id}' ({item_name}) 生成Markdown内容，已跳过。")
                continue
            file_path = os.path.join(readable_output_dir, f"{item_name}.md")
            save_markdown_file(file_path, markdown_content)
            logging.info(f"    已生成 World/{item_name}.md")
    except Exception as e:
        logging.error(f"  处理 Readable (世界文本) 时发生错误: {e}", exc_info=True)
    
    logging.info("所有数据导出完成！")


if __name__ == "__main__":
    if not os.path.isdir(DATA_ROOT_DIR):
        logging.error(f"数据根目录 '{DATA_ROOT_DIR}' 不存在。请确保该目录位于脚本运行的同级目录。")
        sys.exit(1)
        
    logging.info("正在初始化 API以便从原始文件加载 (无缓存)...")
    api = GameDataAPI(data_root_path=DATA_ROOT_DIR, cache_path=None)

    export_all_to_markdown(api, MARKDOWN_OUTPUT_DIR)
    
    logging.info(f"Markdown 文件已生成到: {os.path.abspath(MARKDOWN_OUTPUT_DIR)}")