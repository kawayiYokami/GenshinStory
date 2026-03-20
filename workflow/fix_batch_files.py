#!/usr/bin/env python3
"""修复批次文件中的格式问题"""
import json
from pathlib import Path

batch_files = [
    'batch1_yae_miko.json', 'batch1_raiden_shogun.json', 'batch1_kamisato_ayaka.json',
    'batch2_yoimiya.json', 'batch2_kokomi.json', 'batch2_kazuha.json',
    'batch3_sayu.json', 'batch3_sara.json', 'batch3_gorou.json',
    'batch4_thoma.json', 'batch4_itto.json', 'batch4_ayato.json',
    'batch5_shinobu.json', 'batch5_heizou.json', 'batch5_kirara.json',
]

def fix_item(item):
    """修复单个item的格式问题"""

    # 修复notes：确保所有元素都是字符串
    if 'notes' in item:
        fixed_notes = []
        for note in item['notes']:
            if isinstance(note, str):
                fixed_notes.append(note)
            elif isinstance(note, dict):
                # 将字典转换为字符串
                fixed_notes.append(json.dumps(note, ensure_ascii=False))
            else:
                fixed_notes.append(str(note))
        item['notes'] = fixed_notes

    # 修复events：确保每个event都有evidence字段
    if 'events' in item:
        for event in item['events']:
            if 'evidence' not in event:
                # 添加默认evidence
                event['evidence'] = {
                    'file_path': item.get('file_path', 'unknown'),
                    'chunk_id': item.get('chunk_id', 'unknown'),
                    'quote': event.get('summary', '')[:100] if event.get('summary') else ''
                }

    # 修复relations：确保每个relation都有evidence字段
    if 'relations' in item:
        for relation in item['relations']:
            if 'evidence' not in relation:
                relation['evidence'] = {
                    'file_path': item.get('file_path', 'unknown'),
                    'chunk_id': item.get('chunk_id', 'unknown'),
                    'quote': relation.get('reason', '')[:100] if relation.get('reason') else ''
                }

    return item

def fix_batch_file(filepath):
    """修复单个批次文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'items' not in data:
        return False

    fixed_items = []
    for item in data['items']:
        fixed_item = fix_item(item)
        fixed_items.append(fixed_item)

    data['items'] = fixed_items

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True

if __name__ == "__main__":
    batch_dir = Path('graph_batches')
    fixed_count = 0

    for filename in batch_files:
        filepath = batch_dir / filename
        if not filepath.exists():
            print(f"⚠️ 文件不存在: {filename}")
            continue

        try:
            if fix_batch_file(filepath):
                fixed_count += 1
                print(f"✅ 已修复: {filename}")
        except Exception as e:
            print(f"❌ 修复失败 {filename}: {e}")

    print(f"\n📊 共修复 {fixed_count} 个文件")
