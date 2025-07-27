import os
import logging
import time
import re
import sys

# 在导入我们自己的模块之前设置好路径
# 将项目根目录（'scripts'的上级目录）添加到sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from game_data_parser.api import GameDataAPI
from game_data_parser.dataloader import DataLoader

def clean_markdown_for_search(markdown_text: str) -> str:
    """移除Markdown格式，保留纯文本内容。"""
    if not markdown_text: return ""
    text = re.sub(r'#+\s?', '', markdown_text)
    text = re.sub(r'(\*\*|__)(.*?)(\*\*|__)', r'\2', text) # Bold
    text = re.sub(r'(\*|_)(.*?)(\*|_)', r'\2', text) # Italic
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text) # Links
    text = re.sub(r'^\s*-\s+', '', text, flags=re.MULTILINE) # List items
    text = re.sub(r'^\s*>\s+', '', text, flags=re.MULTILINE) # Blockquotes
    text = re.sub(r'---', '', text) # Horizontal rules
    text = re.sub(r'`(.*?)`', r'\1', text) # Inline code
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL) # Code blocks
    return text

# --- 配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DATA_ROOT_DIR = "AnimeGameData"
CACHE_FILE_PATH = os.path.join("game_data_parser", "cache", "gi_data.cache.gz")

def force_load_all(api: GameDataAPI):
    """
    通过调用所有可用的API端点来强制加载所有数据到缓存中。
    """
    start_time = time.time()
    logging.info("开始暴力预热缓存，这将需要一些时间...")

    # 1. 预热 QuestService
    try:
        logging.info("  预热 QuestService...")
        quest_list = api.quest.list_quests()
        logging.info(f"    找到 {len(quest_list)} 个任务，正在获取详情...")
        for i, q_info in enumerate(quest_list):
            api.quest.get_quest_as_json(q_info['id'])
            if (i + 1) % 100 == 0:
                logging.info(f"      ...已处理 {i+1}/{len(quest_list)} 个任务")
    except Exception as e:
        logging.error(f"预热 QuestService 时发生错误: {e}")

    # 2. 预热 CharacterService
    try:
        logging.info("  预热 CharacterService...")
        character_list = api.character.list_characters()
        logging.info(f"    找到 {len(character_list)} 个角色，正在获取详情...")
        for char in character_list:
            api.character.get_character_as_json(char.id)
    except Exception as e:
        logging.error(f"预热 CharacterService 时发生错误: {e}")

    # 3. 预热 WeaponService
    try:
        logging.info("  预热 WeaponService...")
        weapon_list = api.weapon.list_weapons()
        logging.info(f"    找到 {len(weapon_list)} 个武器，正在获取详情...")
        for w_info in weapon_list:
            api.weapon.get_weapon_as_json(w_info['id'])
    except Exception as e:
        logging.error(f"预热 WeaponService 时发生错误: {e}")

    # 4. 预热 RelicService
    try:
        logging.info("  预热 RelicService (套装)...")
        set_list = api.relic.list_relic_sets()
        logging.info(f"    找到 {len(set_list)} 个圣遗物套装，正在获取详情...")
        for relic_set_info in set_list:
            api.relic.get_relic_set_as_json(relic_set_info['id'])
    except Exception as e:
        logging.error(f"预热 RelicService 时发生错误: {e}")

    # 5. 预热 MaterialService
    try:
        logging.info("  预热 MaterialService...")
        material_list = api.material.get_all()
        logging.info(f"    找到 {len(material_list)} 个物料，正在获取详情...")
        for mat in material_list:
            api.material.get_by_id(mat.id)
    except Exception as e:
        logging.error(f"预热 MaterialService 时发生错误: {e}")

    # 6. 预热 BookService
    try:
        logging.info("  预热 BookService...")
        book_series_list = api.book.list_book_series()
        logging.info(f"    找到 {len(book_series_list)} 个书籍系列，正在获取详情...")
        for series_info in book_series_list:
            full_series = api.book.get_book_series_by_id(series_info.id)
            if full_series and full_series.volumes:
                for vol in full_series.volumes:
                    vol.get_content()
    except Exception as e:
        logging.error(f"预热 BookService 时发生错误: {e}")

    # 7. 预热 ReadableService (已移除)
    # 此部分的预热逻辑会导致所有可读物被错误地“染色”为“已使用”，
    # 从而导致后续的索引阶段无法找到任何“世界文本”。
    # ReadableInterpreter 的 _prepare_data 方法已经处理了所有必要的加载。
        
    end_time = time.time()
    logging.info(f"缓存预热完成，总计用时: {end_time - start_time:.2f} 秒。")


