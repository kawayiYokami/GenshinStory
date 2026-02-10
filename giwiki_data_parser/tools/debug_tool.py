#!/usr/bin/env python3
"""
原神Wiki数据解析器调试工具
提供交互式命令行界面，方便调试和测试各种数据类型的解析
"""
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from giwiki_data_parser.main import GIWikiDataParser


class GIWikiDebugTool:
    """调试工具类"""
    
    def __init__(self):
        self.data_dir = project_root / "gi_wiki_scraper" / "output" / "structured_data"
        self.parser = GIWikiDataParser(
            data_dir=str(self.data_dir),
            output_dir=str(project_root / "debug_output")
        )
        
        # 数据类型映射
        self.data_types = {
            "1": ("261_角色逸闻", "角色故事和对话"),
            "2": ("6_敌人", "敌人背景故事"),
            "3": ("5_武器", "武器故事和世界观"),
            "4": ("68_书籍", "游戏内书籍内容"),
            "5": ("255_组织", "组织背景和结构"),
            "6": ("25_角色", "角色详细信息和语音"),
            "7": ("43_任务", "任务对话和故事"),
            "8": ("218_圣遗物", "圣遗物背景故事"),
            "9": ("13_背包", "物品背景故事"),
            "10": ("20_NPC&商店", "NPC对话和互动"),
            "11": ("49_动物", "生物背景和生态"),
            "12": ("55_冒险家协会", "委托任务对话"),
            "13": ("251_地图文本", "地区文化和历史"),
        }
    
    def show_main_menu(self):
        """显示主菜单"""
        print("\n" + "="*60)
        print("🎮 原神Wiki数据解析器调试工具")
        print("="*60)
        print("请选择要调试的数据类型:")
        print()
        
        for key, (data_type, description) in self.data_types.items():
            print(f"{key:>2}. {data_type:<20} - {description}")
        
        print()
        print(" 0. 退出")
        print("="*60)
    
    def show_item_menu(self, data_type: str, description: str):
        """显示项目菜单"""
        data_path = self.data_dir / data_type
        
        if not data_path.exists():
            print(f"\n❌ 数据目录不存在: {data_path}")
            return None
        
        json_files = list(data_path.glob("*.json"))
        if not json_files:
            print(f"\n❌ 数据目录为空: {data_path}")
            return None
        
        # 限制显示数量，避免菜单过长
        max_display = 20
        
        print(f"\n📁 {data_type} - {description}")
        print(f"共找到 {len(json_files)} 个文件")
        print("-" * 60)
        
        display_files = json_files[:max_display]
        for i, file_path in enumerate(display_files, 1):
            # 尝试读取文件获取标题
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                title = data.get('title', data.get('标题', data.get('文本标题', file_path.stem)))
                print(f"{i:>2}. {file_path.stem:<15} - {title[:40]}")
            except:
                print(f"{i:>2}. {file_path.stem:<15} - (读取失败)")
        
        if len(json_files) > max_display:
            print(f"... 还有 {len(json_files) - max_display} 个文件")
        
        print()
        print(" r. 随机选择一个文件")
        print(" a. 解析所有文件")
        print(" 0. 返回上级菜单")
        print("-" * 60)
        
        return json_files
    
    def show_output_menu(self):
        """显示输出格式菜单"""
        print("\n📤 选择输出格式:")
        print("-" * 30)
        print("1. JSON数据结构")
        print("2. Markdown格式")
        print("3. 两种格式都显示")
        print("0. 返回上级菜单")
        print("-" * 30)
    
    def process_single_file(self, file_path: Path, data_type: str, output_format: str):
        """处理单个文件"""
        try:
            # 读取原始数据
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            print(f"\n🔍 处理文件: {file_path.name}")
            print("="*60)
            
            # 获取对应的解析器
            if data_type not in self.parser.parsers:
                print(f"❌ 未找到 {data_type} 的解析器")
                return
            
            config = self.parser.parsers[data_type]
            interpreter = config["interpreter"]
            formatter = config["formatter"]
            
            # 解释数据
            try:
                model = interpreter.interpret(raw_data)
                print("✅ 数据解析成功")
            except Exception as e:
                print(f"❌ 数据解析失败: {e}")
                if output_format in ["1", "3"]:
                    print(f"\n📄 原始数据:")
                    print(json.dumps(raw_data, ensure_ascii=False, indent=2))
                return
            
            # 输出结果
            if output_format in ["1", "3"]:
                print(f"\n📊 解析后的数据结构:")
                print("-" * 40)
                print(model.model_dump_json(ensure_ascii=False, indent=2))
            
            if output_format in ["2", "3"]:
                print(f"\n📝 Markdown格式:")
                print("-" * 40)
                markdown_content = formatter.format(model)
                print(markdown_content)
            
            # 显示元数据
            if hasattr(model, 'metadata') and model.metadata:
                print(f"\n📋 元数据信息:")
                print("-" * 40)
                print(f"数据来源: {model.metadata.source_type}")
                print(f"包含故事内容: {'是' if model.metadata.has_story_content else '否'}")
                if model.metadata.content_tags:
                    print(f"内容标签: {', '.join(model.metadata.content_tags)}")
            
        except Exception as e:
            print(f"❌ 处理文件时发生错误: {e}")
            import traceback
            traceback.print_exc()
    
    def process_all_files(self, data_type: str, output_format: str):
        """处理所有文件"""
        print(f"\n🔄 开始处理 {data_type} 的所有文件...")
        
        try:
            result = self.parser.parse_single_type(data_type)
            
            if result.get("status") == "completed":
                print(f"✅ 处理完成!")
                print(f"总文件数: {result['total']}")
                print(f"成功解析: {result['success']}")
                print(f"解析失败: {result['errors']}")
                
                if result['errors'] > 0 and 'error_details' in result:
                    print(f"\n❌ 错误详情:")
                    for error in result['error_details'][:5]:  # 只显示前5个错误
                        print(f"  - 文件 {error['file_id']}: {error['error']}")
                    if len(result['error_details']) > 5:
                        print(f"  ... 还有 {len(result['error_details']) - 5} 个错误")
            
            elif result.get("status") == "skipped":
                print(f"⏭️ 已跳过: {result['reason']}")
            
            else:
                print(f"❌ 处理失败: {result}")
                
        except Exception as e:
            print(f"❌ 批量处理时发生错误: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """运行调试工具"""
        print("🚀 启动原神Wiki数据解析器调试工具...")
        
        # 检查数据目录
        if not self.data_dir.exists():
            print(f"❌ 数据目录不存在: {self.data_dir}")
            print("请先运行gi_wiki_scraper获取数据")
            return
        
        while True:
            self.show_main_menu()
            
            try:
                choice = input("\n请选择 (0-13): ").strip()
                
                if choice == "0":
                    print("👋 再见!")
                    break
                
                if choice not in self.data_types:
                    print("❌ 无效选择，请重新输入")
                    continue
                
                data_type, description = self.data_types[choice]
                
                # 显示项目菜单
                json_files = self.show_item_menu(data_type, description)
                if json_files is None:
                    continue
                
                while True:
                    item_choice = input(f"\n请选择项目 (1-{min(len(json_files), 20)}, r, a, 0): ").strip().lower()
                    
                    if item_choice == "0":
                        break
                    
                    # 显示输出格式菜单
                    self.show_output_menu()
                    output_choice = input("\n请选择输出格式 (1-3, 0): ").strip()
                    
                    if output_choice == "0":
                        continue
                    
                    if output_choice not in ["1", "2", "3"]:
                        print("❌ 无效的输出格式选择")
                        continue
                    
                    if item_choice == "r":
                        # 随机选择
                        import random
                        selected_file = random.choice(json_files)
                        self.process_single_file(selected_file, data_type, output_choice)
                    
                    elif item_choice == "a":
                        # 处理所有文件
                        self.process_all_files(data_type, output_choice)
                    
                    else:
                        # 选择特定文件
                        try:
                            file_index = int(item_choice) - 1
                            if 0 <= file_index < min(len(json_files), 20):
                                selected_file = json_files[file_index]
                                self.process_single_file(selected_file, data_type, output_choice)
                            else:
                                print("❌ 无效的文件选择")
                        except ValueError:
                            print("❌ 请输入有效的数字")
                    
                    input("\n按回车键继续...")
            
            except KeyboardInterrupt:
                print("\n\n👋 用户中断，再见!")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                input("按回车键继续...")


def main():
    """主函数"""
    tool = GIWikiDebugTool()
    tool.run()


if __name__ == "__main__":
    main()