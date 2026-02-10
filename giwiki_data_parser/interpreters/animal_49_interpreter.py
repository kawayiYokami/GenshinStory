"""
原神Wiki动物数据解释器

负责将JSON数据转换为动物数据模型，专注于提取背景故事和世界观内容。
"""

import logging
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.animal_49 import AnimalModel
from giwiki_data_parser.services.dataloader import DataLoader


class AnimalInterpreter:
    """动物数据解释器"""
    
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)
    
    def interpret(self, data: Dict[str, Any]) -> Optional[AnimalModel]:
        """解析单个动物数据 - 公共接口"""
        return self._interpret_single(data)
    
    def interpret_all(self) -> List[AnimalModel]:
        """解析所有动物数据"""
        animals = []
        raw_data_iterator = self.loader.get_animals()
        
        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                animal = self._interpret_single(data, file_path)
                if animal:
                    animals.append(animal)
            except Exception as e:
                self.logger.error(f"解析动物数据时出错: {e}")
        
        self.logger.info(f"成功解析 {len(animals)} 个动物")
        return animals
    
    def _interpret_single(self, data: Dict[str, Any], file_path: str = "") -> Optional[AnimalModel]:
        """解析单个动物数据"""
        try:
            # 基础数据提取
            name = data.get("名称", "").strip()
            attack_method = data.get("攻略方法", "").strip()
            background_story = data.get("背景故事", "").strip()
            notes = data.get("备注", "").strip()
            
            # 处理掉落物品
            drop_items = []
            raw_drops = data.get("掉落物品", [])
            if isinstance(raw_drops, list):
                for drop_data in raw_drops:
                    if isinstance(drop_data, dict):
                        drop_name = drop_data.get("名称", "").strip()
                        if drop_name:
                            from giwiki_data_parser.models.animal_49 import DropItem
                            drop_items.append(DropItem(name=drop_name, link=drop_data.get("链接", "")))
            
            # 创建动物对象
            animal = AnimalModel(
                name=name,
                attack_method=attack_method,
                drop_items=drop_items,
                background_story=background_story,
                notes=notes,
                images=[]
            )
            
            # 从文件路径设置ID
            if file_path:
                animal.set_id_from_filename(file_path)
            elif "_file_path" in data:
                animal.set_id_from_filename(data["_file_path"])
            elif "_file_id" in data:
                file_id = str(data["_file_id"])
                if file_id.isdigit():
                    animal.id = file_id
                else:
                    self.logger.warning(f"非数字文件ID，跳过: {file_id}")
                    return None
            
            return animal
            
        except Exception as e:
            self.logger.error(f"解析单个动物数据时出错: {e}")
            return None