from typing import Dict
from .loader_service import DataLoader

class TextMapService:
    """Service to handle text map resolving."""
    def __init__(self, loader: DataLoader, language_code: str = "CHS"):
        self._text_map: Dict[str, str] = {}
        self._language_code = language_code
        self._loader = loader
        self._load_text_map()

    def _load_text_map(self):
        """Loads the text map from the specified language file."""
        filename = f"TextMap{self._language_code}.json"
        data = self._loader.get_json(filename)
        if data:
            self._text_map = data

    def get(self, text_hash: any, default: str = "") -> str:
        """Gets a string from a text map hash."""
        return self._text_map.get(str(text_hash), default)