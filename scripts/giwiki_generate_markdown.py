import os
import logging
import sys
import re
import json
import gzip
from typing import List, Dict, Any, Optional
from pathlib import Path

# 在导入我们自己的模块之前设置好路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from giwiki_data_parser.main import GiWikiDataParser

# --- 配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
WIKI_DATA_DIR = "gi_wiki_scraper/output/structured_data"
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
    "68_书籍": "书籍类型",
}

def clean_filename(name: str) -> str:
    """清理字符串，使其适合作为文件名或URL的一部分。"""
    if not isinstance(name, str):
        name = str(name)
    # 移除所有非(汉字、字母、数字、下划线、中划线)的字符
    name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9_-]', '', name)
    name = name.replace(' ', '-')  # 将空格替换为中划线
    name = name.strip()  # 移除首尾空格
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
            'food': cache_service.foods,
            'domains': cache_service.domains,
            'outfits': cache_service.outfits,
        },
        'search_index': cache_service._search_index
    }
    
    return cache_data

def export_all_to_markdown(parser: GiWikiDataParser, output_dir: str) -> List[Dict[str, Any]]:
    """
    将所有解析的数据导出为Markdown文件，并返回元数据索引。
    """
    logging.info(f"开始导出所有数据到Markdown文件，输出目录: {output_dir}")

    metadata_index = []
    supported_types = parser.get_supported_data_types()

    for data_type in supported_types:
        # 去除 data_type 开头的数字和下划线，得到干净的分类名
        clean_data_type = re.sub(r'^\d+_', '', data_type)
        logging.info(f"  正在处理数据类型: {data_type} (cleaned: {clean_data_type})")

        try:
            # 获取该类型的所有文件
            type_dir = Path(WIKI_DATA_DIR) / data_type
            if not type_dir.exists():
                logging.warning(f"    数据目录不存在: {type_dir}")
                continue

            json_files = list(type_dir.glob("*.json"))
            logging.info(f"    找到 {len(json_files)} 个文件")

            # 创建输出子目录，使用干净的分类名
            output_subdir = Path(output_dir) / clean_data_type

            for json_file in json_files:
                try:
                    # 解析文件
                    parsed_data = parser.parse_file(str(json_file))
                    if not parsed_data:
                        continue

                    # 生成Markdown内容
                    markdown_content = parser.format_to_markdown(parsed_data, data_type)
                    if not markdown_content:
                        continue

                    # 确定文件名和路径
                    file_id = json_file.stem
                    item_name = getattr(parsed_data, 'name', None) or getattr(parsed_data, 'title', None) or file_id
                    cleaned_name = clean_filename(item_name)

                    file_name_without_ext = f"{cleaned_name}-{file_id}"
                    file_name = f"{file_name_without_ext}.md"

                    # 获取二级分类
                    sub_category_name = None
                    if data_type in CLASSIFICATION_MAP:
                        field_name = CLASSIFICATION_MAP[data_type]
                        # 从标签字典中获取分类字段值
                        if hasattr(parsed_data, 'tags') and parsed_data.tags and field_name in parsed_data.tags:
                            sub_category_name = parsed_data.tags[field_name]

                    # 如果没有获取到分类或分类为空，则设置为 "未分类"
                    if not sub_category_name or str(sub_category_name).strip() == "":
                        sub_category_name = "未分类"

                    # 确定输出路径
                    if data_type in CLASSIFICATION_MAP:
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
                        "id": file_id,
                        "name": item_name,
                        "type": clean_data_type,
                        "category": display_category,
                        "path": frontend_path
                    })

                except Exception as e:
                    logging.error(f"    处理文件 {json_file} 时出错: {e}")
                    continue

        except Exception as e:
            logging.error(f"  处理数据类型 {data_type} 时出错: {e}")
            continue

    logging.info(f"Markdown导出完成，共处理 {len(metadata_index)} 个文件")
    return metadata_index

def export_catalog_index(metadata_index: List[Dict[str, Any]], output_dir: str):
    """
    导出编目索引到JSON文件。
    """
    logging.info("开始导出编目索引...")

    output_path = Path(output_dir) / "index.json"
    save_file(output_path, json.dumps(metadata_index, ensure_ascii=False, indent=2))
    logging.info(f"编目索引已保存到: {output_path}")

def export_search_index_chunked(search_index: Dict[str, List[Dict[str, Any]]], base_output_dir: str):
    """
    导出分片后的搜索索引。
    每个分片以词条的第一个字符命名，如 '旅.json'。
    """
    logging.info("开始导出分片式搜索索引...")

    if not search_index:
        logging.error("错误：搜索索引为空。")
        return

    chunked_index = {}

    # 1. 按第一个字符对所有词条进行分组
    for keyword, results in search_index.items():
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
            chunked_index[first_char][keyword].add(item['id'])

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

        if (i + 1) % 100 == 0:
            logging.info(f"  ...已写入 {i + 1}/{total_chunks} 个分片文件")

    logging.info(f"所有分片索引已保存到: {output_chunk_dir.resolve()}")

def main():
    """主执行函数"""
    # --- 1. 检查缓存文件 ---
    if not os.path.exists(CACHE_FILE_PATH):
        logging.error(f"缓存文件 '{CACHE_FILE_PATH}' 不存在。请先运行 `scripts/giwiki_create_cache.py`。")
        sys.exit(1)

    # --- 2. 从缓存加载数据 ---
    logging.info(f"正在从缓存 '{CACHE_FILE_PATH}' 加载数据...")
    try:
        cache_data = load_cache_data(CACHE_FILE_PATH)
        logging.info("缓存数据加载成功")
    except Exception as e:
        logging.error(f"加载缓存数据失败: {e}")
        sys.exit(1)

    # --- 3. 初始化解析器 ---
    logging.info("正在初始化解析器...")
    parser = GiWikiDataParser(WIKI_DATA_DIR)

    # 如果缓存中有解析器数据，可以在这里恢复
    if 'parser_cache' in cache_data:
        parser.load_cache_data(cache_data)
        logging.info("解析器缓存数据已恢复")

    # --- 4. 清理旧文件 ---
    output_path = Path(MARKDOWN_OUTPUT_DIR)
    if output_path.exists():
        import shutil
        shutil.rmtree(output_path)
        logging.info(f"已清理旧的Markdown目录: {output_path}")

    # --- 5. 执行导出 ---
    metadata_index = export_all_to_markdown(parser, MARKDOWN_OUTPUT_DIR)
    export_catalog_index(metadata_index, JSON_OUTPUT_DIR)

    # 导出搜索索引
    if 'search_index' in cache_data:
        export_search_index_chunked(cache_data['search_index'], JSON_OUTPUT_DIR)
    else:
        logging.warning("缓存中未找到搜索索引数据")

    logging.info(f"所有文件已生成。")
    logging.info(f"  - Markdown: {output_path.resolve()}")
    logging.info(f"  - JSON Indices: {Path(JSON_OUTPUT_DIR).resolve()}")

if __name__ == "__main__":
    main()