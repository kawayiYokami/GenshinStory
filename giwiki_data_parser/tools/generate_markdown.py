#!/usr/bin/env python3
"""
原神Wiki数据解析脚本
将gi_wiki_scraper的结构化数据转换为Markdown格式
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from giwiki_data_parser.main import GIWikiDataParser


def main():
    """主函数"""
    print("=== 原神Wiki数据解析器 ===")
    print("将结构化JSON数据转换为Markdown格式")
    print()
    
    # 检查数据目录是否存在
    data_dir = project_root / "gi_wiki_scraper" / "output" / "structured_data"
    if not data_dir.exists():
        print(f"错误: 数据目录不存在: {data_dir}")
        print("请先运行gi_wiki_scraper获取数据")
        return 1
    
    # 创建解析器
    output_dir = project_root / "output" / "giwiki_markdown"
    parser = GIWikiDataParser(
        data_dir=str(data_dir),
        output_dir=str(output_dir)
    )
    
    print(f"数据目录: {data_dir}")
    print(f"输出目录: {output_dir}")
    print()
    
    try:
        # 执行解析
        results = parser.parse_all(max_workers=4)
        
        print("\n=== 解析完成 ===")
        print(f"总计处理: {results['success_files']}/{results['total_files']} 文件")
        
        if results['total_files'] > 0:
            success_rate = results['success_files'] / results['total_files'] * 100
            print(f"成功率: {success_rate:.1f}%")
        else:
            print("成功率: 0%")
        
        print(f"\n已处理的数据类型: {len(results['processed'])}")
        for data_type, result in results['processed'].items():
            print(f"  - {data_type}: {result['success']}/{result['total']} 文件")
        
        print(f"\n跳过的数据类型: {len(results['skipped'])}")
        for data_type, reason in results['skipped'].items():
            print(f"  - {data_type}: {reason}")
        
        if results['errors']:
            print(f"\n处理错误: {len(results['errors'])}")
            for data_type, error in results['errors'].items():
                print(f"  - {data_type}: {error}")
        
        print(f"\n输出目录: {output_dir}")
        print("解析报告已生成: 解析报告.md")
        
        return 0
        
    except Exception as e:
        print(f"解析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)