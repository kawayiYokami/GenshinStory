import logging
from typing import Dict, Optional

# Assuming the DataLoader class from the original hsr_data_parser is available
# or its necessary parts are copied over.
from hsrwiki_data_parser.services.game_data_loader import GameDataLoader

class TextMapService:
    def __init__(self, loader: GameDataLoader):
        self._text_map: Dict[str, str] = loader.load_text_map()
        self._patch_text_map: Dict[str, str] = loader.load_patch_text_map()
        logging.info(f"TextMapService initialized with {len(self._text_map)} entries.")

    def get_text(self, text_hash: str, default: str = "") -> str:
        """获取文本，优先从补丁中查找，然后是主文本映射。"""
        if not isinstance(text_hash, (str, int)):
            return default
        text_hash_str = str(text_hash)
        return self._patch_text_map.get(text_hash_str, self._text_map.get(text_hash_str, default))

    def __getitem__(self, key: str) -> str:
        return self.get_text(key)

    def __contains__(self, key: str) -> bool:
        return str(key) in self._text_map or str(key) in self._patch_text_map
