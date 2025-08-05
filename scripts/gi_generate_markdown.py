import os
import logging
import sys
import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

# 在导入我们自己的模块之前设置好路径
# 将项目根目录（'scripts'的上级目录）添加到sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from game_data_parser.api import GameDataAPI

# --- 配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DATA_ROOT_DIR = "AnimeGameData"  # 原始游戏数据根目录
CACHE_FILE_PATH = "game_data_parser/cache/gi_data.cache.gz" # 和 gi_create_cache.py 中必须完全一致
MARKDOWN_OUTPUT_DIR = "web/docs-site/public/domains/gi/docs" # 前端静态资源目录
JSON_OUTPUT_DIR = "web/docs-site/public/domains/gi/metadata" # JSON索引输出目录


def clean_filename(name: str) -> str:
    """清理字符串，使其适合作为文件名或URL的一部分。"""
    if not isinstance(name, str):
        name = str(name)
    # 最终修正：移除所有非(汉字、字母、数字、下划线、中划线)的字符，一劳永逸地解决特殊符号问题
    name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9_-]', '', name)
    name = name.replace(' ', '-') # 将空格替换为中划线
    name = name.strip() # 移除首尾空格
    return name.lower() # 统一转换为小写

def save_file(file_path: Path, content: str):
    """
    将内容保存到指定路径的文件中，并确保目录存在。
    使用 pathlib 提高稳健性。
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        logging.debug(f"已保存文件: {file_path}")
    except Exception as e:
        logging.error(f"保存文件 {file_path} 时出错: {e}")
        # 抛出异常以便上层可以捕获并停止执行
        raise

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
        service_name_lower = service_name.lower()
        logging.info(f"  正在处理通用服务: {service_name}...")
        # 修正：确保 service_output_dir 路径是小写的
        service_output_dir = os.path.join(output_dir, service_name_lower)
        
        try:
            tree_data = service_info["tree_func"]()
            
            if service_name in ["Character", "Weapon", "Material"]:
                for category_node in tree_data:
                    category_name = category_node.get("title") or "未知分类"
                    # 修正：确保 category_path 路径是小写的
                    category_path = os.path.join(service_output_dir, clean_filename(category_name))
                    
                    if "children" in category_node and category_node["children"]:
                        for item_node in category_node["children"]:
                            item_id_str = item_node.get("id")
                            item_name = item_node.get("title") or item_node.get("name") or str(item_id_str)
                            if not item_id_str or not item_name: continue
                            
                            try:
                                item_id = int(item_id_str)
                                markdown_content = service_info["markdown_func"](item_id)
                                if markdown_content is None:
                                    logging.warning(f"    无法为 {service_name} ID '{item_id}' ({item_name}) 生成Markdown内容，已跳过。")
                                    continue
                            except (ValueError, TypeError):
                                logging.warning(f"    ID '{item_id_str}' 无法转换为整数，已跳过。")
                                continue

                            file_name_cleaned = clean_filename(item_name)
                            file_path = Path(category_path) / f"{file_name_cleaned}-{item_id}.md"
                            save_file(file_path, markdown_content)

            elif service_name in ["RelicSet", "Book"]:
                # RelicSet 和 Book (系列) 直接处理列表
                for item_node in tree_data:
                    item_id = item_node.id if hasattr(item_node, 'id') else item_node.get('id')
                    item_name = item_node.name if hasattr(item_node, 'name') else item_node.get('name') or item_node.get('title') or str(item_id)
                    if not item_id or not item_name: continue
                    
                    markdown_content = service_info["markdown_func"](item_id)
                    if markdown_content is None:
                        logging.warning(f"    无法为 {service_name} ID '{item_id}' ({item_name}) 生成Markdown内容，已跳过。")
                        continue
                    
                    file_name_cleaned = clean_filename(item_name)
                    # 修正： Book 和 RelicSet 没有子目录，直接放在 service_output_dir
                    file_path = Path(service_output_dir) / f"{file_name_cleaned}-{item_id}.md"
                    save_file(file_path, markdown_content)

        except Exception as e:
            logging.error(f"  处理 {service_name} 时发生错误: {e}", exc_info=True)

    # --- 2. 特殊处理任务(Quest)服务 ---
    logging.info("  正在处理特殊服务: Quest...")
    quest_output_dir = os.path.join(output_dir, "quest")
    try:
        quest_tree = api.quest.get_quest_tree()
        for category_node in quest_tree:
            category_id = category_node.get("id")
            category_title = category_node.get("title") or "未知分类"
            # 修正：确保 category_path 路径是小写的
            category_path = os.path.join(quest_output_dir, clean_filename(category_title))
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
                    item_name = node.get("title") or node.get("name") or str(item_id)
                    if not item_id or not item_name: continue
                    markdown_content = api.quest.get_quest_as_markdown(item_id)
                    if markdown_content is None:
                        logging.warning(f"    无法为 Quest ID '{item_id}' ({item_name}) 生成Markdown内容，已跳过。")
                        continue
                    
                    file_name_cleaned = clean_filename(item_name)
                    file_path = Path(category_path) / f"{file_name_cleaned}-{item_id}.md"
                    save_file(file_path, markdown_content)
            else:
                # 章节任务
                chapter_nodes = category_node.get("children", [])
                for node in chapter_nodes:
                    item_id = node.get("id")
                    item_name = node.get("title") or str(item_id)
                    if not item_id or not item_name: continue
                    markdown_content = api.quest.get_chapter_as_markdown(item_id)
                    if markdown_content is None:
                        logging.warning(f"    无法为 Chapter ID '{item_id}' ({item_name}) 生成Markdown内容，已跳过。")
                        continue
                    
                    file_name_cleaned = clean_filename(item_name)
                    file_path = Path(category_path) / f"{file_name_cleaned}-{item_id}.md"
                    save_file(file_path, markdown_content)

    except Exception as e:
        logging.error(f"  处理 Quest 时发生错误: {e}", exc_info=True)

    # --- 3. 特殊处理 Readable (世界文本) 服务 ---
    logging.info("  正在处理特殊服务: Readable (世界文本)...")
    readable_output_dir = os.path.join(output_dir, "world") # 世界是平铺的，直接放在world目录下
    try:
        world_texts = api.readable.list_world_texts()
        for item in world_texts:
            item_id = item.get('id')
            item_name = item.get('name') or str(item_id)
            if not item_id or not item_name: continue
            
            markdown_content = api.readable.get_readable_as_markdown(item_id)
            if markdown_content is None:
                logging.warning(f"    无法为 Readable ID '{item_id}' ({item_name}) 生成Markdown内容，已跳过。")
                continue
            
            file_name_cleaned = clean_filename(item_name)
            file_path = Path(readable_output_dir) / f"{file_name_cleaned}-{item_id}.md"
            save_file(file_path, markdown_content)
    except Exception as e:
        logging.error(f"  处理 Readable (世界文本) 时发生错误: {e}", exc_info=True)
    
    logging.info("所有数据导出完成！")

def export_catalog_index(api: GameDataAPI, output_dir: str):
    """
    导出编目索引 (catalog index) 到 JSON 文件。
    这个索引包含了所有条目的元数据，用于前端的列表展示。
    """
    logging.info("开始导出编目索引...")
    catalog = []
    
    # 逻辑与 export_all_to_markdown 类似，但不写真实文件，只收集元数据
    # --- 1. 处理通用服务 ---
    generic_services = [
        {"name": "Character", "tree_func": api.character.get_tree},
        {"name": "Weapon", "tree_func": api.weapon.get_tree},
        {"name": "RelicSet", "tree_func": api.relic.get_tree},
        {"name": "Material", "tree_func": api.material.get_tree},
        {"name": "Book", "tree_func": api.book.list_book_series},
    ]

    for service_info in generic_services:
        service_name = service_info['name']
        tree_data = service_info["tree_func"]()
        
        if service_name in ["Character", "Weapon", "Material"]:
            for category_node in tree_data:
                category_name = category_node.get("title") or "未知分类"
                if "children" in category_node and category_node["children"]:
                    for item_node in category_node["children"]:
                        item_id = item_node.get("id")
                        item_title = item_node.get("title") or item_node.get("name")
                        if not item_id or not item_title: continue
                        
                        # 修正：生成完整的、可直接用于路由的绝对路径
                        path = f"/v2/gi/category/{service_name.lower()}/{clean_filename(category_name)}/{clean_filename(item_title)}-{item_id}"
                        catalog.append({"id": item_id, "name": item_title, "type": service_name, "category": category_name, "path": path})

        elif service_name in ["RelicSet", "Book"]:
            for item_node in tree_data:
                item_id = item_node.id if hasattr(item_node, 'id') else item_node.get('id')
                item_title = item_node.name if hasattr(item_node, 'name') else item_node.get('name') or item_node.get('title')
                if not item_id or not item_title: continue

                path = f"/v2/gi/category/{service_name.lower()}/{clean_filename(item_title)}-{item_id}"
                catalog.append({"id": item_id, "name": item_title, "type": service_name, "category": service_name, "path": path})

    # --- 2. 特殊处理任务(Quest)服务 ---
    quest_tree = api.quest.get_quest_tree()
    for category_node in quest_tree:
        category_id = category_node.get("id")
        category_title = category_node.get("title") or "未知分类"
        
        if category_id == "ORPHAN_MISC":
            if category_node.get("children"):
                intermediate_node = category_node["children"][0]
                quest_nodes = intermediate_node.get("children", [])
            else:
                quest_nodes = []
            
            for node in quest_nodes:
                item_id = node.get("id")
                item_title = node.get("title") or node.get("name")
                if not item_id or not item_title: continue
                path = f"/v2/gi/category/quest/{clean_filename(category_title)}/{clean_filename(item_title)}-{item_id}"
                catalog.append({"id": item_id, "name": item_title, "type": "Quest", "category": category_title, "path": path})
        else:
            chapter_nodes = category_node.get("children", [])
            for node in chapter_nodes:
                item_id = node.get("id")
                item_title = node.get("title")
                if not item_id or not item_title: continue
                path = f"/v2/gi/category/quest/{clean_filename(category_title)}/{clean_filename(item_title)}-{item_id}"
                # 注意：这里我们用 chapter id 作为 item_id
                catalog.append({"id": item_id, "name": item_title, "type": "QuestChapter", "category": category_title, "path": path})

    # --- 3. 特殊处理 Readable (世界文本) 服务 ---
    world_texts = api.readable.list_world_texts()
    for item in world_texts:
        item_id = item.get('id')
        item_name = item.get('name')
        if not item_id or not item_name: continue
        path = f"/v2/gi/category/world/{clean_filename(item_name)}-{item_id}"
        catalog.append({"id": item_id, "name": item_name, "type": "Readable", "category": "World", "path": path})

    output_path = Path(output_dir) / "index.json"
    save_file(output_path, json.dumps(catalog, ensure_ascii=False, indent=2))
    logging.info(f"编目索引已保存到: {output_path}")

def export_search_index_chunked(api: GameDataAPI, base_output_dir: str):
    """
    导出分片后的搜索索引。
    每个分片以词条的第一个字符命名，如 '旅.json'。
    """
    logging.info("开始导出分片式搜索索引...")
    if not api.loader or not hasattr(api.loader, '_search_index') or not api.loader._search_index:
        logging.error("错误：API loader中未找到或为空的搜索索引 (_search_index)。请确保缓存已正确生成。")
        return

    chunked_index = {}
    full_index = api.loader._search_index

    # 1. 按第一个字符对所有词条进行分组
    for keyword, results in full_index.items():
        if not keyword:
            continue
        first_char = keyword[0]
        if first_char not in chunked_index:
            chunked_index[first_char] = {}
        
        # 将结果（仅ID）添加到对应的分片中
        # 使用 set 来自动去重
        if keyword not in chunked_index[first_char]:
            chunked_index[first_char][keyword] = set()
        
        for item in results:
            chunked_index[first_char][keyword].add(item.id)

    # 2. 将每个分片写入单独的JSON文件
    output_chunk_dir = Path(base_output_dir) / "search"
    if output_chunk_dir.exists():
        import shutil
        shutil.rmtree(output_chunk_dir)
        logging.info(f"已清理旧的分片索引目录: {output_chunk_dir}")
    output_chunk_dir.mkdir(parents=True, exist_ok=True)

    total_chunks = len(chunked_index)
    logging.info(f"共找到 {total_chunks} 个分片，准备写入文件...")

    for i, (char, chunk_data) in enumerate(chunked_index.items()):
        # 将 set 转换为 list 以便 JSON 序列化
        final_chunk_data = {k: list(v) for k, v in chunk_data.items()}

        # 文件名不能包含非法字符，但我们的key是单个字符，通常是安全的
        chunk_file_path = output_chunk_dir / f"{char}.json"
        
        # 为了生产环境的性能，分片文件不使用indent
        save_file(chunk_file_path, json.dumps(final_chunk_data, ensure_ascii=False, separators=(',', ':')))
        
        if (i + 1) % 1000 == 0:
            logging.info(f"  ...已写入 {i + 1}/{total_chunks} 个分片文件")

    logging.info(f"所有分片索引已保存到: {output_chunk_dir.resolve()}")

def main():
    """主执行函数"""
    # --- 1. 初始化API (从缓存加载) ---
    if not os.path.exists(CACHE_FILE_PATH):
        logging.error(f"缓存文件 '{CACHE_FILE_PATH}' 不存在。请先运行 `scripts/gi_create_cache.py`。")
        sys.exit(1)
        
    logging.info(f"正在从缓存 '{CACHE_FILE_PATH}' 初始化 API...")
    # 最终的、正确的初始化方式：
    # data_root_path 仍然提供，以防某些服务需要它
    # cache_path 提供准确的、相对于项目根目录的路径
    api = GameDataAPI(data_root_path=DATA_ROOT_DIR, cache_path=CACHE_FILE_PATH)
    
    # 验证是否真的从缓存加载
    if not api.loader._cache:
        logging.error("致命错误：API 初始化后，内部文件缓存为空。缓存加载失败。")
        logging.error("请检查 DataLoader 实现和缓存文件本身是否有效。")
        sys.exit(1)
        
    logging.info("API 初始化完成，已从缓存加载。")

    # --- 2. 清理旧文件 ---
    output_path = Path(MARKDOWN_OUTPUT_DIR)
    if output_path.exists():
        import shutil
        shutil.rmtree(output_path)
        logging.info(f"已清理旧的Markdown目录: {output_path}")
    
    # --- 3. 执行导出 ---
    export_all_to_markdown(api, MARKDOWN_OUTPUT_DIR)
    export_catalog_index(api, JSON_OUTPUT_DIR)
    # 调用新的分片导出函数
    export_search_index_chunked(api, JSON_OUTPUT_DIR)
    
    logging.info(f"所有文件已生成。")
    logging.info(f"  - Markdown: {output_path.resolve()}")
    logging.info(f"  - JSON Indices: {Path(JSON_OUTPUT_DIR).resolve()}")

if __name__ == "__main__":
    main()