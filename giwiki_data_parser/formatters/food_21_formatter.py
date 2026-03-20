"""
原神Wiki 食物数据格式化器

将食物数据转换为Markdown格式，专注于展示品质变体和描述内容。
"""

from typing import List
from ..models.food_21 import FoodModel, FoodCollection, FoodVariant


class FoodFormatter:
    """食物数据格式化器"""

    def format_single_food(self, food: FoodModel, include_metadata: bool = True) -> str:
        """格式化单个食物"""
        lines = []

        # 标题
        lines.append(f"# {food.food_name}")
        lines.append("")

        # 基本信息
        if include_metadata:
            lines.append("## 基本信息")
            lines.append("")

            lines.append(f"**食物名称**: {food.food_name}")
            lines.append(f"**品质变体数量**: {len(food.quality_variants)}")

            if food.has_special_dish():
                lines.append("**包含特色料理**: 是")
            else:
                lines.append("**包含特色料理**: 否")

            lines.append("")

        # 品质变体
        if food.quality_variants:
            lines.append("## 品质变体")
            lines.append("")
            lines.extend(self._format_quality_variants(food.quality_variants))

        return '\n'.join(lines).strip()

    def _format_quality_variants(self, variants: List[FoodVariant]) -> List[str]:
        """格式化品质变体"""
        lines = []

        for i, variant in enumerate(variants, 1):
            # 变体标题
            lines.append(f"### {i}. {variant.name}")
            lines.append("")

            # 变体描述
            lines.append(f"> {variant.description}")
            lines.append("")

            # 变体之间的分隔
            if variant != variants[-1]:  # 不是最后一个变体
                lines.append("---")
                lines.append("")

        return lines

    def format_collection(self, collection: FoodCollection, story_only: bool = True) -> str:
        """格式化食物集合"""
        lines = []

        # 标题
        lines.append("# 原神食物资料")
        lines.append("")

        # 统计信息
        total_foods = len(collection.foods)
        story_foods = collection.get_story_foods()
        special_dishes = collection.get_special_dishes()

        lines.append("## 数据概览")
        lines.append("")
        lines.append(f"- 总食物数量: {total_foods}")
        lines.append(f"- 包含故事内容: {len(story_foods)}")
        lines.append(f"- 包含特色料理: {len(special_dishes)}")
        lines.append("")

        # 选择要展示的食物
        foods_to_show = story_foods if story_only else collection.foods

        if story_only and story_foods:
            lines.append("## 故事食物")
            lines.append("")
            lines.append("以下食物包含丰富的故事内容和特色料理：")
            lines.append("")

        # 展示食物
        if foods_to_show:
            for food in foods_to_show:
                lines.append(f"### {food.food_name}")
                lines.append("")

                # 显示品质变体预览
                if food.quality_variants:
                    lines.append("**品质变体**:")
                    lines.append("")

                    for variant in food.quality_variants:
                        lines.append(f"- **{variant.name}**: {variant.description}")

                    lines.append("")

                # 特色料理标记
                if food.has_special_dish():
                    special_dish = food.get_special_dish()
                    if special_dish:
                        lines.append(f"**特色料理**: {special_dish.name}")
                        lines.append("")

                lines.append("---")
                lines.append("")

        return '\n'.join(lines).strip()

    def format_special_dishes_only(self, collection: FoodCollection) -> str:
        """仅格式化特色料理"""
        special_dishes = collection.get_special_dishes()

        if not special_dishes:
            return "# 原神特色料理\n\n暂无特色料理。"

        lines = []
        lines.append("# 原神特色料理")
        lines.append("")
        lines.append(f"共收录 {len(special_dishes)} 个包含特色料理的食物。")
        lines.append("")

        # 按食物名称排序
        special_dishes.sort(key=lambda x: x.food_name)

        for food in special_dishes:
            lines.append(f"## {food.food_name}")
            lines.append("")

            special_dish = food.get_special_dish()
            if special_dish:
                lines.append(f"### {special_dish.name}")
                lines.append("")
                lines.append(f"> {special_dish.description}")
                lines.append("")

            # 显示其他品质变体
            other_variants = [v for v in food.quality_variants if v != special_dish]
            if other_variants:
                lines.append("**其他品质变体**:")
                lines.append("")
                for variant in other_variants:
                    lines.append(f"- **{variant.name}**: {variant.description}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return '\n'.join(lines).strip()

    def get_filename(self, food: FoodModel) -> str:
        """生成文件名"""
        # 清理文件名中的特殊字符
        safe_name = food.food_name.replace("/", "_").replace("\\", "_").replace(":", "_")
        return f"{safe_name}.md"

    def format(self, food: FoodModel) -> str:
        """标准格式化方法，用于与主解析器兼容"""
        return self.format_single_food(food)