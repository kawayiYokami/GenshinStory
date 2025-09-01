import re
from typing import List, Dict, Optional, Any
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

    def get_item_as_markdown(self, item_id: int) -> str:
        """
        Generate a markdown representation of an item.

        Args:
            item_id: The ID of the item.

        Returns:
            A markdown string representing the item.
        """
        item = self.get_item_by_id(item_id)
        if not item:
            return f"# Item {item_id} not found"

        # Simple markdown template
        markdown = f"# {item.name}\n\n"
        markdown += f"**ID**: {item.id}\n\n"
        markdown += "## Description\n\n"
        markdown += f"{item.description}\n\n"
        markdown += "## Story\n\n"
        markdown += f"{item.story}\n\n"

        return markdown

    def get_tree(self) -> List[Dict[str, Any]]:
        """
        Generate a tree structure for items, categorized by type.

        Returns:
            A list of dictionaries representing the tree structure.
        """
        self._load_data()
        if not self._items:
            return []

        # For now, we'll put all items in a single "其他" category
        # In a more advanced implementation, we would categorize by type
        items_list = []
        for item in self._items:
            if self._is_valid_item_name(item.name):
                items_list.append({
                    "id": item.id,
                    "name": item.name,
                    "type": "item"
                })
        # Convert to the required format
        tree = [{
            "name": "其他道具",
            "children": items_list
        }]

        return tree

    def _is_valid_item_name(self, name: str) -> bool:
        """
        Checks if the item name is valid for file creation and display.
        """
        if not name:
            return False
        if name.startswith("unnamed-"):
            return False
        # Check for invalid characters for filenames like #, ?
        if re.search(r"[#?]", name):
            return False
        return True