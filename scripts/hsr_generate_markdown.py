import os
import logging
import sys
import re
import json
import shutil
from typing import List, Dict, Any
from pathlib import Path
from collections import defaultdict

# --- 路径设置 ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# 直接使用 CacheService，这是HSR数据访问的核心
from hsr_data_parser.services.cache_service import CacheService

# --- 配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
CACHE_FILE_PATH = "hsr_data_parser/cache/hsr_data.cache.gz"
MARKDOWN_OUTPUT_DIR = "web/docs-site/public/domains/hsr/docs"
JSON_OUTPUT_DIR = "web/docs-site/public/domains/hsr/metadata"

# --- 辅助函数 (从GI脚本移植并验证) ---

def clean_filename(name: str) -> str:
    """清理字符串，使其适合作为文件名或URL的一部分。"""
    if not isinstance(name, str):
        name = str(name)
    # 移除所有非(汉字、字母、数字、下划线、中划线)的字符
    name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9_-]', '', name)
    name = name.replace(' ', '-')
    name = name.strip()
    return name.lower()

def save_file(file_path: Path, content: str):
    """将内容保存到指定路径的文件中，并确保目录存在。"""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        logging.debug(f"已保存文件: {file_path}")
    except Exception as e:
        logging.error(f"保存文件 {file_path} 时出错: {e}")
        raise

# --- HSR 导出逻辑 (基于GI模式重构) ---

def export_all_to_markdown(cache: CacheService, output_dir_str: str):
    """将所有HSR游戏数据从缓存导出为Markdown文件。"""
    logging.info(f"开始导出所有HSR数据到Markdown文件，输出目录: {output_dir_str}")
    output_dir = Path(output_dir_str)

    # 定义需要处理的数据类别及其格式化器
    # 注意：这里的 'formatter' 需要从 cache 中获取，因为它们是与数据一同缓存的
    # 这个设计有缺陷，我们暂时手动创建格式化器实例
    from hsr_data_parser.formatters import (
        BookFormatter, CharacterFormatter, LightconeFormatter, MaterialFormatter,
        MessageFormatter, MiracleFormatter, MissionFormatter, RelicFormatter,
        RogueEventFormatter
    )
    
    # 手动映射数据类别、其在缓存中的属性名、格式化器和前端路由中的分类名
    # 键 (key) 必须与前端路由路径中的分类名完全一致 (通常是复数)
    category_map = {
        'characters': {'attr': 'characters', 'formatter': CharacterFormatter(), 'sub_cat_func': lambda item: "角色"},
        'lightcones': {'attr': 'lightcones', 'formatter': LightconeFormatter(), 'sub_cat_func': lambda item: "光锥"},
        'relics': {'attr': 'relics', 'formatter': RelicFormatter(), 'sub_cat_func': lambda item: "遗器"},
        'materials': {'attr': 'materials', 'formatter': MaterialFormatter(), 'sub_cat_func': lambda item: item.main_type},
        'books': {'attr': 'books', 'formatter': BookFormatter(), 'sub_cat_func': lambda item: "书籍"},
        'miracles': {'attr': 'miracles', 'formatter': MiracleFormatter(), 'sub_cat_func': lambda item: "奇物"},
        'missions': {'attr': 'missions', 'formatter': MissionFormatter(), 'sub_cat_func': lambda item: "任务"},
        'rogue_events': {'attr': 'rogue_events', 'formatter': RogueEventFormatter(), 'sub_cat_func': lambda item: "模拟宇宙事件"},
    }

    for cat_name, config in category_map.items():
        logging.info(f"  正在处理类别: {cat_name}...")
        items = getattr(cache, config['attr'], [])
        formatter = config['formatter']
        sub_cat_func = config['sub_cat_func']

        if not items:
            logging.warning(f"  类别 {cat_name} 中没有找到任何项目。")
            continue

        for item in items:
            try:
                item_id = item.id
                if cat_name == 'rogue_events':
                    item_name = f"模拟宇宙事件-{item_id}"
                else:
                    item_name = item.name or f"{cat_name}-{item_id}"
                sub_category = sub_cat_func(item) or "未分类"

                markdown_content = formatter.format(item)
                if not markdown_content:
                    logging.warning(f"    无法为 {cat_name} ID '{item_id}' ({item_name}) 生成Markdown内容，已跳过。")
                    continue

                # 构建路径
                cleaned_sub_cat = clean_filename(sub_category)
                cleaned_item_name = clean_filename(item_name)

                # 对于没有实际子分类的类别（如角色、光锥、遗器），直接放在该类别的一级目录下
                if cat_name in ['characters', 'lightcones', 'relics', 'books', 'miracles', 'missions', 'rogue_events']:
                     file_path = output_dir / cat_name / f"{cleaned_item_name}-{item_id}.md"
                else:
                     file_path = output_dir / cat_name / cleaned_sub_cat / f"{cleaned_item_name}-{item_id}.md"

                save_file(file_path, markdown_content)
            except Exception as e:
                logging.error(f"    处理 {cat_name} 项目 {getattr(item, 'id', 'N/A')} 时出错: {e}", exc_info=True)
                if not markdown_content:
                    logging.warning(f"    无法为 {cat_name} ID '{item_id}' ({item_name}) 生成Markdown内容，已跳过。")
                    continue

                # 构建路径
                cleaned_sub_cat = clean_filename(sub_category)
                cleaned_item_name = clean_filename(item_name)

                # 对于没有实际子分类的类别（如角色、光锥、遗器），直接放在该类别的一级目录下
                if cat_name == 'rogue_events':
                    file_path = output_dir / cat_name / f"{cleaned_item_name}.md"
                elif cat_name in ['characters', 'lightcones', 'relics', 'books', 'miracles', 'missions']:
                     file_path = output_dir / cat_name / f"{cleaned_item_name}-{item_id}.md"
                else:
                     file_path = output_dir / cat_name / cleaned_sub_cat / f"{cleaned_item_name}-{item_id}.md"

                save_file(file_path, markdown_content)
            except Exception as e:
                logging.error(f"    处理 {cat_name} 项目 {getattr(item, 'id', 'N/A')} 时出错: {e}", exc_info=True)

    logging.info("所有HSR Markdown数据导出完成！")


