from typing import Dict, Any, Optional

from hsr_data_parser.services.loader_service import DataLoader

class TextJoinService:
    """
    Handles the logic for resolving {TEXTJOIN#...} placeholders by linking
    TextJoinConfig.json with TextJoinItem.json.
    """
    def __init__(self, loader: DataLoader):
        self._loader = loader
        self._text_join_config: Dict[int, Any] = {}
        self._text_join_items: Dict[int, int] = {}
        self._prepare_data()

    def _prepare_data(self):
        """Pre-loads and caches data from TextJoinConfig.json and TextJoinItem.json."""
        # Load TextJoinConfig.json to get the DefaultItem ID
        config_data = self._loader.get_json("TextJoinConfig.json")
        if config_data:
            for item in config_data:
                if "TextJoinID" in item:
                    self._text_join_config[item["TextJoinID"]] = item
        
        # Load TextJoinItem.json to map the Item ID to the final text hash
        item_data = self._loader.get_json("TextJoinItem.json")
        if item_data:
            for item in item_data:
                item_id = item.get("TextJoinItemID")
                if item_id is None:
                    continue

                # Try to get the hash. If it's missing or the parent key is missing, this will be None.
                text_hash = item.get("TextJoinText", {}).get("Hash")

                if text_hash:
                    # If we have a valid hash, store it.
                    self._text_join_items[item_id] = text_hash
                else:
                    # If there's no hash (key missing or value empty), it's a Player placeholder.
                    self._text_join_items[item_id] = -1

    def get_text_hash_by_join_id(self, join_id: int) -> Optional[int]:
        """
        Gets the final text map hash for a given TextJoin ID by following the chain:
        TextJoinID -> DefaultItemID -> TextHash
        """
        # Step 1: Find the config for the join_id to get the DefaultItem
        config = self._text_join_config.get(join_id)
        if not config:
            return None
        
        # Step 2: Get the default item ID from the config
        default_item_id = config.get("DefaultItem")
        if default_item_id is None:
            return None
            
        # Step 3: Use the default item ID to get the final text hash from the items map
        return self._text_join_items.get(default_item_id)
