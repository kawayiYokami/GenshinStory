#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用于生成绝区零游戏数据 Markdown 文档和索引的脚本。
此脚本会从缓存文件中加载数据，并生成 Markdown 文档、目录索引和搜索索引。
"""

import sys
import os
import json
import re
import shutil
import msgpack

from pathlib import Path
# 将项目根目录添加到 sys.path，以便可以导入 zzz_data_parser
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from zzz_data_parser.api import ZZZDataAPI

# --- 差值编码函数 ---
def delta_encode(sorted_ids):
    """差值编码：将排序ID转换为相邻差值"""
    if not sorted_ids or len(sorted_ids) == 0:
        return []

    deltas = [sorted_ids[0]]  # 第一个ID保持原值
    for i in range(1, len(sorted_ids)):
        deltas.append(sorted_ids[i] - sorted_ids[i-1])
    return deltas

# 配置
CACHE_FILE_PATH = "zzz_data_parser/cache/zzz_data.cache.gz"
MARKDOWN_OUTPUT_DIR = "web/docs-site/public/domains/zzz/docs"
JSON_OUTPUT_DIR = "web/docs-site/public/domains/zzz/metadata"

def clean_filename(filename: str) -> str:
    """
    清理文件名，移除或替换操作系统不允许的字符。

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 移除或替换不允许的字符
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)

    # 移除首尾的空格和点
    filename = filename.strip('. ')

    # 如果文件名为空，则使用默认名称
    if not filename:
        filename = "unnamed"

    return filename
