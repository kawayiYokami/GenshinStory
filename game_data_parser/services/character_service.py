from typing import Any, Dict, List, Optional
from dataclasses import asdict
import json

from ..dataloader import DataLoader
from ..interpreters.avatar_interpreter import AvatarInterpreter
from ..formatters.character_formatter import CharacterFormatter
from ..models import Avatar

class CharacterService:
    """
    提供所有与“角色(Character/Avatar)”领域相关的查询和操作。
    """
    def __init__(self, loader: DataLoader):
        self.interpreter = AvatarInterpreter(loader)
        self.formatter = CharacterFormatter()

    def list_characters(self) -> List[Avatar]:
        """
        获取所有可玩的角色信息。
        """
        all_avatars = []
        all_ids = self.interpreter.get_all_avatar_ids()
        for avatar_id in all_ids:
            avatar = self.interpreter.interpret(avatar_id)
            if avatar and avatar.nation:
                all_avatars.append(avatar)
        return all_avatars

    def get_character_by_id(self, avatar_id: int) -> Optional[Avatar]:
        """
        根据ID获取单个角色的详细信息。
        """
        return self.interpreter.interpret(avatar_id)

    def get_character_as_json(self, avatar_id: int) -> Optional[Dict]:
        """
        根据ID获取单个角色的详细信息，并以JSON兼容的字典格式返回。
        """
        avatar = self.get_character_by_id(avatar_id)
        if not avatar:
            return None
        # 使用pydantic的model_dump方法来获取一个可序列化的字典
        return asdict(avatar)

    def get_character_as_markdown(self, avatar_id: int) -> str:
        """
        根据ID获取单个角色的详细信息，并以Markdown格式返回。
        """
        avatar = self.get_character_by_id(avatar_id)
        if not avatar:
            return f"Error: Could not find character with ID {avatar_id}."
        return self.formatter.format(avatar)

    def get_tree(self) -> List[Dict[str, Any]]:
        """获取角色的树状结构图 (国家 -> 角色)。"""
        all_characters = self.list_characters()
        
        nation_map: Dict[str, List[Avatar]] = {}
        
        for char in all_characters:
            nation = char.nation
            if nation not in nation_map:
                nation_map[nation] = []
            nation_map[nation].append(char)
            
        result_tree = []
        for nation, chars in sorted(nation_map.items()):
            nation_node = {
                "id": nation,
                "title": nation,
                "children": sorted(
                    [{"id": c.id, "title": c.name} for c in chars],
                    key=lambda x: x['id']
                )
            }
            result_tree.append(nation_node)
            
        return result_tree