"""
原神Wiki物品数据解释器

负责将JSON数据转换为物品数据模型，专注于提取故事和世界观内容。
"""

import logging
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.inventory_item_13 import InventoryItemModel
from giwiki_data_parser.services.dataloader import DataLoader


class InventoryItemInterpreter:
    """物品数据解释器"""
    
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)
    
    def interpret(self, data: Dict[str, Any]) -> Optional[InventoryItemModel]:
        """解析单个物品数据 - 公共接口"""
        return self._interpret_single(data)
    
    def interpret_all(self) -> List[InventoryItemModel]:
        """解析所有物品数据"""
        items = []
        raw_data_iterator = self.loader.get_items()
        
        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                item = self._interpret_single(data, file_path)
                if item:
                    items.append(item)
            except Exception as e:
                self.logger.error(f"解析物品数据时出错: {e}")
        
        self.logger.info(f"成功解析 {len(items)} 个物品")
        return items
    
    def _interpret_single(self, data: Dict[str, Any], file_path: str = "") -> Optional[InventoryItemModel]:
        """解析单个物品数据"""
        try:
            # 基础数据提取
            title = data.get("title", "").strip()
            description = data.get("description", "").strip()
            obtain_method = data.get("obtain_method", [])
            exchange_requirements = data.get("exchange_requirements", [])
            usage = data.get("usage", "").strip()
            
            # 确保列表类型
            if not isinstance(obtain_method, list):
                obtain_method = [str(obtain_method)] if obtain_method else []
            
            # exchange_requirements 可能是字符串列表或字典列表，保持原始格式
            if not isinstance(exchange_requirements, list):
                exchange_requirements = [exchange_requirements] if exchange_requirements else []
            
            # 创建物品对象
            item = InventoryItemModel(
                title=title,
                description=description,
                obtain_method=obtain_method,
                exchange_requirements=exchange_requirements,
                usage=usage
            )
            
            # 从文件路径设置ID
            if file_path:
                item.set_id_from_filename(file_path)
            elif "_file_path" in data:
                item.set_id_from_filename(data["_file_path"])
            elif "_file_id" in data:
                file_id = str(data["_file_id"])
                if file_id.isdigit():
                    item.id = file_id
                else:
                    self.logger.warning(f"非数字文件ID，跳过: {file_id}")
                    return None
            
            return item
            
        except Exception as e:
            self.logger.error(f"解析单个物品数据时出错: {e}")
            return None