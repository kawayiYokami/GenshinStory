import os
import logging
import time
import sys

# 设置路径
# 将项目根目录（'scripts'的上级目录）添加到sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from hsr_data_parser.services.loader_service import DataLoader
from hsr_data_parser.services.text_map_service import TextMapService
from hsr_data_parser.services.cache_service import CacheService

# 导入所有解析器
from hsr_data_parser.interpreters import (
    BookInterpreter, CharacterInterpreter, LightConeInterpreter, MaterialInterpreter,
    MessageInterpreter, MiracleInterpreter, MissionInterpreter, RelicInterpreter,
    RogueEventInterpreter
)

# 导入所有格式化器
from hsr_data_parser.formatters.book_formatter import BookFormatter
from hsr_data_parser.formatters.character_formatter import CharacterFormatter
from hsr_data_parser.formatters.lightcone_formatter import LightconeFormatter
from hsr_data_parser.formatters.material_formatter import MaterialFormatter
from hsr_data_parser.formatters.message_formatter import MessageFormatter
from hsr_data_parser.formatters.miracle_formatter import MiracleFormatter
from hsr_data_parser.formatters.mission_formatter import MissionFormatter
from hsr_data_parser.formatters.relic_formatter import RelicFormatter
from hsr_data_parser.formatters.rogue_event_formatter import RogueEventFormatter

# --- 配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
CACHE_DIR = "hsr_data_parser/cache"
CACHE_FILE = os.path.join(CACHE_DIR, "hsr_data.cache.gz")

def main():
    """主函数，用于创建和保存 HSR 数据的缓存和索引。"""
    start_time = time.time()
    logging.info("开始创建崩坏：星铁数据缓存...")

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    # --- 1. 初始化服务 ---
    logging.info("初始化服务...")
    loader = DataLoader()
    text_map_service = TextMapService(loader)
    # Re-assign the text_map_service to the loader instance after it's created
    loader.text_map_service = text_map_service
    cache_service = CacheService()

    # 将解析器和格式化器映射起来
    processing_map = {
        'books': {'interpreter': BookInterpreter(loader, text_map_service), 'formatter': BookFormatter(), 'type_name': 'Book'},
        'characters': {'interpreter': CharacterInterpreter(loader, text_map_service), 'formatter': CharacterFormatter(), 'type_name': 'Character'},
        'lightcones': {'interpreter': LightConeInterpreter(loader, text_map_service), 'formatter': LightconeFormatter(), 'type_name': 'LightCone'},
        'relics': {'interpreter': RelicInterpreter(loader, text_map_service), 'formatter': RelicFormatter(), 'type_name': 'Relic'},
        'materials': {'interpreter': MaterialInterpreter(loader, text_map_service), 'formatter': MaterialFormatter(), 'type_name': 'Material'},
        'miracles': {'interpreter': MiracleInterpreter(loader, text_map_service), 'formatter': MiracleFormatter(), 'type_name': 'Miracle'},
        'messages': {'interpreter': MessageInterpreter(loader, text_map_service), 'formatter': MessageFormatter(), 'type_name': 'MessageThread'},
        'missions': {'interpreter': MissionInterpreter(loader, text_map_service), 'formatter': MissionFormatter(), 'type_name': 'Mission'},
        'rogue_events': {'interpreter': RogueEventInterpreter(loader, text_map_service), 'formatter': RogueEventFormatter(), 'type_name': 'RogueEvent'},
    }

    # --- 2. 解析、格式化和索引所有数据 ---
    for store_key, config in processing_map.items():
        interpreter = config['interpreter']
        formatter = config['formatter']
        type_name = config['type_name']
        
        logging.info(f"--- 正在处理: {type_name} ---")
        
        try:
            # 统一调用 interpret_all 方法
            # 对于需要额外参数的 MessageInterpreter, 我们需要特殊处理
            if type_name == 'MessageThread':
                # 确保在解析短信前，角色数据已加载并存入缓存服务
                if not cache_service.characters:
                    logging.error("无法解析短信，因为角色数据尚未加载。请确保角色在短信之前处理。")
                    continue
                char_map = {c.id: c for c in cache_service.characters}
                items = interpreter.interpret_all(characters_by_id=char_map)
            elif hasattr(interpreter, 'interpret_all'):
                 items = interpreter.interpret_all()
            else:
                 # 对于 RogueEvent 这种需要ID的，我们在此脚本中不进行单独解析
                 logging.warning(f"解析器 {type_name} 没有 'interpret_all' 方法，跳过批量处理。")
                 continue

            if not items:
                logging.warning(f"未能从 {type_name} 解析器获取任何数据。")
                continue
            
            # 存储到 cache_service
            setattr(cache_service, store_key, items)
            logging.info(f"  找到 {len(items)} 个 {type_name} 条目。")

            # 创建索引
            for item in items:
                markdown_content = formatter.format(item)
                item_id = getattr(item, 'id', None)
                item_name = getattr(item, 'name', None)
                
                # 对于短信，它的标题从内容生成
                if type_name == 'MessageThread' and not item_name:
                    item_name = f"短信对话: {getattr(item.messages[0], 'sender', '未知')}" if item.messages else "未知对话"

                if item_id is not None and item_name:
                    cache_service.index_item(item_id, item_name, type_name, markdown_content)

        except Exception as e:
            logging.error(f"处理 {type_name} 时发生错误: {e}", exc_info=True)

    # --- 3. 保存缓存 ---
    logging.info(f"正在将完整缓存保存到 '{CACHE_FILE}'...")
    cache_service.save(CACHE_FILE)
    
    end_time = time.time()
    logging.info(f"缓存创建完成！总计用时: {end_time - start_time:.2f} 秒。")
    logging.info(f"缓存文件已保存至: {CACHE_FILE}")

if __name__ == "__main__":
    main()