"""
原神Wiki 食物数据模型

处理食物相关的数据结构，专注于提取品质变体和描述内容。
"""

from typing import List, Optional
from pydantic import Field
from ._core import BaseWikiModel, WikiMetadata


class FoodVariant(BaseWikiModel):
    """食物品质变体模型"""

    name: str = Field(..., description="变体名称")
    description: str = Field(..., description="变体描述")


class FoodModel(BaseWikiModel):
    """食物数据模型"""

    # 基础信息
    food_name: str = Field(..., description="食物名称")

    # 品质变体
    quality_variants: List[FoodVariant] = Field(default_factory=list, description="品质变体列表")

    def get_base_food_name(self) -> str:
        """获取基础食物名称"""
        return self.food_name.strip()

    def has_special_dish(self) -> bool:
        """判断是否包含特色料理"""
        for variant in self.quality_variants:
            if "特色料理" in variant.description or "的特色料理" in variant.name:
                return True
        return False

    def get_special_dish(self) -> Optional[FoodVariant]:
        """获取特色料理变体"""
        for variant in self.quality_variants:
            if "特色料理" in variant.description or "的特色料理" in variant.name:
                return variant
        return None

    def get_quality_levels(self) -> List[str]:
        """获取所有品质等级"""
        quality_levels = []
        for variant in self.quality_variants:
            if variant.name.startswith("奇怪的"):
                quality_levels.append("奇怪")
            elif variant.name.startswith("美味的"):
                quality_levels.append("美味")
            elif "特色料理" in variant.description:
                quality_levels.append("特色")
            else:
                quality_levels.append("普通")
        return quality_levels

    def has_story_content(self) -> bool:
        """判断是否包含故事内容"""
        # 检查是否有特色料理（通常包含角色故事）
        if self.has_special_dish():
            return True

        # 检查描述是否包含故事性内容
        all_descriptions = " ".join([variant.description for variant in self.quality_variants])
        story_indicators = [
            "特色料理", "秘制", "独门", "传说", "故事", "回忆",
            "角色", "专属", "特制", "心意", "情感"
        ]

        return any(indicator in all_descriptions for indicator in story_indicators)


class FoodCollection(BaseWikiModel):
    """食物集合模型"""

    foods: List[FoodModel] = Field(default_factory=list, description="食物列表")
    metadata: WikiMetadata = Field(default_factory=WikiMetadata, description="元数据")

    def get_story_foods(self) -> List[FoodModel]:
        """获取包含故事内容的食物"""
        return [food for food in self.foods if food.has_story_content()]

    def get_special_dishes(self) -> List[FoodModel]:
        """获取包含特色料理的食物"""
        return [food for food in self.foods if food.has_special_dish()]

    def search_by_keyword(self, keyword: str) -> List[FoodModel]:
        """按关键词搜索食物"""
        results = []

        for food in self.foods:
            # 在食物名称和描述中搜索
            search_text = f"{food.food_name} {' '.join([v.name + ' ' + v.description for v in food.quality_variants])}"
            if keyword.lower() in search_text.lower():
                results.append(food)

        return results

    def group_by_quality_count(self) -> dict:
        """按品质变体数量分组"""
        quality_groups = {}

        for food in self.foods:
            count = len(food.quality_variants)
            if count not in quality_groups:
                quality_groups[count] = []
            quality_groups[count].append(food)

        return quality_groups