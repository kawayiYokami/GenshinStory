import json
import os
import logging
from typing import Dict, Any, List, Optional

class GameDataLoader:
    """Loads all necessary game data files from the turnbasedgamedata directory."""
    def __init__(self, base_path: str = 'turnbasedgamedata'):
        self.base_path = base_path
        self.excel_path = os.path.join(self.base_path, 'ExcelOutput')
        self.textmap_path = os.path.join(self.base_path, 'TextMap')
        self.patch_path = os.path.join(self.base_path, 'Patch', 'TextMap')

    def _read_json_file(self, file_path: str) -> Optional[Any]:
        if not os.path.exists(file_path):
            logging.warning(f"File not found: {file_path}")
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to read or parse {file_path}: {e}")
            return None

    def load_text_map(self) -> Dict[str, str]:
        path = os.path.join(self.textmap_path, 'TextMapCHS.json')
        return self._read_json_file(path) or {}

    def load_patch_text_map(self) -> Dict[str, str]:
        path = os.path.join(self.patch_path, 'TextMapCHS.json')
        return self._read_json_file(path) or {}

    def get_messages(self) -> List[Dict[str, Any]]:
        return self._read_json_file(os.path.join(self.excel_path, 'MessageGroupConfig.json')) or []

    def get_message_contacts(self) -> List[Dict[str, Any]]:
        return self._read_json_file(os.path.join(self.excel_path, 'MessageContactsConfig.json')) or []

    def get_message_sections(self) -> List[Dict[str, Any]]:
        return self._read_json_file(os.path.join(self.excel_path, 'MessageSectionConfig.json')) or []

    def get_message_items(self) -> List[Dict[str, Any]]:
        return self._read_json_file(os.path.join(self.excel_path, 'MessageItemConfig.json')) or []

    def get_rogue_magic_scepters(self) -> List[Dict[str, Any]]:
        """加载奇物 (RogueMagicScepter) 数据。"""
        return self._read_json_file(os.path.join(self.excel_path, 'RogueMagicScepterDisplay.json')) or []

    def get_rogue_miracles(self) -> List[Dict[str, Any]]:
        """加载奇物主配置数据。"""
        return self._read_json_file(os.path.join(self.excel_path, 'RogueMiracle.json')) or []

    def get_rogue_miracle_displays(self) -> List[Dict[str, Any]]:
        """加载奇物显示数据。"""
        return self._read_json_file(os.path.join(self.excel_path, 'RogueMiracleDisplay.json')) or []