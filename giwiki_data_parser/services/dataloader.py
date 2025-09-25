import os
import json
import logging
from typing import Iterator, Dict, Any

class DataLoader:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.logger = logging.getLogger(__name__)
    
    def _load_json_files(self, category_path: str) -> Iterator[Dict[str, Any]]:
        """从指定类别目录加载所有JSON文件"""
        if not os.path.exists(category_path):
            self.logger.warning(f"Category path does not exist: {category_path}")
            return
        
        for filename in os.listdir(category_path):
            if filename.endswith('.json'):
                file_path = os.path.join(category_path, filename)
                file_id = filename[:-5]  # 移除.json后缀
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 添加文件相关信息到数据中
                        data["_file_id"] = file_id
                        data["_file_path"] = file_path
                        yield data
                except Exception as e:
                    self.logger.error(f"Error loading {file_path}: {e}")
    
    def get_characters(self) -> Iterator[Dict[str, Any]]:
        """获取角色数据"""
        category_path = os.path.join(self.base_path, "25_角色")
        return self._load_json_files(category_path)
    
    def get_weapons(self) -> Iterator[Dict[str, Any]]:
        """获取武器数据"""
        category_path = os.path.join(self.base_path, "5_武器")
        return self._load_json_files(category_path)
    
    def get_artifacts(self) -> Iterator[Dict[str, Any]]:
        """获取圣遗物数据"""
        category_path = os.path.join(self.base_path, "218_圣遗物")
        return self._load_json_files(category_path)
    
    def get_enemies(self) -> Iterator[Dict[str, Any]]:
        """获取敌人数据"""
        category_path = os.path.join(self.base_path, "6_敌人")
        return self._load_json_files(category_path)
    
    def get_items(self) -> Iterator[Dict[str, Any]]:
        """获取背包物品数据"""
        category_path = os.path.join(self.base_path, "13_背包")
        return self._load_json_files(category_path)
    
    def get_npcs(self) -> Iterator[Dict[str, Any]]:
        """获取NPC数据"""
        category_path = os.path.join(self.base_path, "20_NPC&商店")
        return self._load_json_files(category_path)
    
    def get_food(self) -> Iterator[Dict[str, Any]]:
        """获取食物数据"""
        category_path = os.path.join(self.base_path, "21_食物")
        return self._load_json_files(category_path)
    
    def get_quests(self) -> Iterator[Dict[str, Any]]:
        """获取任务数据"""
        category_path = os.path.join(self.base_path, "43_任务")
        return self._load_json_files(category_path)
    
    def get_animals(self) -> Iterator[Dict[str, Any]]:
        """获取动物数据"""
        category_path = os.path.join(self.base_path, "49_动物")
        return self._load_json_files(category_path)
    
    def get_domains(self) -> Iterator[Dict[str, Any]]:
        """获取秘境数据"""
        category_path = os.path.join(self.base_path, "54_秘境")
        return self._load_json_files(category_path)
    
    def get_adventurer_guild(self) -> Iterator[Dict[str, Any]]:
        """获取冒险家协会数据"""
        category_path = os.path.join(self.base_path, "55_冒险家协会")
        return self._load_json_files(category_path)
    
    def get_spiral_abyss(self) -> Iterator[Dict[str, Any]]:
        """获取深境螺旋数据"""
        category_path = os.path.join(self.base_path, "65_深境螺旋")
        return self._load_json_files(category_path)
    
    def get_books(self) -> Iterator[Dict[str, Any]]:
        """获取书籍数据"""
        category_path = os.path.join(self.base_path, "68_书籍")
        return self._load_json_files(category_path)
    
    def get_events(self) -> Iterator[Dict[str, Any]]:
        """获取活动数据"""
        category_path = os.path.join(self.base_path, "105_活动")
        return self._load_json_files(category_path)
    
    def get_namecards(self) -> Iterator[Dict[str, Any]]:
        """获取名片数据"""
        category_path = os.path.join(self.base_path, "109_名片")
        return self._load_json_files(category_path)
    
    def get_housing(self) -> Iterator[Dict[str, Any]]:
        """获取洞天数据"""
        category_path = os.path.join(self.base_path, "130_洞天")
        return self._load_json_files(category_path)
    
    def get_outfits(self) -> Iterator[Dict[str, Any]]:
        """获取装扮数据"""
        category_path = os.path.join(self.base_path, "211_装扮")
        return self._load_json_files(category_path)
    
    def get_tutorials(self) -> Iterator[Dict[str, Any]]:
        """获取教程数据"""
        category_path = os.path.join(self.base_path, "227_教程")
        return self._load_json_files(category_path)
    
    def get_avatars(self) -> Iterator[Dict[str, Any]]:
        """获取头像数据"""
        category_path = os.path.join(self.base_path, "244_头像")
        return self._load_json_files(category_path)
    
    def get_imaginarium_theater(self) -> Iterator[Dict[str, Any]]:
        """获取幻想真境剧诗数据"""
        category_path = os.path.join(self.base_path, "249_幻想真境剧诗")
        return self._load_json_files(category_path)
    
    def get_map_text(self) -> Iterator[Dict[str, Any]]:
        """获取地图文本数据"""
        category_path = os.path.join(self.base_path, "251_地图文本")
        return self._load_json_files(category_path)
    
    def get_achievements(self) -> Iterator[Dict[str, Any]]:
        """获取成就数据"""
        category_path = os.path.join(self.base_path, "252_成就")
        return self._load_json_files(category_path)
    
    def get_organizations(self) -> Iterator[Dict[str, Any]]:
        """获取组织数据"""
        category_path = os.path.join(self.base_path, "255_组织")
        return self._load_json_files(category_path)
    
    def get_moonlight_song(self) -> Iterator[Dict[str, Any]]:
        """获取空月之歌数据"""
        category_path = os.path.join(self.base_path, "257_空月之歌")
        return self._load_json_files(category_path)
    
    def get_character_stories(self) -> Iterator[Dict[str, Any]]:
        """获取角色逸闻数据"""
        category_path = os.path.join(self.base_path, "261_角色逸闻")
        return self._load_json_files(category_path)
    
    def load_data_type(self, data_type: str) -> Dict[str, Dict[str, Any]]:
        """加载指定数据类型的所有文件，返回文件ID到数据的映射"""
        category_path = os.path.join(self.base_path, data_type)
        result = {}
        
        if not os.path.exists(category_path):
            self.logger.warning(f"数据目录不存在: {category_path}")
            return result
        
        for filename in os.listdir(category_path):
            if filename.endswith('.json'):
                file_id = filename[:-5]  # 移除.json后缀
                file_path = os.path.join(category_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 添加文件相关信息到数据中
                        data["_file_id"] = file_id
                        data["_file_path"] = file_path
                        result[file_id] = data
                except Exception as e:
                    self.logger.error(f"加载文件 {file_path} 失败: {e}")
        
        return result