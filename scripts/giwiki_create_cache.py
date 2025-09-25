import os
import logging
import time
import sys

# Setup project root path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from giwiki_data_parser.main import GiWikiDataParser

# --- 配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
WIKI_DATA_DIR = "gi_wiki_scraper/output/structured_data"
CACHE_FILE_PATH = os.path.join("giwiki_data_parser", "cache", "giwiki_data.cache.gz")

def main():
    """主函数，创建并保存缓存"""
    start_time = time.time()
    logging.info("开始创建GI Wiki数据缓存...")

    if not os.path.isdir(WIKI_DATA_DIR):
        logging.error(f"Wiki数据根目录 '{WIKI_DATA_DIR}' 不存在。请确保已运行wiki爬虫。")
        sys.exit(1)

    # 确保缓存目录存在
    cache_dir = os.path.dirname(CACHE_FILE_PATH)
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # 初始化解析器
    logging.info("正在初始化 GiWiki 数据解析器...")
    parser = GiWikiDataParser(WIKI_DATA_DIR)

    # 构建缓存和索引
    logging.info("--- 开始构建缓存和搜索索引 ---")
    cache_start_time = time.time()
    
    try:
        parser.build_cache_with_index()
    except Exception as e:
        logging.error(f"❌ 缓存创建失败: {e}")
        logging.error("程序遇到错误，立即停止以便修复")
        sys.exit(1)
    
    cache_end_time = time.time()
    logging.info(f"--- 缓存和索引构建完成, 耗时: {cache_end_time - cache_start_time:.2f} 秒 ---")

    # 获取统计信息
    stats = parser.cache_service.get_statistics()
    logging.info("--- 缓存统计信息 ---")
    for key, value in stats.items():
        if isinstance(value, int):
            logging.info(f"  {key}: {value}")
    logging.info("--------------------")

    # 保存缓存
    logging.info(f"正在保存缓存到 '{CACHE_FILE_PATH}'...")
    parser.save_cache(CACHE_FILE_PATH)

    end_time = time.time()
    logging.info(f"缓存创建过程完成，总耗时: {end_time - start_time:.2f} 秒")
    logging.info(f"缓存文件已保存至: {os.path.abspath(CACHE_FILE_PATH)}")

    # 测试搜索功能
    logging.info("--- 测试搜索功能 ---")
    test_queries = ["原神", "任务", "角色", "武器"]
    for query in test_queries:
        results = parser.search(query, limit=5)
        logging.info(f"搜索 '{query}': 找到 {len(results)} 个结果")
        for result in results[:3]:  # 只显示前3个结果
            logging.info(f"  - {result['name']} ({result['type']}) [ID: {result['id']}]")

if __name__ == "__main__":
    main()