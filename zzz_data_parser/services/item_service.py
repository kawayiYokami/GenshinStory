from typing import List, Dict, Optional
from ..interpreters.item_interpreter import ItemInterpreter
from ..models.item import Item


class ItemService:
    """
    Service layer for accessing item data.
    This service handles parsing and caching of item data.
    """

    _instance: Optional['ItemService'] = None
    _items: Optional[List[Item]] = None
    _item_map: Optional[Dict[int, Item]] = None

    def __new__(cls) -> 'ItemService':
        """
        Singleton pattern implementation. Ensures only one instance of the service exists.
        """
        if cls._instance is None:
            cls._instance = super(ItemService, cls).__new__(cls)
        return cls._instance

    def _load_data(self) -> None:
        """
        Loads and parses item data using the ItemInterpreter.
        This method initializes the internal cache.
        """
        if self._items is None:
            interpreter = ItemInterpreter()
            self._items = interpreter.parse()
            # Create a map for quick ID-based lookups
            self._item_map = {item.id: item for item in self._items}

    def get_item_by_id(self, item_id: int) -> Optional[Item]:
        """
        Retrieves an item by its unique ID.

        Args:
            item_id: The ID of the item to retrieve.

        Returns:
            The Item object if found, otherwise None.
        """
        self._load_data()
        return self._item_map.get(item_id)

    def list_item_ids(self) -> List[int]:
        """
        Retrieves a list of all available item IDs.

        Returns:
            A list of item IDs.
        """
        self._load_data()
        return list(self._item_map.keys()) if self._item_map else []