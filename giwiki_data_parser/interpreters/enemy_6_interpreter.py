import logging
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.enemy_6 import Enemy
from giwiki_data_parser.services.dataloader import DataLoader

class EnemyInterpreter:
    """敌人解释器"""
    
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)
    
    def interpret(self, data: Dict[str, Any]) -> Optional[Enemy]:
        """解析单个敌人数据 - 公共接口"""
        return self._interpret_single(data)
    
    def interpret_all(self) -> List[Enemy]:
        """解析所有敌人数据"""
        enemies = []
        raw_data_iterator = self.loader.get_enemies()
        
        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                enemy = self._interpret_single(data, file_path)
                if enemy:
                    enemies.append(enemy)
            except Exception as e:
                self.logger.error(f"解析敌人数据时出错: {e}")
        
        self.logger.info(f"成功解析 {len(enemies)} 个敌人")
        return enemies
    
    def _interpret_single(self, data: Dict[str, Any], file_path: str = "") -> Optional[Enemy]:
        """解析单个敌人数据"""
        try:
            # 处理攻击方式
            attack_methods = []
            raw_attack_methods = data.get("attack_methods", [])
            
            for method in raw_attack_methods:
                if isinstance(method, str):
                    # 如果是逗号分隔的字符串，进行分割
                    if '、' in method:
                        attack_methods.extend([m.strip() for m in method.split('、')])
                    else:
                        attack_methods.append(method.strip())
                elif isinstance(method, list):
                    attack_methods.extend(method)
            
            # 创建敌人对象
            enemy = Enemy(
                name=data.get("title", ""),
                element=data.get("element"),
                attack_methods=attack_methods,
                background_story=data.get("background_story")
            )
            
            # 从文件路径设置ID
            if file_path:
                enemy.set_id_from_filename(file_path)
            elif "_file_path" in data:
                enemy.set_id_from_filename(data["_file_path"])
            elif "_file_id" in data:
                file_id = str(data["_file_id"])
                if file_id.isdigit():
                    enemy.id = file_id
                else:
                    self.logger.warning(f"非数字文件ID，跳过: {file_id}")
                    return None
            
            return enemy
            
        except Exception as e:
            self.logger.error(f"解析单个敌人数据时出错: {e}")
            return None