def export_catalog_index(cache: CacheService, output_dir_str: str):
    """导出HSR编目索引 (catalog index) 到 JSON 文件。"""
    logging.info("开始导出HSR编目索引...")
    output_dir = Path(output_dir_str)
    catalog = []

    category_map = {
        'characters': {'attr': 'characters', 'sub_cat_func': lambda item: "角色"},
        'lightcones': {'attr': 'lightcones', 'sub_cat_func': lambda item: "光锥"},
        'relics': {'attr': 'relics', 'sub_cat_func': lambda item: "遗器"},
        'materials': {'attr': 'materials', 'sub_cat_func': lambda item: item.main_type},
        'books': {'attr': 'books', 'sub_cat_func': lambda item: "书籍"},
        'miracles': {'attr': 'miracles', 'sub_cat_func': lambda item: "奇物"},
        'missions': {'attr': 'missions', 'sub_cat_func': lambda item: "任务"},
        'rogue_events': {'attr': 'rogue_events', 'sub_cat_func': lambda item: "模拟宇宙事件"},
    }

    for cat_name, config in category_map.items():
        items = getattr(cache, config['attr'], [])
        sub_cat_func = config['sub_cat_func']

        for item in items:
            try:
                item_id = item.id
                if cat_name == 'rogue_events':
                    item_name = f"模拟宇宙事件-{item_id}"
                else:
                    item_name = item.name or f"{cat_name}-{item_id}"
                sub_category = sub_cat_func(item) or "未分类"

                # 构建与 antdv 兼容的 key 和前端路由 path
                cleaned_sub_cat = clean_filename(sub_category)
                cleaned_item_name = clean_filename(item_name)

                # 调整路径和key的生成逻辑，以匹配新的文件结构
                if cat_name == 'rogue_events':
                    path = f"/v2/hsr/category/{cat_name}/{cleaned_item_name}"
                    key = f"{cat_name}-{item_id}"
                    cat_display_name = sub_category
                elif cat_name in ['characters', 'lightcones', 'relics', 'books', 'miracles', 'missions']:
                    path = f"/v2/hsr/category/{cat_name}/{cleaned_item_name}-{item_id}"
                    key = f"{cat_name}-{item_id}"
                    cat_display_name = sub_category # "角色", "光锥", "遗器" 等
                else:
                    path = f"/v2/hsr/category/{cat_name}/{cleaned_sub_cat}/{cleaned_item_name}-{item_id}"
                    key = f"{cat_name}-{cleaned_sub_cat}-{item_id}"
                    cat_display_name = sub_category
                
                catalog.append({
                    "id": item_id,
                    "name": item_name,
                    "type": cat_name.capitalize(), # 类型，如 Character
                    "category": cat_display_name, # 子分类，如 物理
                    "path": path,
                    "key": key
                })
            except Exception as e:
                logging.error(f"    处理 {cat_name} 目录项目 {getattr(item, 'id', 'N/A')} 时出错: {e}", exc_info=True)
            cleaned_sub_cat = clean_filename(sub_category)
            cleaned_item_name = clean_filename(item_name)

            # 调整路径和key的生成逻辑，以匹配新的文件结构
            if cat_name in ['characters', 'lightcones', 'relics', 'books', 'miracles', 'missions', 'rogue_events']:
                path = f"/v2/hsr/category/{cat_name}/{cleaned_item_name}-{item_id}"
                key = f"{cat_name}-{item_id}"
                cat_display_name = sub_category # "角色", "光锥", "遗器" 等
            else:
                path = f"/v2/hsr/category/{cat_name}/{cleaned_sub_cat}/{cleaned_item_name}-{item_id}"
                key = f"{cat_name}-{cleaned_sub_cat}-{item_id}"
                cat_display_name = sub_category
            
            catalog.append({
                "id": item_id,
                "name": item_name,
                "type": cat_name.capitalize(), # 类型，如 Character
                "category": cat_display_name, # 子分类，如 物理
                "path": path,
                "key": key
            })
    
    output_path = output_dir / "index.json"
    save_file(output_path, json.dumps(catalog, ensure_ascii=False, indent=2))
    logging.info(f"HSR编目索引已保存到: {output_path}")

