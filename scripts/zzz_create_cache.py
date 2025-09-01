#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用于创建绝区零游戏数据缓存的脚本。
此脚本会加载所有游戏数据到内存中，并将其保存到一个缓存文件中，
以便后续脚本可以快速加载。
"""

import sys
import os

# 将项目根目录添加到 sys.path，以便可以导入 zzz_data_parser
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from zzz_data_parser.api import ZZZDataAPI
from zzz_data_parser.dataloader import ZZZDataLoader
from zzz_data_parser.formatters.dialogue_formatter import DialogueFormatter

# 配置
DATA_ROOT_DIR = "ZenlessData"
CACHE_FILE_PATH = "zzz_data_parser/cache/zzz_data.cache.gz"

def force_load_all(api: ZZZDataAPI) -> None:
    """
    强制加载所有数据到内存中。

    Args:
        api: ZZZDataAPI 实例
    """
    print("正在加载所有数据...")

    # 加载所有伙伴数据
    print("正在加载伙伴数据...")
    api.partner._load_data()  # 这将触发加载
    print(f"已加载 {len(api.partner._partners) if api.partner._partners else 0} 个伙伴")

    # 加载所有武器数据
    print("正在加载武器数据...")
    api.weapon._load_data()  # 这将触发加载
    print(f"已加载 {len(api.weapon._weapons) if api.weapon._weapons else 0} 个武器")

    # 加载所有道具数据
    print("正在加载道具数据...")
    api.item._load_data()  # 这将触发加载
    print(f"已加载 {len(api.item._items) if api.item._items else 0} 个道具")

    # 加载所有空洞道具数据
    print("正在加载空洞道具数据...")
    api.hollow_item._load_data()  # 这将触发加载
    print(f"已加载 {len(api.hollow_item._items) if api.hollow_item._items else 0} 个空洞道具")

    # 加载所有录像带集合数据
    print("正在加载录像带集合数据...")
    api.vhs_collection._load_data()  # 这将触发加载
    print(f"已加载 {len(api.vhs_collection._vhs_collections) if api.vhs_collection._vhs_collections else 0} 个录像带集合")

    # 加载所有对话章节数据
    print("正在加载对话章节数据...")
    chapter_ids = api.dialogue.list_all_chapter_ids()
    print(f"已加载 {len(chapter_ids)} 个对话章节")

    # 加载所有会话数据
    print("正在加载会话数据...")
    api.session._load_data()  # 这将触发加载
    print(f"已加载 {len(api.session._sessions) if api.session._sessions else 0} 个会话")

def build_search_index(api: ZZZDataAPI) -> None:
    """
    为所有数据构建搜索索引。

    Args:
        api: ZZZDataAPI 实例
    """
    print("正在构建搜索索引...")

    # 清空旧索引
    api.loader.clear_search_index()

    # 为伙伴数据构建索引
    print("正在为伙伴数据建立索引...")
    if api.partner._partners:
        for partner in api.partner._partners:
            # 获取伙伴的 Markdown 内容
            markdown_content = api.partner.get_partner_as_markdown(partner.id)

            # 清理 Markdown 内容以用于搜索
            cleaned_content = clean_markdown_for_search(markdown_content)

            # 构建上下文
            item_name = partner.name or f"Partner {partner.id}"
            context = {
                "id": partner.id,
                "name": item_name,
                "type": "partner"
            }

            # 索引数据
            api.loader._index_item({"content": cleaned_content}, context)

    # 为武器数据构建索引
    print("正在为武器数据建立索引...")
    if api.weapon._weapons:
        for weapon in api.weapon._weapons:
            # 获取武器的 Markdown 内容
            markdown_content = api.weapon.get_weapon_as_markdown(weapon.id)

            # 清理 Markdown 内容以用于搜索
            cleaned_content = clean_markdown_for_search(markdown_content)

            # 构建上下文
            item_name = weapon.name or f"Weapon {weapon.id}"
            context = {
                "id": weapon.id,
                "name": item_name,
                "type": "weapon"
            }

            # 索引数据
            api.loader._index_item({"content": cleaned_content}, context)

    # 为道具数据构建索引
    print("正在为道具数据建立索引...")
    if api.item._items:
        for item in api.item._items:
            # 获取道具的 Markdown 内容
            markdown_content = api.item.get_item_as_markdown(item.id)

            # 清理 Markdown 内容以用于搜索
            cleaned_content = clean_markdown_for_search(markdown_content)

            # 构建上下文
            item_name = item.name or f"Item {item.id}"
            context = {
                "id": item.id,
                "name": item_name,
                "type": "item"
            }

            # 索引数据
            api.loader._index_item({"content": cleaned_content}, context)

    # 为空洞道具数据构建索引
    print("正在为空洞道具数据建立索引...")
    if api.hollow_item._items:
        for item in api.hollow_item._items:
            # 获取空洞道具的 Markdown 内容
            markdown_content = api.hollow_item.get_hollow_item_as_markdown(item.id)

            # 清理 Markdown 内容以用于搜索
            cleaned_content = clean_markdown_for_search(markdown_content)

            # 构建上下文
            item_name = item.name or f"Hollow Item {item.id}"
            context = {
                "id": item.id,
                "name": item_name,
                "type": "hollow_item"
            }

            # 索引数据
            api.loader._index_item({"content": cleaned_content}, context)

    # 为录像带集合数据构建索引
    print("正在为录像带集合数据建立索引...")
    if api.vhs_collection._vhs_collections:
        for vhs in api.vhs_collection._vhs_collections:
            # 获取录像带集合的 Markdown 内容
            markdown_content = api.vhs_collection.get_vhs_collection_as_markdown(vhs.id)

            # 清理 Markdown 内容以用于搜索
            cleaned_content = clean_markdown_for_search(markdown_content)

            # 构建上下文
            item_name = vhs.name or f"VHS Collection {vhs.id}"
            context = {
                "id": vhs.id,
                "name": item_name,
                "type": "vhs_collection"
            }

            # 索引数据
            api.loader._index_item({"content": cleaned_content}, context)

    # 为对话章节数据构建索引（按 Act）
    print("正在为对话章节数据建立索引...")
    chapter_ids = api.dialogue.list_all_chapter_ids()
    for chapter_id in chapter_ids:
        chapter = api.dialogue.get_chapter_by_id(chapter_id)
        if not chapter:
            continue

        formatter = DialogueFormatter(chapter)
        markdown_files = formatter.to_markdown_files()

        # 对 acts 进行排序以确保索引顺序稳定
        sorted_acts = sorted(chapter.acts.items(), key=lambda item: int(item[0]))

        act_number = 1
        for act_id, act in sorted_acts:
            filename = f"{chapter.id}-{act_number}.md"

            # 从 formatter 的结果中获取对应 act 的 markdown 内容
            # 注意：formatter.to_markdown_files() 返回的键是带 .md 后缀的文件名
            markdown_content = markdown_files.get(filename)

            if not markdown_content:
                continue

            cleaned_content = clean_markdown_for_search(markdown_content)

            display_name = f"{chapter.id} - 第 {act_number} 幕"

            context = {
                "id": f"{chapter.id}-{act_id}",  # 创建一个唯一的复合ID
                "name": display_name,
                "type": "dialogue_act", # 使用新的类型以区分
                "category": f"{chapter.category or 'Uncategorized'}/{chapter.sub_category or 'Misc'}",
            }

            api.loader._index_item({"content": cleaned_content}, context)
            act_number += 1

    # 为会话数据构建索引
    print("正在为会话数据建立索引...")
    if api.session._sessions:
        for session in api.session._sessions:
            # 获取会话的 Markdown 内容
            markdown_content = api.session.get_session_as_markdown(session.session_id)

            # 清理 Markdown 内容以用于搜索
            cleaned_content = clean_markdown_for_search(markdown_content)

            # 构建上下文
            item_name = session.main_npc_name or f"Session {session.session_id}"
            context = {
                "id": session.session_id,
                "name": item_name,
                "type": "session"
            }

            # 索引数据
            api.loader._index_item({"content": cleaned_content}, context)

def clean_markdown_for_search(content: str) -> str:
    """
    清理 Markdown 内容以用于搜索索引。
    移除所有 Markdown 语法，只保留纯文本内容。

    Args:
        content: 原始 Markdown 内容

    Returns:
        清理后的纯文本内容
    """
    import re

    # 移除 Markdown 标题
    content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)

    # 移除 Markdown 粗体和斜体
    content = re.sub(r'\*{1,2}(.+?)\*{1,2}', r'\1', content)
    content = re.sub(r'_{1,2}(.+?)_{1,2}', r'\1', content)

    # 移除 Markdown 链接，保留链接文本
    content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)

    # 移除 Markdown 图片
    content = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', content)

    # 移除 Markdown 代码块标记
    content = re.sub(r'`{3}.*?`{3}', '', content, flags=re.DOTALL)

    # 移除 Markdown 行内代码
    content = re.sub(r'`([^`]+)`', r'\1', content)

    # 移除 Markdown 引用
    content = re.sub(r'^>\s*', '', content, flags=re.MULTILINE)

    # 移除 Markdown 分割线
    content = re.sub(r'^-{3,}$', '', content, flags=re.MULTILINE)

    # 移除 Markdown 表格分隔符
    content = re.sub(r'^\|.*\|$', '', content, flags=re.MULTILINE)

    # 移除多余的空白行
    content = re.sub(r'\n\s*\n', '\n', content)

    return content.strip()

def main():
    """主函数"""
    print("正在为绝区零数据创建缓存...")

    # 初始化 API
    api = ZZZDataAPI(data_root_path=DATA_ROOT_DIR)

    # 强制加载所有数据
    force_load_all(api)

    # 构建搜索索引
    build_search_index(api)

    # 保存缓存
    print(f"正在保存缓存到 {CACHE_FILE_PATH}...")
    api.loader.save_cache(CACHE_FILE_PATH)

    print("缓存创建完成!")

if __name__ == "__main__":
    main()