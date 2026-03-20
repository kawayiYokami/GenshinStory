import logging
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.weapon_5 import Weapon
from giwiki_data_parser.services.dataloader import DataLoader

class WeaponInterpreter:
    """武器解释器"""
    
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)
    
    def interpret(self, data: Dict[str, Any]) -> Optional[Weapon]:
        """解析单个武器数据 - 公共接口"""
        return self._interpret_single(data)
    
    def interpret_all(self) -> List[Weapon]:
        """解析所有武器数据"""
        weapons = []
        raw_data_iterator = self.loader.get_weapons()
        
        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                weapon = self._interpret_single(data, file_path)
                if weapon:
                    weapons.append(weapon)
            except Exception as e:
                self.logger.error(f"解析武器数据时出错: {e}")
        
        self.logger.info(f"成功解析 {len(weapons)} 个武器")
        return weapons
    
    def _interpret_single(self, data: Dict[str, Any], file_path: str = "") -> Optional[Weapon]:
        """解析单个武器数据"""
        try:
            # 处理武器类型
            weapon_type = data.get("type")
            if weapon_type == "":
                weapon_type = None
            
            # 创建武器对象
            weapon = Weapon(
                name=data.get("title", ""),
                description=data.get("description"),
                rarity=data.get("rarity"),
                weapon_type=weapon_type,
                story=data.get("story")
            )
            
            # 从文件路径设置ID
            if file_path:
                weapon.set_id_from_filename(file_path)
            elif "_file_path" in data:
                weapon.set_id_from_filename(data["_file_path"])
            elif "_file_id" in data:
                file_id = str(data["_file_id"])
                if file_id.isdigit():
                    weapon.id = file_id
                else:
                    self.logger.warning(f"非数字文件ID，跳过: {file_id}")
                    return None
            
            return weapon
            
        except Exception as e:
            self.logger.error(f"解析单个武器数据时出错: {e}")
            return None