from typing import Any, Dict, List, Optional
from dataclasses import asdict

from ..dataloader import DataLoader
from ..interpreters.weapon_interpreter import WeaponInterpreter
from ..formatters.weapon_formatter import WeaponFormatter
from ..models import Weapon


class WeaponService:
    """
    提供所有与“武器(Weapon)”领域相关的查询和操作。
    """
    def __init__(self, loader: DataLoader):
        self.interpreter = WeaponInterpreter(loader)
        self.formatter = WeaponFormatter()

    def list_weapons(self) -> List[Dict[str, Any]]:
        """
        获取所有武器的简明列表 (id, name)。
        """
        return self.search_weapons()

    def search_weapons(self, type: Optional[str] = None, rarity: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取所有武器的简明列表，支持按类型和稀有度筛选。
        """
        all_weapons = []
        all_weapon_ids = self.interpreter.get_all_weapon_ids()

        for weapon_id in all_weapon_ids:
            # For filtering, we need the full object
            weapon = self.interpreter.interpret(weapon_id)
            if not weapon:
                continue

            # --- Filtering Logic ---
            if rarity is not None and weapon.rank_level != rarity:
                continue
            if type is not None and weapon.type_name != type:
                continue

            all_weapons.append({
                "id": weapon.id,
                "name": weapon.name
            })

        return all_weapons

    def get_weapon_by_id(self, item_id: int, index_context: Optional[Any] = None) -> Optional[Weapon]:
        """获取单个武器的完整信息。"""
        return self.interpreter.interpret(item_id, index_context=index_context)

    def get_weapon_as_json(self, item_id: int, index_context: Optional[Any] = None) -> Optional[Dict]:
        """根据ID获取单个武器的详细信息，并以JSON兼容的字典格式返回。"""
        weapon = self.get_weapon_by_id(item_id, index_context=index_context)
        if not weapon:
            return None
        return asdict(weapon)

    def get_weapon_as_markdown(self, item_id: int) -> Optional[str]:
        """获取单个武器的格式化Markdown文档。"""
        weapon = self.get_weapon_by_id(item_id)
        if not weapon:
            return None
        return self.formatter.format_weapon(weapon)

    def _get_all_weapons_full(self) -> List[Weapon]:
        """获取所有武器的完整对象列表。"""
        all_weapons = []
        all_ids = self.interpreter.get_all_weapon_ids()
        for weapon_id in all_ids:
            weapon = self.interpreter.interpret(weapon_id)
            if weapon:
                all_weapons.append(weapon)
        return all_weapons

    def get_tree(self) -> List[Dict[str, Any]]:
        """获取武器的树状结构图 (武器类型 -> 武器)。"""
        all_weapons = self._get_all_weapons_full()
        
        type_map: Dict[str, List[Weapon]] = {}
        
        for weapon in all_weapons:
            # 关键修复：确保武器有有效的、非空的名称，再将其添加到树中
            if not weapon.name or not weapon.name.strip():
                continue

            w_type = weapon.type_name
            if w_type not in type_map:
                type_map[w_type] = []
            type_map[w_type].append(weapon)
            
        result_tree = []
        for w_type, weapons in sorted(type_map.items()):
            type_node = {
                "id": w_type,
                "title": w_type,
                "children": sorted(
                    [{"id": w.id, "title": w.name} for w in weapons],
                    key=lambda x: x['id']
                )
            }
            result_tree.append(type_node)
            
        return result_tree
