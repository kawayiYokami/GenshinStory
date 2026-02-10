import json
import logging
from pathlib import Path
from typing import Iterator, Dict, Any, List

class DataLoader:
    """Loads data from the 'structured_data' directory."""

    def __init__(self, base_path: str = 'structured_data'):
        self.base_path = Path(base_path)
        if not self.base_path.exists() or not self.base_path.is_dir():
            logging.error(f"Base data path does not exist or is not a directory: {self.base_path}")
            raise FileNotFoundError(f"Base data path not found: {self.base_path}")

        # Discover categories by looking at the subdirectories
        self.categories = {p.name for p in self.base_path.iterdir() if p.is_dir()}
        logging.info(f"Discovered categories: {self.categories}")

    def _load_json_files(self, category_dir: str) -> Iterator[Dict[str, Any]]:
        """Loads all JSON files from a specific category directory."""
        path = self.base_path / category_dir
        if not path.is_dir():
            logging.warning(f"Category directory not found: {path}")
            return

        for file_path in path.glob('*.json'):
            try:
                with file_path.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Add id from filename
                    data['id'] = int(file_path.stem)
                    yield data
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Failed to load or parse {file_path}: {e}")

    def get_characters(self) -> Iterator[Dict[str, Any]]:
        return self._load_json_files('18_角色')

    def get_relics(self) -> Iterator[Dict[str, Any]]:
        return self._load_json_files('30_遗器')

    def get_books(self) -> Iterator[Dict[str, Any]]:
        return self._load_json_files('31_阅读物')

    def get_materials(self) -> Iterator[Dict[str, Any]]:
        material_dirs = ['20_养成材料', '53_任务道具', '54_贵重物', '55_其他材料']
        for category in material_dirs:
            yield from self._load_json_files(category)

    def get_quests(self) -> Iterator[Dict[str, Any]]:
        return self._load_json_files('25_任务')

    def get_outfits(self) -> Iterator[Dict[str, Any]]:
        return self._load_json_files('157_装扮')

    def get_rogue_events(self) -> Iterator[Dict[str, Any]]:
        return self._load_json_files('103_模拟宇宙·事件图鉴')

    def get_lightcones(self) -> Iterator[Dict[str, Any]]:
        return self._load_json_files('19_光锥')

