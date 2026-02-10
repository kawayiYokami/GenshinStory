"""
JSON模板生成器 - HSR Wiki Scraper版本
用于为hsr_wiki_scraper的所有解析器生成JSON模板文件
"""
import json
import importlib
from pathlib import Path
from typing import Dict, Any, List
from hsr_wiki_scraper.parsers.base_parser import BaseParser


class TemplateGenerator:
    """模板生成器类 - HSR Wiki Scraper版本"""

    # HSR指定需要生成模板的解析器类别
    INCLUDED_CATEGORIES = {
        "18",   # 角色
        "19",   # 光锥
        "20",   # 养成材料
        "25",   # 任务
        "30",   # 遗器
        "31",   # 阅读物
        "53",   # 任务道具
        "54",   # 贵重物
        "55",   # 其他材料
        "103",  # 模拟宇宙·事件图鉴
        "157",  # 装扮
    }

    def __init__(self, parsers_dir: Path, output_dir: Path):
        """
        初始化模板生成器

        Args:
            parsers_dir (Path): 解析器目录路径
            output_dir (Path): 模板输出目录路径
        """
        self.parsers_dir = parsers_dir
        self.output_dir = output_dir

    def generate_all_templates(self) -> None:
        """为所有指定解析器生成模板文件"""
        print("开始生成HSR Wiki Scraper的JSON模板文件...")

        # HSR解析器文件名到类名的映射
        parser_mappings = {
            "18": "parser_18_角色.CharacterParser",
            "19": "parser_19_光锥.LightConeParser",
            "20": "parser_20_养成材料.CultivationMaterialParser",
            "25": "parser_25_任务.TaskParser",
            "30": "parser_30_遗器.RelicParser",
            "31": "parser_31_阅读物.ReadingMaterialParser",
            "53": "parser_53_任务道具.QuestItemParser",
            "54": "parser_54_贵重物.ValuableParser",
            "55": "parser_55_其他材料.OtherMaterialParser",
            "103": "parser_103_模拟宇宙·事件图鉴.RogueEventParser",
            "157": "parser_157_装扮.OutfitParser"
        }

        generated_count = 0
        failed_count = 0

        for category_id, parser_class_path in parser_mappings.items():
            try:
                # 动态导入解析器类
                parser_class = self._import_parser_class(parser_class_path)
                if parser_class:
                    # 创建解析器实例
                    parser_instance = parser_class()

                    # 获取模板
                    template = parser_instance.get_template()

                    # 保存模板文件
                    self._save_template(category_id, parser_class_path, template)
                    generated_count += 1
                    print(f"✓ 已生成模板: {parser_class_path}")
                else:
                    failed_count += 1
                    print(f"✗ 导入失败: {parser_class_path}")

            except Exception as e:
                failed_count += 1
                print(f"✗ 生成模板失败 {parser_class_path}: {e}")

        print(f"\nHSR模板生成完成！")
        print(f"成功生成: {generated_count} 个模板")
        print(f"失败: {failed_count} 个模板")

    def _import_parser_class(self, parser_class_path: str):
        """
        动态导入解析器类

        Args:
            parser_class_path (str): 解析器类路径，格式为 "module_name.ClassName"

        Returns:
            type: 解析器类，如果导入失败返回None
        """
        try:
            module_name, class_name = parser_class_path.split('.')
            module_path = f"hsr_wiki_scraper.parsers.{module_name}"

            # 动态导入模块
            module = importlib.import_module(module_path)

            # 获取类
            parser_class = getattr(module, class_name)

            # 验证是否是BaseParser的子类
            if issubclass(parser_class, BaseParser):
                return parser_class
            else:
                print(f"警告: {parser_class_path} 不是BaseParser的子类")
                return None

        except (ImportError, AttributeError, ValueError) as e:
            print(f"导入解析器失败 {parser_class_path}: {e}")
            return None

    def _save_template(self, category_id: str, parser_class_path: str, template: Dict[str, Any]) -> None:
        """
        保存模板到文件

        Args:
            category_id (str): 类别ID
            parser_class_path (str): 解析器类路径
            template (Dict[str, Any]): 模板数据
        """
        # 从类路径中提取模块名
        module_name = parser_class_path.split('.')[0]

        # 生成文件名
        filename = f"{module_name}_template.json"
        filepath = self.output_dir / filename

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 保存模板文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)

        print(f"模板已保存到: {filepath}")


if __name__ == "__main__":
    # 测试模板生成器
    print("启动HSR Wiki Scraper模板生成器...")
    project_root = Path(__file__).parent.parent
    parsers_dir = project_root / "hsr_wiki_scraper" / "parsers"
    templates_dir = project_root / "hsr_wiki_scraper" / "output" / "templates"

    print(f"项目根目录: {project_root}")
    print(f"解析器目录: {parsers_dir}")
    print(f"模板输出目录: {templates_dir}")

    generator = TemplateGenerator(parsers_dir, templates_dir)
    generator.generate_all_templates()