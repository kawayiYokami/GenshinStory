#!/usr/bin/env python3
"""修复chunk_id不一致问题"""
import json
from pathlib import Path

def fix_chunk_ids(filepath):
    """修复文件中的chunk_id不一致问题"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'items' not in data:
        return False

    for item in data['items']:
        item_chunk_id = item.get('chunk_id', '')
        item_file_path = item.get('file_path', '')

        # 修复relations中的evidence
        if 'relations' in item:
            for relation in item['relations']:
                if 'evidence' in relation:
                    relation['evidence']['chunk_id'] = item_chunk_id
                    relation['evidence']['file_path'] = item_file_path

        # 修复events中的evidence
        if 'events' in item:
            for event in item['events']:
                if 'evidence' in event:
                    event['evidence']['chunk_id'] = item_chunk_id
                    event['evidence']['file_path'] = item_file_path

        # 修复entities中的evidence (如果有的话)
        if 'entities' in item:
            for entity in item['entities']:
                if 'evidence' in entity:
                    entity['evidence']['chunk_id'] = item_chunk_id
                    entity['evidence']['file_path'] = item_file_path

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True

if __name__ == "__main__":
    filepath = Path('graph_batches/batch2_kokomi.json')
    if fix_chunk_ids(filepath):
        print(f"✅ 已修复: {filepath}")
    else:
        print(f"❌ 修复失败")
