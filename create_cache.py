import os
import logging
import time

# 在导入我们自己的模块之前设置好路径
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from game_data_parser.api import GameDataAPI

# --- 配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DATA_ROOT_DIR = "AnimeGameDataX"  # 使用正确的目录名
CACHE_FILE_PATH = "game_data.cache"

def force_load_all(api: GameDataAPI):
    """
    通过调用所有可用的API端点来强制加载所有数据到缓存中。
    """
    start_time = time.time()
    logging.info("开始暴力预热缓存，这将需要一些时间...")

    # 1. 预热 QuestService
    try:
        logging.info("  预热 QuestService...")
        quest_ids = [q['id'] for q in api.quest.list_quests()]
        logging.info(f"    找到 {len(quest_ids)} 个任务，正在获取详情...")
        for i, qid in enumerate(quest_ids):
            api.quest.get_quest_as_json(qid) # get_as_json 会触发深层解析
            if (i + 1) % 100 == 0:
                logging.info(f"      ...已处理 {i+1}/{len(quest_ids)} 个任务")
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
        weapon_ids = [w['id'] for w in api.weapon.list_weapons()]
        logging.info(f"    找到 {len(weapon_ids)} 个武器，正在获取详情...")
        for wid in weapon_ids:
            api.weapon.get_weapon_as_json(wid)
    except Exception as e:
        logging.error(f"预热 WeaponService 时发生错误: {e}")

    # 4. 预热 RelicService
    try:
        logging.info("  预热 RelicService (套装)...")
        set_list = api.relic.list_relic_sets()
        logging.info(f"    找到 {len(set_list)} 个圣遗物套装，正在获取详情...")
        for relic_set in set_list:
            api.relic.get_relic_set_as_json(relic_set['id'])
    except Exception as e:
        logging.error(f"预热 RelicService 时发生错误: {e}")

    # 5. 预热 MaterialService
    try:
        logging.info("  预热 MaterialService...")
        material_ids = [m.id for m in api.material.get_all()]
        logging.info(f"    找到 {len(material_ids)} 个物料，这个过程会隐式完成，因为 get_all() 已经加载了所有物料。")
        # get_all() 已经加载了所有内容，无需再遍历
    except Exception as e:
        logging.error(f"预热 MaterialService 时发生错误: {e}")

    # 6. 预热 BookService
    try:
        logging.info("  预热 BookService...")
        book_series_ids = [s.id for s in api.book.list_book_series()]
        logging.info(f"    找到 {len(book_series_ids)} 个书籍系列，正在获取详情...")
        for sid in book_series_ids:
            full_series = api.book.get_book_series_by_id(sid)
            # 触发所有分卷内容的加载
            if full_series and full_series.volumes:
                for vol in full_series.volumes:
                    vol.get_content()
    except Exception as e:
        logging.error(f"预热 BookService 时发生错误: {e}")

    # 7. 强制触发 Readable 目录的缓存
    try:
        logging.info("  强制预热 Readable 目录缓存...")
        # 触发各个 interpreter 的 _prepare_data 方法，确保 Readable 目录被访问
        # 这样 get_all_file_paths_in_folder 和 get_text_file 的调用会被缓存
        
        # 触发武器故事加载
        weapon_list = api.weapon.list_weapons()
        if weapon_list:
            sample_weapon = weapon_list[0]
            api.weapon.get_weapon_as_json(sample_weapon['id'])
        
        # 触发圣遗物故事加载
        relic_sets = api.relic.list_relic_sets()
        if relic_sets:
            sample_relic_set = relic_sets[0]
            api.relic.get_relic_set_as_json(sample_relic_set['id'])
        
        # 触发材料故事加载
        materials = api.material.get_all()
        if materials:
            # 只需要调用 get_all 就会触发 _prepare_data
            pass
        
        # 触发书籍内容加载
        book_contents = api.book_content.get_all()
        if book_contents:
            # 只需要调用 get_all 就会触发 _prepare_data
            pass
            
        logging.info("    Readable 目录缓存预热完成。")
    except Exception as e:
        logging.error(f"预热 Readable 目录缓存时发生错误: {e}")

    end_time = time.time()
    logging.info(f"缓存预热完成，总计用时: {end_time - start_time:.2f} 秒。")


if __name__ == "__main__":
    if not os.path.isdir(DATA_ROOT_DIR):
        logging.error(f"数据根目录 '{DATA_ROOT_DIR}' 不存在。请确保该目录位于脚本运行的同级目录。")
        sys.exit(1)
        
    # 强制从原始文件加载，不使用任何现有缓存
    logging.info("正在初始化 API以便从原始文件加载...")
    api = GameDataAPI(data_root_path=DATA_ROOT_DIR, cache_path=None)

    # 暴力加载所有数据
    force_load_all(api)

    # 保存缓存
    logging.info(f"正在将完整缓存保存到 '{CACHE_FILE_PATH}'...")
    api.loader.save_cache(CACHE_FILE_PATH)
    logging.info("缓存保存成功！")