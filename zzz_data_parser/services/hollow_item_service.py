from typing import List, Dict, Optional
from ..interpreters.hollow_item_interpreter import HollowItemInterpreter
from ..models.hollow_item import HollowItem


class HollowItemService:
    """
    Service layer for accessing hollow item data.
    This service handles parsing and caching of hollow item data.
    """

    _instance: Optional['HollowItemService'] = None
    _items: Optional[List[HollowItem]] = None
    _item_map: Optional[Dict[int, HollowItem]] = None

    def __new__(cls) -> 'HollowItemService':
        """
        Singleton pattern implementation. Ensures only one instance of the service exists.
        """
        if cls._instance is None:
            cls._instance = super(HollowItemService, cls).__new__(cls)
        return cls._instance

    def _load_data(self) -> None:
        """
        Loads and parses hollow item data using the HollowItemInterpreter.
        This method initializes the internal cache.
        """
        if self._items is None:
            interpreter = HollowItemInterpreter()
            self._items = interpreter.parse()
            # Create a map for quick ID-based lookups
            self._item_map = {item.id: item for item in self._items}

    def get_item_by_id(self, item_id: int) -> Optional[HollowItem]:
        """
        Retrieves a hollow item by its unique ID.

        Args:
            item_id: The ID of the hollow item to retrieve.

        Returns:
            The HollowItem object if found, otherwise None.
        """
        self._load_data()
        return self._item_map.get(item_id)

    def list_item_ids(self) -> List[int]:
        """
        Retrieves a list of all available hollow item IDs.

        Returns:
            A list of hollow item IDs.
        """
        self._load_data()
        return list(self._item_map.keys()) if self._item_map else []