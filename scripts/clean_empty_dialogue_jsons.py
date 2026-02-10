#!/usr/bin/env python3
"""
清理空白内容的NPC&商店JSON文件
删除对话组为空的JSON文件
"""

import os
import json
import sys

def clean_empty_dialogue_jsons(directory):
    """
    遍历目录下的所有JSON文件，如果对话组为空，则删除该文件
    """
    deleted_count = 0

    for filename in os.listdir(directory):
        if not filename.endswith('.json'):
            continue

        filepath = os.path.join(directory, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 检查对话组是否为空
            if '对话组' in data and isinstance(data['对话组'], list) and len(data['对话组']) == 0:
                os.remove(filepath)
                print(f"已删除空白JSON文件: {filename}")
                deleted_count += 1

        except json.JSONDecodeError:
            print(f"跳过无效JSON文件: {filename}")
        except Exception as e:
            print(f"处理文件时出错 {filename}: {e}")

    print(f"清理完成，共删除 {deleted_count} 个空白JSON文件")

if __name__ == "__main__":
    # 指定目录
    target_dir = r"gi_wiki_scraper\output\structured_data\20_NPC&商店"

    # 检查目录是否存在
    if not os.path.exists(target_dir):
        print(f"目录不存在: {target_dir}")
        sys.exit(1)

    print(f"开始清理目录: {target_dir}")
    clean_empty_dialogue_jsons(target_dir)