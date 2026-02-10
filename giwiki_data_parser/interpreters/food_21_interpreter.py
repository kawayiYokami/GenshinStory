"""
原神Wiki 食物数据解释器

负责将JSON数据转换为食物数据模型，专注于提取品质变体和描述内容。
"""

import logging
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.food_21 import FoodModel, FoodVariant
from giwiki_data_parser.services.dataloader import DataLoader


class FoodInterpreter:
    """食物数据解释器"""

    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)

    def interpret(self, data: Dict[str, Any]) -> Optional[FoodModel]:
        """解析单个食物数据 - 公共接口"""
        return self._interpret_single(data)

    def interpret_all(self) -> List[FoodModel]:
        """解析所有食物数据"""
        foods = []
        raw_data_iterator = self.loader.get_food()

        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                food = self._interpret_single(data, file_path)
                if food:
                    foods.append(food)
            except Exception as e:
                self.logger.error(f"解析食物数据时出错: {e}")

        self.logger.info(f"成功解析 {len(foods)} 个食物")
        return foods

    def _interpret_single(self, data: Dict[str, Any], file_path: str = "") -> Optional[FoodModel]:
        """解析单个食物数据"""
        try:
            # 基础信息提取
            food_name = data.get("食物名称", "").strip()
            if not food_name:
                self.logger.warning("食物名称为空，跳过")
                return None

            # 解析品质变体
            quality_variants = []
            variants_data = data.get("品质变体", [])

            if isinstance(variants_data, list):
                for variant_data in variants_data:
                    if isinstance(variant_data, dict):
                        variant_name = variant_data.get("名称", "").strip()
                        variant_description = variant_data.get("描述", "").strip()

                        if variant_name and variant_description:
                            food_variant = FoodVariant(
                                name=variant_name,
                                description=variant_description
                            )
                            quality_variants.append(food_variant)

            # 创建食物对象
            food = FoodModel(
                name=food_name,  # 设置为标准name字段，与其他模型保持一致
                food_name=food_name,
                quality_variants=quality_variants
            )

            # 从文件路径设置ID
            if file_path:
                food.set_id_from_filename(file_path)
            elif "_file_path" in data:
                food.set_id_from_filename(data["_file_path"])
            elif "_file_id" in data:
                file_id = str(data["_file_id"])
                if file_id.isdigit():
                    food.id = file_id
                else:
                    self.logger.warning(f"非数字文件ID，跳过: {file_id}")
                    return None

            return food

        except Exception as e:
            self.logger.error(f"解析食物数据时出错: {e}")
            return None