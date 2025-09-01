from typing import List, Dict, Optional
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