if __name__ == "__main__":
    if not os.path.isdir(DATA_ROOT_DIR):
        logging.error(f"数据根目录 '{DATA_ROOT_DIR}' 不存在。请确保该目录位于脚本运行的同级目录。")
        sys.exit(1)
        
    DataLoader._instance = None
    
    logging.info("正在初始化 API以便从原始文件加载...")
    api = GameDataAPI(data_root_path=DATA_ROOT_DIR, cache_path=None)

    force_load_all(api)

    logging.info("--- 开始构建新的搜索索引 (基于Tree和Markdown) ---")
    start_time = time.time()
    
    api.loader._search_index.clear()

    # --- 1. 处理通用服务 ---
    generic_services = [
        {"name": "Character", "tree_func": api.character.get_tree, "markdown_func": api.character.get_character_as_markdown},
        {"name": "Weapon", "tree_func": api.weapon.get_tree, "markdown_func": api.weapon.get_weapon_as_markdown},
        {"name": "RelicSet", "tree_func": api.relic.get_tree, "markdown_func": api.relic.get_relic_set_as_markdown},
        {"name": "Material", "tree_func": api.material.get_tree, "markdown_func": api.material.get_material_as_markdown},
        # 关键修复：为 Book 单独指定获取 series markdown 的函数
        {"name": "Book", "tree_func": api.book.get_tree, "markdown_func": api.book.get_book_series_as_markdown},
    ]
    # 将 Readable 单独处理，因为它没有树状结构
    generic_services.append({"name": "Readable", "list_func": api.readable.list_readables, "markdown_func": api.readable.get_readable_as_markdown})

    for service in generic_services:
        service_name = service['name']
        logging.info(f"  正在处理通用服务: {service_name}...")
        try:
            nodes_to_index = []
            if "tree_func" in service:
                tree_data = service["tree_func"]()
                # 关键修复：对 Book 进行特殊处理，直接索引系列
                if service_name == "Book":
                    nodes_to_index = tree_data
                elif service_name in ["RelicSet"]:
                    nodes_to_index = tree_data
                elif service_name in ["Character", "Weapon", "Material"]:
                    for category_node in tree_data:
                        if "children" in category_node and category_node["children"]:
                            nodes_to_index.extend(category_node["children"])
            elif "list_func" in service:
                if service_name == "Readable":
                    # 对于 Readable，我们只索引“世界文本”
                    nodes_to_index = api.readable.list_world_texts()
                else:
                    nodes_to_index = service["list_func"]()

            logging.info(f"    找到 {len(nodes_to_index)} 个 {service_name} 节点进行索引。")
            for node in nodes_to_index:
                item_id = node.get("id")
                item_name = node.get("title") or node.get("name")

                if service_name != "Readable":
                    try:
                        item_id = int(item_id)
                    except (ValueError, TypeError, AttributeError):
                        logging.warning(f"  [!] 发现非数字ID，跳过此节点: {node}")
                        continue

                if not item_name:
                    continue

                try:
                    markdown_content = service["markdown_func"](item_id)
                except Exception as md_exc:
                    logging.error(f"    [!!] 无法为节点生成Markdown，已跳过。 服务: {service_name}, 节点: {node}, 错误: {md_exc}")
                    continue
                
                plain_text = clean_markdown_for_search(markdown_content)
                
                # 关键修复：如果服务是 Book，则将类型覆写为 Series
                index_type = "Series" if service_name == "Book" else service_name
                
                data_to_index = {'name': item_name, 'content': plain_text}
                context = {'id': item_id, 'name': item_name, 'type': index_type}
                api.loader._index_item(data_to_index, context)
        except Exception as e:
            logging.error(f"  索引 {service_name} 时发生错误: {e}", exc_info=True)

    # --- 2. 特殊处理任务(Quest)服务 ---
    logging.info("  正在处理特殊服务: Quest...")
    try:
        quest_tree = api.quest.get_quest_tree()
        for category_node in quest_tree:
            category_id = category_node.get("id")
            category_title = category_node.get("title")
            logging.info(f"    正在处理任务分类: {category_title}...")

            if category_id == "ORPHAN_MISC":
                # 深入一层获取真正的任务列表
                if category_node.get("children"):
                    intermediate_node = category_node["children"][0]
                    quest_nodes = intermediate_node.get("children", [])
                else:
                    quest_nodes = []
                
                logging.info(f"      找到 {len(quest_nodes)} 个零散任务。")
                for node in quest_nodes:
                    item_id = node.get("id")
                    item_name = node.get("title") or node.get("name")
                    if not item_id or not item_name: continue
                    markdown_content = api.quest.get_quest_as_markdown(item_id)
                    plain_text = clean_markdown_for_search(markdown_content)
                    data_to_index = {'name': item_name, 'content': plain_text}
                    context = {'id': item_id, 'name': item_name, 'type': "Quest"}
                    api.loader._index_item(data_to_index, context)
            else:
                chapter_nodes = category_node.get("children", [])
                logging.info(f"      找到 {len(chapter_nodes)} 个章节。")
                for node in chapter_nodes:
                    item_id = node.get("id")
                    item_name = node.get("title")
                    if not item_id or not item_name: continue
                    markdown_content = api.quest.get_chapter_as_markdown(item_id)
                    plain_text = clean_markdown_for_search(markdown_content)
                    data_to_index = {'name': item_name, 'content': plain_text}
                    context = {'id': item_id, 'name': item_name, 'type': "Chapter"}
                    api.loader._index_item(data_to_index, context)

    except Exception as e:
        logging.error(f"  索引 Quest 时发生错误: {e}", exc_info=True)

    end_time = time.time()
    logging.info(f"--- 新的搜索索引构建完成, 耗时: {end_time - start_time:.2f} 秒 ---")
    
    logging.info("--- 搜索索引简述 ---")
    final_search_index = api.loader._search_index
    unique_tokens = len(final_search_index)
    total_references = sum(len(refs) for refs in final_search_index.values())
    logging.info(f"  唯一的词条数量: {unique_tokens}")
    logging.info(f"  总的索引引用数量: {total_references}")
    logging.info("--------------------")

    # 保存缓存
    logging.info(f"正在将完整缓存保存到 '{CACHE_FILE_PATH}'...")
    # 确保在保存前，目录存在
    os.makedirs(os.path.dirname(CACHE_FILE_PATH), exist_ok=True)
    api.loader.save_cache(CACHE_FILE_PATH)
    logging.info("缓存保存成功！")