def save_file(file_path: Path, content: str):
    """
    将内容保存到指定路径的文件中，并确保目录存在。
    使用 pathlib 提高稳健性。
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
    except Exception as e:
        print(f"Error saving file {file_path}: {e}")
        raise

def export_all_to_markdown(api: ZZZDataAPI) -> None:
    """
    将所有数据导出为 Markdown 文档。

    Args:
        api: ZZZDataAPI 实例
    """
    print("Exporting all data to Markdown...")

    # 确保输出目录存在
    os.makedirs(MARKDOWN_OUTPUT_DIR, exist_ok=True)

    # 导出伙伴数据
    print("Exporting partners...")
    export_service_to_markdown(api, api.partner, "partner")

    # 导出武器数据
    print("Exporting weapons...")
    export_service_to_markdown(api, api.weapon, "weapon")

    # 导出道具数据
    print("Exporting items...")
    export_service_to_markdown(api, api.item, "item")

    # 导出空洞道具数据
    print("Exporting hollow items...")
    export_service_to_markdown(api, api.hollow_item, "hollowitem")

    # 导出录像带集合数据
    print("Exporting VHS collections...")
    export_service_to_markdown(api, api.vhs_collection, "vhscollection")

    # 导出对话章节数据
    print("Exporting dialogue chapters...")
    export_dialogue_to_markdown(api)

    # 导出会话数据
    print("Exporting sessions...")
    export_session_to_markdown(api)

def export_service_to_markdown(api, service, type_name: str) -> None:
    """
    将服务中的数据导出为 Markdown 文档。

    Args:
        api: ZZZDataAPI 实例
        service: 服务实例
        type_name: 数据类型名称（用于目录结构）
    """
    # 获取树状结构
    tree = service.get_tree()

    # 遍历树状结构
    for category_node in tree:
        # 清理并创建分类目录
        category_name_clean = clean_filename(category_node["name"])
        category_dir = os.path.join(MARKDOWN_OUTPUT_DIR, type_name, category_name_clean)
        os.makedirs(category_dir, exist_ok=True)

        # 遍历分类中的项目
        for item_node in category_node.get("children", []):
            # 获取项目的 Markdown 内容
            # 对于空洞道具，先检查是否有实际内容（名字或描述）
            if type_name == "hollowitem":
                try:
                    # service is HollowItemService and exposes get_item_by_id
                    item_obj = service.get_item_by_id(item_node["id"])
                except Exception:
                    item_obj = None

                # 如果项的名字和描述都为空，或名字为占位词（如含 '待定' 或 'unnamed'），则跳过并删除已存在的占位文件（清理旧输出）
                is_placeholder = False
                if item_obj:
                    name = (item_obj.name or "").strip()
                    desc = (item_obj.description or "").strip()
                    if (not name and not desc):
                        is_placeholder = True
                    else:
                        lname = name.lower()
                        if '待定' in name or '待定' == name or lname.startswith('unnamed') or lname == 'unnamed' or lname == 'tbd':
                            is_placeholder = True

                if is_placeholder:
                    # 计算可能存在的文件路径并删除
                    filename_to_remove = f"{clean_filename(item_node.get('name',''))}-{item_node['id']}.md"
                    file_path_to_remove = os.path.join(category_dir, filename_to_remove)
                    if os.path.exists(file_path_to_remove):
                        try:
                            os.remove(file_path_to_remove)
                        except Exception:
                            pass
                    continue

            if type_name == "partner":
                markdown_content = service.get_partner_as_markdown(item_node["id"])
            elif type_name == "weapon":
                markdown_content = service.get_weapon_as_markdown(item_node["id"])
            elif type_name == "item":
                markdown_content = service.get_item_as_markdown(item_node["id"])
            elif type_name == "hollowitem":
                markdown_content = service.get_hollow_item_as_markdown(item_node["id"])
            elif type_name == "vhscollection":
                markdown_content = service.get_vhs_collection_as_markdown(item_node["id"])
            else:
                continue

            # 清理文件名
            filename = clean_filename(item_node["name"])

            # 保存 Markdown 文件
            file_path = os.path.join(category_dir, f"{filename}-{item_node['id']}.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

def export_dialogue_to_markdown(api: ZZZDataAPI) -> None:
    """
    将对话数据导出为 Markdown 文档，每个 Act 一个文件。
    """
    # 导入 DialogueFormatter
    from zzz_data_parser.formatters.dialogue_formatter import DialogueFormatter

    all_chapter_ids = api.dialogue.list_all_chapter_ids()

    for chapter_id in all_chapter_ids:
        chapter = api.dialogue.get_chapter_by_id(chapter_id)
        if not chapter:
            print(f"  - WARNING: Could not find chapter {chapter_id}, skipping.")
            continue

        # 使用 category 和 sub_category 构建基本目录
        category_name = clean_filename(chapter.category or "Uncategorized")
        sub_category_name = clean_filename(chapter.sub_category or "Misc")

        # 为每个章节创建一个独立的子文件夹
        chapter_folder_name = clean_filename(chapter.id)

        category_dir = os.path.join(MARKDOWN_OUTPUT_DIR, "dialogue", category_name, sub_category_name, chapter_folder_name)
        os.makedirs(category_dir, exist_ok=True)

        # 使用新的 Formatter 生成多个文件
        formatter = DialogueFormatter(chapter)
        markdown_files = formatter.to_markdown_files()

        for filename, content in markdown_files.items():
            file_path = os.path.join(category_dir, clean_filename(filename))
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        if markdown_files:
            print(f"  - Generated {len(markdown_files)} files for chapter '{chapter_id}' in '{category_dir}'")
def export_session_to_markdown(api: ZZZDataAPI) -> None:
    """
    将会话数据导出为 Markdown 文档。

    Args:
        api: ZZZDataAPI 实例
    """
    # 获取树状结构
    tree = api.session.get_tree()

    # 遍历树状结构
    for npc_node in tree:
        npc_name = npc_node["name"]

        # 创建并清理 NPC 目录（在循环内）
        npc_name_clean = clean_filename(npc_name)
        npc_dir = os.path.join(MARKDOWN_OUTPUT_DIR, "session", npc_name_clean)
        os.makedirs(npc_dir, exist_ok=True)

        # 遍历 NPC 的会话
        for session_node in npc_node.get("children", []):
            # 获取会话的 Markdown 内容
            markdown_content = api.session.get_session_as_markdown(session_node["id"])

            # 清理文件名
            filename = clean_filename(f"session-{session_node['id']}")

            # 保存 Markdown 文件
            file_path = os.path.join(npc_dir, f"{filename}.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

def export_catalog_index(api: ZZZDataAPI) -> None:
    """
    导出目录索引。

    Args:
        api: ZZZDataAPI 实例
    """
    print("Exporting catalog index...")

    # 确保输出目录存在
    os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)

    # 收集所有数据的元信息
    catalog = []

    # 收集伙伴数据
    collect_service_metadata(api, api.partner, "partner", catalog)

    # 收集武器数据
    collect_service_metadata(api, api.weapon, "weapon", catalog)

    # 收集道具数据
    collect_service_metadata(api, api.item, "item", catalog)

    # 收集空洞道具数据
    collect_service_metadata(api, api.hollow_item, "hollowitem", catalog)

    # 收集录像带集合数据
    collect_service_metadata(api, api.vhs_collection, "vhscollection", catalog)

    # 收集对话章节数据
    collect_dialogue_metadata(api, catalog)

    # 收集会话数据
    collect_session_metadata(api, catalog)

    # 保存目录索引
    index_file_path = os.path.join(JSON_OUTPUT_DIR, "index.json")
    with open(index_file_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

def collect_service_metadata(api, service, type_name: str, catalog: list) -> None:
    """
    收集服务中数据的元信息。

    Args:
        api: ZZZDataAPI 实例
        service: 服务实例
        type_name: 数据类型名称
        catalog: 用于存储元信息的列表
    """
    # 获取树状结构
    tree = service.get_tree()

    # 遍历树状结构
    for category_node in tree:
        category_name = category_node["name"]
        category_name_clean = clean_filename(category_name)

        # 遍历分类中的项目
        for item_node in category_node.get("children", []):
            # 对于 hollowitem，跳过名称和描述为空的项目
            if type_name == "hollowitem":
                try:
                    item_obj = service.get_item_by_id(item_node["id"])
                except Exception:
                    item_obj = None

                # 跳过名称/描述为空或名称为占位词的项目
                if item_obj:
                    name = (item_obj.name or "").strip()
                    desc = (item_obj.description or "").strip()
                    lname = name.lower()
                    if (not name and not desc) or ('待定' in name) or lname.startswith('unnamed') or lname == 'unnamed' or lname == 'tbd':
                        continue

            # 构建路径
            item_name_clean = clean_filename(item_node['name'])
            path = f"/v2/zzz/category/{type_name}/{category_name_clean}/{item_name_clean}-{item_node['id']}"

            # 添加到目录
            catalog.append({
                "id": item_node["id"],
                "name": item_node["name"],
                "type": type_name,
                "category": category_name, # 使用真实的子分类名
                "path": path
            })

def collect_dialogue_metadata(api: ZZZDataAPI, catalog: list) -> None:
    """
    收集对话数据的元信息，为每个 Act 文件创建条目。
    """
    all_chapter_ids = api.dialogue.list_all_chapter_ids()

    for chapter_id in all_chapter_ids:
        chapter = api.dialogue.get_chapter_by_id(chapter_id)
        if not chapter:
            continue

        category_name = chapter.category or "Uncategorized"
        sub_category_name = chapter.sub_category or "Misc"
        category_name_clean = clean_filename(category_name)
        sub_category_name_clean = clean_filename(sub_category_name)
        chapter_folder_name = clean_filename(chapter.id)

        # 对 acts 进行排序以确保元数据顺序稳定
        sorted_acts = sorted(chapter.acts.items(), key=lambda item: int(item[0]))

        act_number = 1
        for act_id, act in sorted_acts:
            filename = f"{chapter.id}-{act_number}"
            clean_file_name = clean_filename(filename)
            path = f"/v2/zzz/category/dialogue/{category_name_clean}/{sub_category_name_clean}/{chapter_folder_name}/{clean_file_name}"

            # 使用 "章节ID - 第 X 幕" 作为显示名称
            display_name = f"{chapter.id} - 第 {act_number} 幕"

            catalog.append({
                "id": f"{chapter.id}-{act_id}", # 创建一个唯一的复合ID
                "name": display_name,
                "type": "dialogue",
                "category": f"{category_name} - {sub_category_name}",
                "path": path
            })
            act_number += 1

def collect_session_metadata(api: ZZZDataAPI, catalog: list) -> None:
    """
    收集会话数据的元信息。

    Args:
        api: ZZZDataAPI 实例
        catalog: 用于存储元信息的列表
    """
    # 获取树状结构
    tree = api.session.get_tree()

    # 遍历树状结构
    for npc_node in tree:
        npc_name = npc_node["name"]
        npc_name_clean = clean_filename(npc_name)

        # 遍历 NPC 的会话
        for session_node in npc_node.get("children", []):
            # 构建路径
            session_id = session_node["id"]
            path = f"/v2/zzz/category/session/{npc_name_clean}/{clean_filename(f'session-{session_id}')}"

            # 添加到目录
            catalog.append({
                "id": session_node["id"],
                "name": f"{npc_name} - {session_id}",
                "type": "session",
                "category": npc_name, # 使用 NPC 名称作为子分类
                "path": path
            })

def export_search_index_chunked(api: ZZZDataAPI) -> None:
    """
    导出优化的ZZZ-Wiki搜索索引（差值编码+MessagePack格式）。
    """
    print("Exporting ZZZ-Wiki optimized search index (delta+msgpack)...")

    if not api.loader or not hasattr(api.loader, '_search_index') or not api.loader._search_index:
        print("Error: Search index not found or is empty in API loader. Please ensure cache is generated correctly.")
        return

    chunked_index = {}
    full_index = api.loader._search_index

    # 处理搜索索引，按第一个字符分组并差值编码
    for keyword, results in full_index.items():
        if not keyword:
            continue
        first_char = keyword[0]
        if first_char not in chunked_index:
            chunked_index[first_char] = {}

        # 提取ID、排序并差值编码
        sorted_ids = []
        for item in results:
            item_id = None
            if hasattr(item, 'id'):
                item_id = item.id
            elif isinstance(item, dict) and 'id' in item:
                item_id = item['id']

            if item_id:
                # 提取数字部分用于差值编码（处理 'BangBooAB-10161802' 格式）
                numeric_id = re.sub(r'[^\d]', '', str(item_id))
                if numeric_id:
                    sorted_ids.append(int(numeric_id))

        sorted_ids = sorted(set(sorted_ids))
        chunked_index[first_char][keyword] = delta_encode(sorted_ids)

    # 生成MessagePack文件
    output_dir = Path(JSON_OUTPUT_DIR) / "search"
    if output_dir.exists():
        shutil.rmtree(output_dir)
        print(f"Cleaned old index directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 完整索引文件
    index_data = msgpack.packb(chunked_index, use_bin_type=True)
    with open(output_dir / "index.msg", "wb") as f:
        f.write(index_data)

    # 元数据文件
    metadata = {
        "version": "2.0",
        "format": "delta+msgpack",
        "keywords": len(chunked_index),
        "total_ids": sum(len(chunk) for chunk in chunked_index.values()),
        "chunks": len(chunked_index)
    }

    metadata_data = msgpack.packb(metadata, use_bin_type=True)
    with open(output_dir / "metadata.msg", "wb") as f:
        f.write(metadata_data)

    size_mb = len(index_data) / (1024 * 1024)
    print(f"优化索引已生成: {size_mb:.1f}MB")
    print(f"索引文件: {output_dir / 'index.msg'}")
    print(f"元数据文件: {output_dir / 'metadata.msg'}")
    print(f"分片数量: {len(chunked_index)}")
    print(f"词条总数: {sum(len(chunk) for chunk in chunked_index.values())}")

def main():
    """主函数"""
    print("Cleaning old output files...")

    # 更精确地清理旧的输出目录，避免删除 uiconfig.json 等静态文件

    # 清理 Markdown 输出目录
    if os.path.exists(MARKDOWN_OUTPUT_DIR):
        for item in os.listdir(MARKDOWN_OUTPUT_DIR):
            item_path = os.path.join(MARKDOWN_OUTPUT_DIR, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
    else:
        os.makedirs(MARKDOWN_OUTPUT_DIR, exist_ok=True)

    # 清理 JSON 输出目录中的生成文件
    if os.path.exists(JSON_OUTPUT_DIR):
        index_file = os.path.join(JSON_OUTPUT_DIR, "index.json")
        if os.path.exists(index_file):
            os.remove(index_file)

        search_dir = os.path.join(JSON_OUTPUT_DIR, "search")
        if os.path.exists(search_dir):
            shutil.rmtree(search_dir)
    else:
        os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)

    print("Generating Markdown documents and indexes for ZZZ data...")

    # 初始化 API 并从缓存加载数据
    api = ZZZDataAPI()
    if not api.loader.load_cache(CACHE_FILE_PATH):
        print(f"Failed to load cache from {CACHE_FILE_PATH}")
        return

    # 导出所有数据为 Markdown
    export_all_to_markdown(api)

    # 导出目录索引
    export_catalog_index(api)

    # 导出分片的搜索索引
    export_search_index_chunked(api)

    print("Markdown generation completed successfully!")

if __name__ == "__main__":
    main()