from typing import Any, Dict, List, Optional
from dataclasses import asdict
import json

from ..dataloader import DataLoader
from ..interpreters.character_interpreter import CharacterInterpreter
from ..formatters.character_formatter import CharacterFormatter
from ..models.character import Character

class CharacterService:
    """
    提供所有与“角色(Character)”领域相关的查询和操作。
    """
    def __init__(self, loader: DataLoader):
        self.interpreter = CharacterInterpreter(loader)
        self.formatter = CharacterFormatter()

    def list_characters(self) -> List[Character]:
        """
        获取所有可玩的角色信息。
        """
        all_characters = []
        all_ids = self.interpreter.get_all_character_ids()
        for character_id in all_ids:
            character = self.interpreter.interpret(character_id)
            if character and character.nation:
                all_characters.append(character)
        return all_characters

    def get_character_by_id(self, character_id: int, index_context: Optional[Any] = None) -> Optional[Character]:
        """
        根据ID获取单个角色的详细信息。
        """
        return self.interpreter.interpret(character_id, index_context=index_context)

    def get_character_as_json(self, character_id: int, index_context: Optional[Any] = None) -> Optional[Dict]:
        """
        根据ID获取单个角色的详细信息，并以JSON兼容的字典格式返回。
        """
        character = self.get_character_by_id(character_id, index_context=index_context)
        if not character:
            return None
        # 使用pydantic的model_dump方法来获取一个可序列化的字典
        return asdict(character)

    def get_character_as_markdown(self, character_id: int) -> str:
        """
        根据ID获取单个角色的详细信息，并以Markdown格式返回。
        """
        character = self.get_character_by_id(character_id)
        if not character:
            return f"Error: Could not find character with ID {character_id}."
        return self.formatter.format(character)

    def get_tree(self) -> List[Dict[str, Any]]:
        """获取角色的树状结构图 (国家 -> 角色)。"""
        all_characters = self.list_characters()
        
        nation_map: Dict[str, List[Character]] = {}
        
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