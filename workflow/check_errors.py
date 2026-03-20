#!/usr/bin/env python3
import json
import urllib.request
from pathlib import Path

batch_files = [
    'batch1_yae_miko.json', 'batch1_raiden_shogun.json', 'batch1_kamisato_ayaka.json',
    'batch2_yoimiya.json', 'batch2_kokomi.json', 'batch2_kazuha.json',
    'batch3_sayu.json', 'batch3_sara.json', 'batch3_gorou.json',
    'batch4_thoma.json', 'batch4_itto.json', 'batch4_ayato.json',
    'batch5_shinobu.json', 'batch5_heizou.json', 'batch5_kirara.json',
]

all_items = []
batch_dir = Path('graph_batches')
for fn in batch_files:
    with open(batch_dir / fn, 'r', encoding='utf-8') as f:
        data = json.load(f)
        all_items.extend(data.get('items', []))

print(f"共加载 {len(all_items)} 个items")

# 调用dry_run获取详细错误
payload = {'items': all_items, 'dry_run': True}
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/world-tree/import-graph',
                              data=data, headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req, timeout=60) as resp:
    result = json.loads(resp.read().decode())
    print(f"\n总计: {result.get('total')}, 有效: {result.get('valid_count')}, 无效: {result.get('invalid_count')}")
    for err in result.get('errors', []):
        print(f"\nItem {err.get('item_index')}: {err.get('message')}")
        if err.get('details'):
            for d in err['details'][:3]:
                print(f"  - {d.get('field')}: {d.get('message')}")
