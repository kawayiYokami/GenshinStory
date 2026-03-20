#!/usr/bin/env python3
"""
标签分析工具

分析缓存文件中的标签数据，输出每个数据类型的所有可用标签字段和统计信息，
供用户选择最合适的分类字段。
"""

import os
import sys
import logging
from collections import defaultdict, Counter
from typing import Dict, List, Any, Set

# Setup project root path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from giwiki_data_parser.services.cache_service import CacheService

# 配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
CACHE_FILE_PATH = "giwiki_data_parser/cache/giwiki_data.cache.gz"

def analyze_tags_for_data_type(data_list: List[Any], type_name: str) -> Dict[str, Any]:
    """分析单个数据类型的标签"""
    if not data_list:
        return {"type_name": type_name, "count": 0, "tag_analysis": {}}

    # 统计所有标签键和值
    tag_stats = defaultdict(Counter)
    items_with_tags = 0

    for item in data_list:
        if hasattr(item, 'tags') and item.tags:
            items_with_tags += 1
            for tag_key, tag_value in item.tags.items():
                if tag_value:  # 只统计非空值
                    tag_stats[tag_key][tag_value] += 1

    # 整理统计结果
    tag_analysis = {}
    for tag_key, value_counter in tag_stats.items():
        unique_values = len(value_counter)
        total_occurrences = sum(value_counter.values())
        most_common = value_counter.most_common(10)  # 显示前10个最常见的值

        tag_analysis[tag_key] = {
            "unique_values": unique_values,
            "total_occurrences": total_occurrences,
            "coverage": total_occurrences / len(data_list) * 100,  # 覆盖率
            "most_common_values": most_common
        }

    return {
        "type_name": type_name,
        "total_items": len(data_list),
        "items_with_tags": items_with_tags,
        "tag_coverage": items_with_tags / len(data_list) * 100 if data_list else 0,
        "tag_analysis": tag_analysis
    }

def print_analysis_results(results: List[Dict[str, Any]]):
    """打印分析结果"""
    print("=" * 80)
    print("标签分析结果")
    print("=" * 80)

    for result in results:
        if result["total_items"] == 0:
            continue

        print(f"\n📊 数据类型: {result['type_name']}")
        print(f"   总项目数: {result['total_items']}")
        print(f"   有标签的项目: {result['items_with_tags']} ({result['tag_coverage']:.1f}%)")

        if not result["tag_analysis"]:
            print("   ❌ 无标签数据")
            continue

        print(f"   📋 可用标签字段 ({len(result['tag_analysis'])} 个):")

        # 按唯一值数量排序，便于选择合适的分类字段
        sorted_tags = sorted(
            result["tag_analysis"].items(),
            key=lambda x: x[1]["unique_values"]
        )

        for tag_key, tag_info in sorted_tags:
            print(f"      🏷️  '{tag_key}':")
            print(f"         - 唯一值数量: {tag_info['unique_values']}")
            print(f"         - 覆盖率: {tag_info['coverage']:.1f}%")
            print(f"         - 常见值: {', '.join([f'{v}({c})' for v, c in tag_info['most_common_values'][:5]])}")

            # 给出分类建议
            unique_count = tag_info['unique_values']
            coverage = tag_info['coverage']

            if 2 <= unique_count <= 20 and coverage >= 80:
                print(f"         ✅ 推荐用于分类 (值数量适中，覆盖率高)")
            elif unique_count > 50:
                print(f"         ⚠️  值过多，不适合分类")
            elif coverage < 50:
                print(f"         ⚠️  覆盖率低，不适合分类")
            elif unique_count == 1:
                print(f"         ❌ 只有一个值，无法分类")
            else:
                print(f"         🤔 可考虑用于分类")

def main():
    """主函数"""
    if not os.path.exists(CACHE_FILE_PATH):
        print(f"❌ 缓存文件不存在: {CACHE_FILE_PATH}")
        print("请先运行 scripts/giwiki_create_cache.py 创建缓存")
        sys.exit(1)

    print(f"📂 加载缓存文件: {CACHE_FILE_PATH}")
    try:
        cache_service = CacheService.load(CACHE_FILE_PATH)
        print("✅ 缓存加载成功")
    except Exception as e:
        print(f"❌ 加载缓存失败: {e}")
        sys.exit(1)

    # 获取所有数据类型
    data_types = [
        ("characters", cache_service.characters),
        ("weapons", cache_service.weapons),
        ("artifacts", cache_service.artifacts),
        ("enemies", cache_service.enemies),
        ("animals", cache_service.animals),
        ("inventory_items", cache_service.inventory_items),
        ("npc_shops", cache_service.npc_shops),
        ("organizations", cache_service.organizations),
        ("character_stories", cache_service.character_stories),
        ("map_texts", cache_service.map_texts),
        ("foods", cache_service.foods),
        ("domains", cache_service.domains),
        ("outfits", cache_service.outfits),  # 新增的装扮类型
        ("quests", cache_service.quests),
        ("books", cache_service.books),
    ]

    # 分析每个数据类型
    results = []
    for type_name, data_list in data_types:
        print(f"🔍 分析 {type_name}...")
        result = analyze_tags_for_data_type(data_list, type_name)
        results.append(result)

    # 打印结果
    print_analysis_results(results)

    print("\n" + "=" * 80)
    print("💡 使用建议:")
    print("1. 选择 '✅ 推荐用于分类' 的标签字段")
    print("2. 优先选择唯一值数量在 2-20 之间的字段")
    print("3. 优先选择覆盖率高的字段")
    print("4. 考虑语义上有分类意义的字段")
    print("=" * 80)

if __name__ == "__main__":
    main()