def export_search_index_chunked(cache: CacheService, base_output_dir_str: str):
    """导出HSR分片后的搜索索引。"""
    logging.info("开始导出HSR分片式搜索索引...")
    base_output_dir = Path(base_output_dir_str)

    if not cache._search_index:
        logging.error("错误：缓存中未找到或为空的搜索索引 (_search_index)。")
        return

    chunked_index = defaultdict(lambda: defaultdict(set))
    full_index = cache._search_index

    for keyword, results in full_index.items():
        if not keyword: continue
        first_char = keyword[0]
        for item in results:
            # result 已经是 {'id': ..., 'name': ..., 'type': ...} 格式
            chunked_index[first_char][keyword].add(item['id'])

    output_chunk_dir = base_output_dir / "search"
    if output_chunk_dir.exists():
        shutil.rmtree(output_chunk_dir)
    output_chunk_dir.mkdir(parents=True, exist_ok=True)

    logging.info(f"共找到 {len(chunked_index)} 个HSR分片，准备写入文件...")
    for char, chunk_data in chunked_index.items():
        final_chunk_data = {k: list(v) for k, v in chunk_data.items()}
        chunk_file_path = output_chunk_dir / f"{char}.json"
        save_file(chunk_file_path, json.dumps(final_chunk_data, ensure_ascii=False, separators=(',', ':')))

    logging.info(f"所有HSR分片索引已保存到: {output_chunk_dir.resolve()}")


def main():
    """主执行函数"""
    if not os.path.exists(CACHE_FILE_PATH):
        logging.error(f"缓存文件 '{CACHE_FILE_PATH}' 不存在。请先运行 `scripts/hsr_create_cache.py`。")
        sys.exit(1)
        
    logging.info(f"正在从缓存 '{CACHE_FILE_PATH}' 加载 CacheService...")
    cache_service = CacheService.load(CACHE_FILE_PATH)
    
    if not cache_service:
        logging.error("致命错误：从缓存文件加载 CacheService 失败。")
        sys.exit(1)
        
    logging.info("CacheService 初始化完成，已从缓存加载。")

    # 清理旧的输出目录
    md_output_path = Path(MARKDOWN_OUTPUT_DIR)
    if md_output_path.exists():
        shutil.rmtree(md_output_path)
    
    # 执行导出
    export_all_to_markdown(cache_service, MARKDOWN_OUTPUT_DIR)
    export_catalog_index(cache_service, JSON_OUTPUT_DIR)
    export_search_index_chunked(cache_service, JSON_OUTPUT_DIR)
    
    logging.info(f"所有HSR文件已生成。")
    logging.info(f"  - Markdown: {md_output_path.resolve()}")
    logging.info(f"  - JSON Indices: {Path(JSON_OUTPUT_DIR).resolve()}")

if __name__ == "__main__":
    main()