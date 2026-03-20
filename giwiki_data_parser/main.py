"""原神Wiki数据解析器主程序"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .services.dataloader import DataLoader
from .services.cache_service import CacheService

# 导入所有解释器
from .interpreters.character_story_261_interpreter import CharacterStoryInterpreter
from .interpreters.enemy_6_interpreter import EnemyInterpreter
from .interpreters.weapon_5_interpreter import WeaponInterpreter
from .interpreters.book_68_interpreter import BookInterpreter
from .interpreters.organization_255_interpreter import OrganizationInterpreter
from .interpreters.character_25_interpreter import CharacterInterpreter
from .interpreters.quest_43_interpreter import QuestInterpreter
from .interpreters.artifact_218_interpreter import ArtifactInterpreter
from .interpreters.inventory_item_13_interpreter import InventoryItemInterpreter
from .interpreters.npc_shop_20_interpreter import NPCInterpreter
from .interpreters.animal_49_interpreter import AnimalInterpreter
from .interpreters.food_21_interpreter import FoodInterpreter
from .interpreters.domain_54_interpreter import DomainInterpreter
from .interpreters.adventurers_guild_55_interpreter import AdventurerGuildInterpreter
from .interpreters.map_text_251_interpreter import MapTextInterpreter
from .interpreters.outfit_211_interpreter import OutfitInterpreter

# 导入所有格式化器
from .formatters.character_story_261_formatter import CharacterStoryFormatter
from .formatters.enemy_6_formatter import EnemyFormatter
from .formatters.weapon_5_formatter import WeaponFormatter
from .formatters.book_68_formatter import BookFormatter
from .formatters.organization_255_formatter import OrganizationFormatter
from .formatters.character_25_formatter import CharacterFormatter
from .formatters.quest_43_formatter import QuestFormatter
from .formatters.artifact_218_formatter import ArtifactFormatter
from .formatters.inventory_item_13_formatter import InventoryItemFormatter
from .formatters.npc_shop_20_formatter import NPCFormatter
from .formatters.animal_49_formatter import AnimalFormatter
from .formatters.food_21_formatter import FoodFormatter
from .formatters.domain_54_formatter import DomainFormatter
from .formatters.simple_formatter import SimpleAdventurerGuildFormatter
from .formatters.map_text_251_formatter import MapTextFormatter
from .formatters.outfit_211_formatter import OutfitFormatter


class GiWikiDataParser:
    """原神Wiki数据解析器"""

    def __init__(self, data_dir: str = "gi_wiki_scraper/output/structured_data",
                 output_dir: str = "output/giwiki_markdown"):
        """
        初始化解析器

        Args:
            data_dir: 数据目录路径
            output_dir: 输出目录路径
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.data_loader = DataLoader(str(self.data_dir))
        self.cache_service = CacheService()

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # 注册所有解析器
        self.parsers = {
            "261_角色逸闻": {
                "interpreter": CharacterStoryInterpreter(self.data_loader),
                "formatter": CharacterStoryFormatter(),
                "enabled": True
            },
            "6_敌人": {
                "interpreter": EnemyInterpreter(self.data_loader),
                "formatter": EnemyFormatter(),
                "enabled": True
            },
            "5_武器": {
                "interpreter": WeaponInterpreter(self.data_loader),
                "formatter": WeaponFormatter(),
                "enabled": True
            },
            "68_书籍": {
                "interpreter": BookInterpreter(self.data_loader),
                "formatter": BookFormatter(),
                "enabled": True
            },
            "255_组织": {
                "interpreter": OrganizationInterpreter(self.data_loader),
                "formatter": OrganizationFormatter(),
                "enabled": True
            },
            "25_角色": {
                "interpreter": CharacterInterpreter(self.data_loader),
                "formatter": CharacterFormatter(),
                "enabled": True
            },
            "43_任务": {
                "interpreter": QuestInterpreter(self.data_loader),
                "formatter": QuestFormatter(),
                "enabled": True
            },
            "218_圣遗物": {
                "interpreter": ArtifactInterpreter(self.data_loader),
                "formatter": ArtifactFormatter(),
                "enabled": True
            },
            "13_背包": {
                "interpreter": InventoryItemInterpreter(self.data_loader),
                "formatter": InventoryItemFormatter(),
                "enabled": True
            },
            "20_NPC&商店": {
                "interpreter": NPCInterpreter(self.data_loader),
                "formatter": NPCFormatter(),
                "enabled": True
            },
            "21_食物": {
                "interpreter": FoodInterpreter(self.data_loader),
                "formatter": FoodFormatter(),
                "enabled": True
            },
            "49_动物": {
                "interpreter": AnimalInterpreter(self.data_loader),
                "formatter": AnimalFormatter(),
                "enabled": True
            },
            "54_秘境": {
                "interpreter": DomainInterpreter(self.data_loader),
                "formatter": DomainFormatter(),
                "enabled": True
            },
            "55_冒险家协会": {
                "interpreter": AdventurerGuildInterpreter(self.data_loader),
                "formatter": SimpleAdventurerGuildFormatter(),
                "enabled": True
            },
            "251_地图文本": {
                "interpreter": MapTextInterpreter(self.data_loader),
                "formatter": MapTextFormatter(),
                "enabled": True
            },
            "211_装扮": {
                "interpreter": OutfitInterpreter(self.data_loader),
                "formatter": OutfitFormatter(),
                "enabled": True
            }
        }

        # 跳过的数据类型（无故事价值或数据为空）
        self.skipped_types = {
            "65_深境螺旋": "纯游戏机制数据",
            "105_活动": "临时活动数据",
            "109_名片": "装饰性数据",
            "130_洞天": "建造系统数据",
            "227_教程": "教程数据",
            "244_头像": "装饰性数据",
            "249_幻想真境剧诗": "游戏机制数据",
            "252_成就": "成就系统数据",
            "257_空月之歌": "数据为空，无实际内容"
        }

    def parse_all(self, max_workers: int = 4) -> Dict[str, Any]:
        """
        解析所有数据类型

        Args:
            max_workers: 最大并发工作线程数

        Returns:
            解析结果统计
        """
        self.logger.info("开始解析原神Wiki数据...")

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        results = {
            "processed": {},
            "skipped": self.skipped_types,
            "errors": {},
            "total_files": 0,
            "success_files": 0,
            "error_files": 0
        }

        # 并发处理所有启用的解析器
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_type = {
                executor.submit(self._parse_data_type, data_type, config): data_type
                for data_type, config in self.parsers.items()
                if config["enabled"]
            }

            for future in as_completed(future_to_type):
                data_type = future_to_type[future]
                try:
                    result = future.result()
                    results["processed"][data_type] = result
                    results["total_files"] += result["total"]
                    results["success_files"] += result["success"]
                    results["error_files"] += result["errors"]

                    self.logger.info(f"完成 {data_type}: {result['success']}/{result['total']} 文件")

                except Exception as e:
                    self.logger.error(f"处理 {data_type} 时发生错误: {e}")
                    results["errors"][data_type] = str(e)

        # 生成统计报告
        self._generate_summary_report(results)

        self.logger.info(f"解析完成! 总计: {results['success_files']}/{results['total_files']} 文件成功")
        return results

    def _parse_data_type(self, data_type: str, config: Dict[str, Any]) -> Dict[str, int]:
        """
        解析单个数据类型

        Args:
            data_type: 数据类型名称
            config: 解析器配置

        Returns:
            处理结果统计
        """
        interpreter = config["interpreter"]
        formatter = config["formatter"]

        # 创建输出子目录
        output_subdir = self.output_dir / data_type
        output_subdir.mkdir(parents=True, exist_ok=True)

        # 加载数据
        data_files = self.data_loader.load_data_type(data_type)

        result = {
            "total": len(data_files),
            "success": 0,
            "errors": 0,
            "error_details": []
        }

        for file_id, data in data_files.items():
            try:
                # 构造文件路径用于ID提取
                file_path = self.data_dir / data_type / f"{file_id}.json"

                # 解释数据，传入文件路径
                model = interpreter._interpret_single(data, str(file_path))

                if not model:
                    continue  # 跳过解析失败的数据

                # 检查是否包含故事内容（如果模型有metadata属性）
                if hasattr(model, 'metadata') and model.metadata and hasattr(model.metadata, 'has_story_content'):
                    if not model.metadata.has_story_content:
                        continue  # 跳过无故事内容的数据

                # 格式化为Markdown
                markdown_content = formatter.format(model)

                # 生成文件名
                filename = formatter.get_filename(model)

                # 写入文件
                output_file = output_subdir / filename
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)

                result["success"] += 1

            except Exception as e:
                result["errors"] += 1
                result["error_details"].append({
                    "file_id": file_id,
                    "error": str(e)
                })
                self.logger.warning(f"处理文件 {file_id} 失败: {e}")

        return result

    def parse_single_type(self, data_type: str) -> Dict[str, Any]:
        """
        解析单个数据类型

        Args:
            data_type: 数据类型名称

        Returns:
            解析结果
        """
        if data_type not in self.parsers:
            if data_type in self.skipped_types:
                return {
                    "status": "skipped",
                    "reason": self.skipped_types[data_type]
                }
            else:
                raise ValueError(f"未知的数据类型: {data_type}")

        config = self.parsers[data_type]
        if not config["enabled"]:
            return {
                "status": "disabled",
                "reason": "解析器已禁用"
            }

        result = self._parse_data_type(data_type, config)
        result["status"] = "completed"

        return result

    def _generate_summary_report(self, results: Dict[str, Any]) -> None:
        """生成汇总报告"""
        report_lines = [
            "# 原神Wiki数据解析报告",
            "",
            f"## 总体统计",
            "",
            f"- **总文件数**: {results['total_files']}",
            f"- **成功解析**: {results['success_files']}",
            f"- **解析失败**: {results['error_files']}",
            f"- **成功率**: {results['success_files']/results['total_files']*100:.1f}%" if results['total_files'] > 0 else "- **成功率**: 0%",
            "",
            "## 已处理的数据类型",
            ""
        ]

        for data_type, result in results["processed"].items():
            report_lines.extend([
                f"### {data_type}",
                "",
                f"- 总文件数: {result['total']}",
                f"- 成功解析: {result['success']}",
                f"- 解析失败: {result['errors']}",
                ""
            ])

        if results["skipped"]:
            report_lines.extend([
                "## 跳过的数据类型",
                ""
            ])
            for data_type, reason in results["skipped"].items():
                report_lines.append(f"- **{data_type}**: {reason}")
            report_lines.append("")

        if results["errors"]:
            report_lines.extend([
                "## 处理错误",
                ""
            ])
            for data_type, error in results["errors"].items():
                report_lines.append(f"- **{data_type}**: {error}")

        # 写入报告文件
        report_file = self.output_dir / "解析报告.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))

        self.logger.info(f"解析报告已生成: {report_file}")

    def get_supported_data_types(self) -> List[str]:
        """获取所有支持的数据类型"""
        return list(self.parsers.keys())

    def parse_file(self, file_path: str) -> Optional[Any]:
        """
        解析单个文件

        Args:
            file_path: 文件路径

        Returns:
            解析后的数据对象，如果解析失败返回None
        """
        try:
            # 从文件路径确定数据类型
            path_obj = Path(file_path)
            data_type = path_obj.parent.name

            if data_type not in self.parsers:
                self.logger.warning(f"不支持的数据类型: {data_type}")
                return None

            # 加载JSON数据
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 解释数据，传入文件路径用于ID提取
            interpreter = self.parsers[data_type]["interpreter"]
            model = interpreter._interpret_single(data, file_path)

            return model

        except Exception as e:
            self.logger.error(f"解析文件 {file_path} 失败: {e}")
            return None

    def format_to_markdown(self, model: Any, data_type: str) -> Optional[str]:
        """
        将数据模型格式化为Markdown

        Args:
            model: 数据模型
            data_type: 数据类型

        Returns:
            Markdown内容，如果格式化失败返回None
        """
        try:
            if data_type not in self.parsers:
                return None

            formatter = self.parsers[data_type]["formatter"]
            return formatter.format(model)

        except Exception as e:
            self.logger.error(f"格式化数据失败: {e}")
            return None

    def build_cache_with_index(self) -> None:
        """构建缓存并创建搜索索引"""
        self.logger.info("开始构建缓存和搜索索引...")

        for data_type, config in self.parsers.items():
            if not config["enabled"]:
                continue

            self.logger.info(f"处理数据类型: {data_type}")
            interpreter = config["interpreter"]
            formatter = config["formatter"]

            # 加载数据
            data_files = self.data_loader.load_data_type(data_type)

            for file_id, data in data_files.items():
                try:
                    # 检查解释器是否有_interpret_single方法
                    if not hasattr(interpreter, '_interpret_single'):
                        self.logger.error(f"解释器 {type(interpreter).__name__} 缺少 _interpret_single 方法")
                        raise AttributeError(f"解释器 {type(interpreter).__name__} 缺少 _interpret_single 方法")

                    # 构造文件路径用于ID提取
                    file_path = self.data_dir / data_type / f"{file_id}.json"

                    # 解释数据
                    model = interpreter._interpret_single(data, str(file_path))
                    if not model:
                        continue

                    # 添加到缓存
                    self.cache_service.add_item(model, data_type)

                    # 生成Markdown内容用于索引
                    markdown_content = formatter.format(model)

                    # 建立搜索索引
                    item_name = getattr(model, 'name', None) or getattr(model, 'title', None) or model.id
                    tags = getattr(model, 'tags', None)
                    self.cache_service.index_item(
                        model.id,
                        item_name,
                        data_type,
                        markdown_content,
                        tags=tags
                    )

                except Exception as e:
                    self.logger.error(f"处理文件 {file_id} 失败: {e}")
                    raise  # 立即停止执行

        # 输出统计信息
        stats = self.cache_service.get_statistics()
        self.logger.info(f"缓存构建完成: {stats}")

    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """搜索功能"""
        return self.cache_service.search(query, limit)

    def get_cache_data(self) -> Dict[str, Any]:
        """获取缓存数据"""
        return {
            "data_dir": str(self.data_dir),
            "output_dir": str(self.output_dir),
            "parsers_config": {
                data_type: {"enabled": config["enabled"]}
                for data_type, config in self.parsers.items()
            },
            "cache_service": self.cache_service
        }

    def load_cache_data(self, cache_data: Dict[str, Any]) -> None:
        """加载缓存数据"""
        if "parsers_config" in cache_data:
            for data_type, config in cache_data["parsers_config"].items():
                if data_type in self.parsers:
                    self.parsers[data_type]["enabled"] = config.get("enabled", True)

        if "cache_service" in cache_data:
            self.cache_service = cache_data["cache_service"]

    def save_cache(self, file_path: str) -> None:
        """保存缓存到文件"""
        self.cache_service.save(file_path)
        self.logger.info(f"缓存已保存到: {file_path}")

    def load_cache(self, file_path: str) -> None:
        """从文件加载缓存"""
        self.cache_service = CacheService.load(file_path)
        self.logger.info(f"缓存已从文件加载: {file_path}")


def main():
    """主函数"""
    parser = GiWikiDataParser()
    results = parser.parse_all()

    print("\n=== 解析完成 ===")
    print(f"总计处理: {results['success_files']}/{results['total_files']} 文件")
    print(f"成功率: {results['success_files']/results['total_files']*100:.1f}%" if results['total_files'] > 0 else "成功率: 0%")

    if results['errors']:
        print(f"\n处理错误的数据类型: {len(results['errors'])}")
        for data_type, error in results['errors'].items():
            print(f"  - {data_type}: {error}")


if __name__ == "__main__":
    main()