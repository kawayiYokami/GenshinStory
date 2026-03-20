#!/usr/bin/env python3
"""合并所有稻妻城角色知识图谱并导入世界树"""
import json
import os
from pathlib import Path
import urllib.request
import urllib.error

# 所有批次文件
batch_files = [
    "batch1_yae_miko.json",
    "batch1_raiden_shogun.json",
    "batch1_kamisato_ayaka.json",
    "batch2_yoimiya.json",
    "batch2_kokomi.json",
    "batch2_kazuha.json",
    "batch3_sayu.json",
    "batch3_sara.json",
    "batch3_gorou.json",
    "batch4_thoma.json",
    "batch4_itto.json",
    "batch4_ayato.json",
    "batch5_shinobu.json",
    "batch5_heizou.json",
    "batch5_kirara.json",
]

def merge_batches():
    """合并所有批次文件"""
    merged = {
        "entities": [],
        "relations": [],
        "events": []
    }

    batch_dir = Path(__file__).parent / "graph_batches"

    stats = {
        "processed": 0,
        "failed": [],
        "entity_count": 0,
        "relation_count": 0,
        "event_count": 0
    }

    for filename in batch_files:
        filepath = batch_dir / filename
        if not filepath.exists():
            print(f"⚠️ 文件不存在: {filename}")
            stats["failed"].append(filename)
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 处理嵌套的items结构
            items = data.get("items", [])
            for item in items:
                if "entities" in item:
                    merged["entities"].extend(item["entities"])
                    stats["entity_count"] += len(item["entities"])
                if "relations" in item:
                    merged["relations"].extend(item["relations"])
                    stats["relation_count"] += len(item["relations"])
                if "events" in item:
                    merged["events"].extend(item["events"])
                    stats["event_count"] += len(item["events"])

            stats["processed"] += 1
            print(f"✅ 已合并: {filename} (items: {len(items)})")
        except Exception as e:
            print(f"❌ 处理失败 {filename}: {e}")
            stats["failed"].append(filename)

    # 保存合并后的文件
    output_path = batch_dir / "inazuma_characters_merged.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"\n📊 合并统计:")
    print(f"  - 成功处理: {stats['processed']}/{len(batch_files)}")
    print(f"  - 总实体数: {stats['entity_count']}")
    print(f"  - 总关系数: {stats['relation_count']}")
    print(f"  - 总事件数: {stats['event_count']}")
    print(f"  - 失败文件: {len(stats['failed'])}")
    print(f"\n💾 合并文件已保存: {output_path}")

    return merged, output_path

def import_to_world_tree(items_data, dry_run=True):
    """导入到世界树后端"""
    api_url = "http://127.0.0.1:8000/api/world-tree/import-graph"

    # API期望的格式: { "items": [...], "dry_run": bool }
    payload = {
        "items": items_data,
        "dry_run": dry_run,
        "source_tag": "稻妻城角色批量导入"
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        headers = {
            'Content-Type': 'application/json',
            'Content-Length': len(data)
        }

        req = urllib.request.Request(api_url, data=data, headers=headers, method='POST')

        with urllib.request.urlopen(req, timeout=120) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                print(f"\n✅ 导入成功!")
                print(f"  - 总计: {result.get('total', 'N/A')}")
                print(f"  - 有效: {result.get('valid_count', 'N/A')}")
                print(f"  - 无效: {result.get('invalid_count', 'N/A')}")
                print(f"  - 已导入: {result.get('imported_count', 'N/A')}")
                if result.get('errors'):
                    print(f"  - 错误数: {len(result.get('errors', []))}")
                return result.get('ok', False), result
            else:
                print(f"\n❌ 导入失败: HTTP {response.status}")
                return False, None
    except urllib.error.HTTPError as e:
        print(f"\n❌ 导入失败: HTTP {e.code}")
        try:
            error_body = e.read().decode('utf-8')
            print(f"  响应: {error_body[:500]}")
        except:
            pass
        return False, None
    except Exception as e:
        print(f"\n❌ 导入异常: {e}")
        return False, None

def load_batch_items():
    """加载所有批次文件并返回items列表"""
    batch_dir = Path(__file__).parent / "graph_batches"
    all_items = []

    for filename in batch_files:
        filepath = batch_dir / filename
        if not filepath.exists():
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            items = data.get("items", [])
            for item in items:
                # 确保每个item有必要的字段
                if "file_path" in item and "chunk_id" in item:
                    all_items.append(item)
        except Exception as e:
            print(f"⚠️ 加载失败 {filename}: {e}")

    return all_items


if __name__ == "__main__":
    print("=" * 60)
    print("稻妻城角色知识图谱 - 合并与导入工具")
    print("=" * 60)

    # 合并所有批次（用于统计）
    print("\n🔄 步骤1: 合并所有批次文件...")
    merged_data, merged_path = merge_batches()

    # 加载所有items用于导入
    print("\n🔄 步骤2: 加载所有图谱items...")
    items = load_batch_items()
    print(f"  - 共加载 {len(items)} 个图谱项")

    if len(items) == 0:
        print("\n❌ 没有可导入的数据!")
        exit(1)

    print("\n" + "=" * 60)
    print("🔄 步骤3: 准备导入世界树...")

    # 先进行dry_run测试
    print("\n📋 首先进行 dry_run 测试...")
    success, result = import_to_world_tree(items, dry_run=True)

    if success:
        print("\n✅ dry_run 测试通过!")

        # 分批正式导入（每批5个）
        print("\n🚀 执行正式导入...")
        batch_size = 5
        total_imported = 0

        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            print(f"\n  导入批次 {i//batch_size + 1}/{(len(items)-1)//batch_size + 1} ({len(batch)} 项)...")

            success, result = import_to_world_tree(batch, dry_run=False)
            if success and result:
                total_imported += result.get('imported_count', 0)
            else:
                print(f"  ⚠️ 该批次导入失败")

        print(f"\n🎉 全部完成! 共导入 {total_imported} 个稻妻城角色图谱项!")
    else:
        print("\n⚠️ dry_run 测试失败，请检查数据格式")
        if result and result.get('errors'):
            for err in result['errors'][:3]:
                print(f"  - 错误: {err.get('message', '未知错误')}")
