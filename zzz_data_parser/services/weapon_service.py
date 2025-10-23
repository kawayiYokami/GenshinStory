from typing import List, Dict, Optional, Any
from ..interpreters.weapon_interpreter import WeaponInterpreter
from ..models.weapon import Weapon


class WeaponService:
    """
    Service layer for accessing weapon data.
    This service handles parsing and caching of weapon data.
    """

    _instance: Optional['WeaponService'] = None
    _weapons: Optional[List[Weapon]] = None
    _weapon_map: Optional[Dict[int, Weapon]] = None

    def __new__(cls) -> 'WeaponService':
        """
        Singleton pattern implementation. Ensures only one instance of the service exists.
        """
        if cls._instance is None:
            cls._instance = super(WeaponService, cls).__new__(cls)
        return cls._instance

    def _load_data(self) -> None:
        """
        Loads and parses weapon data using the WeaponInterpreter.
        This method initializes the internal cache.
        """
        if self._weapons is None:
            interpreter = WeaponInterpreter()
            self._weapons = interpreter.parse()
            # Create a map for quick ID-based lookups
            self._weapon_map = {weapon.id: weapon for weapon in self._weapons}

    def get_weapon_by_id(self, weapon_id: int) -> Optional[Weapon]:
        """
        Retrieves a weapon by its unique ID.

        Args:
            weapon_id: The ID of the weapon to retrieve.

        Returns:
            The Weapon object if found, otherwise None.
        """
        self._load_data()
        return self._weapon_map.get(weapon_id)

    def list_weapon_ids(self) -> List[int]:
        """
        Retrieves a list of all available weapon IDs.

        Returns:
            A list of weapon IDs.
        """
        self._load_data()
        return list(self._weapon_map.keys()) if self._weapon_map else []

    def get_weapon_as_markdown(self, weapon_id: int) -> str:
        """
        Generate a markdown representation of a weapon.

        Args:
            weapon_id: The ID of the weapon.

        Returns:
            A markdown string representing the weapon.
        """
        weapon = self.get_weapon_by_id(weapon_id)
        if not weapon:
            return f"# Weapon {weapon_id} not found"

        # Simple markdown template
        markdown = f"# {weapon.name}\n\n"
        markdown += f"**Model ID**: {weapon.model_id}\n\n"
        markdown += "## Description\n\n"
        markdown += f"{weapon.description}\n\n"
        markdown += "## Story\n\n"
        markdown += f"{weapon.story}\n\n"

        return markdown

    def get_tree(self) -> List[Dict[str, Any]]:
        """
        Generate a tree structure for weapons, categorized by rarity.

        Returns:
            A list of dictionaries representing the tree structure.
        """
        self._load_data()
        if not self._weapons:
            return []

        # Categorize weapons by rarity based on model_id
        rarities: Dict[str, List[Dict[str, Any]]] = {
            "S级武器": [],
            "A级武器": [],
            "其他": []
        }

        for weapon in self._weapons:
            # Determine rarity from model_id
            rarity = "其他"
            if "S_" in weapon.model_id:
                rarity = "S级武器"
            elif "A_" in weapon.model_id:
                rarity = "A级武器"

            # Add weapon to the appropriate rarity category
            rarities[rarity].append({
                "id": weapon.id,
                "name": weapon.name,
                "type": "weapon"
            })

        # Convert to the required format
        tree = []
        for rarity_name, weapons in rarities.items():
            if weapons:  # Only add rarities that have weapons
                tree.append({
                    "name": rarity_name,
                    "children": weapons
                })

        return tree