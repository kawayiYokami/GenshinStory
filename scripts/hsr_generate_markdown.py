import os
import logging
import sys
import re

# 在导入我们自己的模块之前设置好路径
# 将项目根目录（'scripts'的上级目录）添加到sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from hsr_data_parser.services.cache_service import CacheService

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
CACHE_PATH = "hsr_data_parser/cache/hsr_data.cache.gz"
OUTPUT_DIR = "docs/hsr_md"

def clean_filename(name: str) -> str:
    """清理字符串，使其适合作为文件名。"""
    if not name:
        return ""
    name = re.sub(r'[\\/:*?"<>|]', '', name) # 移除非法字符
    name = name.replace(' ', '_') # 将空格替换为下划线
    name = name.strip() # 移除首尾空格
    return name

def save_markdown_file(file_path: str, content: str):
    """将Markdown内容保存到指定路径的文件中，并确保目录存在。"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logging.debug(f"已保存文件: {file_path}")

def main():
    """主函数，用于从缓存加载数据并生成Markdown文档。"""
    if not os.path.exists(CACHE_PATH):
        logging.error(f"缓存文件未找到: {CACHE_PATH}")
        logging.error("请先运行 'scripts/hsr_create_cache.py' 来生成缓存。")
        sys.exit(1)

    logging.info(f"正在从 '{CACHE_PATH}' 加载缓存...")
    cache_service = CacheService.load(CACHE_PATH)
    logging.info("缓存加载成功。")

    # 将数据类型映射到其在cache_service中的属性名和格式化器
    export_map = {
        'books': {'data': cache_service.books, 'formatter': BookFormatter()},
        'characters': {'data': cache_service.characters, 'formatter': CharacterFormatter()},
        'lightcones': {'data': cache_service.lightcones, 'formatter': LightconeFormatter()},
        'relics': {'data': cache_service.relics, 'formatter': RelicFormatter()},
        'materials': {'data': cache_service.materials, 'formatter': MaterialFormatter()},
        'miracles': {'data': cache_service.miracles, 'formatter': MiracleFormatter()},
        'messages': {'data': cache_service.messages, 'formatter': MessageFormatter()},
        'missions': {'data': cache_service.missions, 'formatter': MissionFormatter()},
    }

    logging.info(f"开始导出所有数据到Markdown文件，输出目录: {OUTPUT_DIR}")

    for category, config in export_map.items():
        data_list = config['data']
        formatter = config['formatter']
        category_dir = os.path.join(OUTPUT_DIR, category)
        
        if not data_list:
            logging.warning(f"类别 '{category}' 中没有数据，跳过。")
            continue

        logging.info(f"  正在处理类别: {category} ({len(data_list)} 个条目)...")
        
        for item in data_list:
            try:
                markdown_content = formatter.format(item)
                
                # 为文件名获取一个合适的名称
                item_name = getattr(item, 'name', None)
                if not item_name and hasattr(item, 'title'):
                    item_name = getattr(item, 'title')
                if not item_name and category == 'messages':
                     item_name = f"对话_{getattr(item, 'id', 'unknown')}"

                # 如果在所有尝试之后仍然没有名字，使用ID作为备用
                if not item_name:
                    item_id = getattr(item, 'id', None)
                    if item_id:
                        logging.warning(f"    '{category}' 中 ID 为 {item_id} 的条目缺少名称，将使用ID作为文件名。")
                        item_name = f"{category}_{item_id}"
                    else:
                        logging.error(f"    无法确定 '{category}' 中某个条目的文件名和ID，已跳过。")
                        continue

                # 为“偶遇”任务特别处理文件名以确保唯一性
                if category == 'missions' and item_name == "偶遇":
                    filename = f"偶遇-{getattr(item, 'id', 'unknown')}.md"
                else:
                    filename = f"{clean_filename(item_name)}.md"
                
                file_path = os.path.join(category_dir, filename)
                
                save_markdown_file(file_path, markdown_content)
            except Exception as e:
                logging.error(f"    处理条目时发生错误 (ID: {getattr(item, 'id', 'N/A')}, Name: {getattr(item, 'name', 'N/A')}): {e}", exc_info=True)

    logging.info("Markdown导出完成！")

if __name__ == "__main__":
    main()