import logging
import os
import re
from typing import Dict, Any, List, Optional

from ..dataloader import DataLoader
from ..models import Material
from ..utils.text_transformer import transform_text

class MaterialInterpreter:
    """
    负责将原始的材料/道具相关数据解析成结构化的 Material 对象。
    """
    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
        self._text_map: Dict[str, str] = {}
        
        # Pre-processed data caches
        self._material_configs: Dict[int, Dict[str, Any]] = {}
        self._wing_stories: Dict[int, str] = {}
        self._codex_data: Dict[int, int] = {}
        
        self._is_prepared = False

    def _get_text(self, text_map_hash: Any, default: str = "") -> str:
        """根据哈希值安全地获取原始文本。"""
        text, _ = transform_text(self._text_map.get(str(text_map_hash), default))
        return text

    def _prepare_data(self):
        """一次性加载所有需要的数据并进行预处理。"""
        if self._is_prepared:
            return
        
        logging.info("加载材料相关数据 (Material)...")
        self._text_map = self.loader.get_json("TextMap/TextMapCHS.json")
        self._material_configs = {item['id']: item for item in self.loader.get_json("ExcelBinOutput/MaterialExcelConfigData.json")}
        
        # Build a mapping from Material ID to Codex ID for books
        books_codex_data = self.loader.get_json("ExcelBinOutput/BooksCodexExcelConfigData.json")
        for book_entry in books_codex_data:
            if book_entry.get("materialId"):
                self._codex_data[book_entry["materialId"]] = book_entry["id"]
        
        # Load wing stories from Readable text files
        for file_path in self.loader.get_all_file_paths_in_folder("Readable/CHS", "Wings"):
            try:
                # Extract ID from filename like "Wings140001.txt"
                match = re.search(r"Wings(\d+)", file_path)
                if match:
                    material_id = int(match.group(1))
                    # Convert absolute path from get_all_file_paths_in_folder to relative for get_text_file
                    relative_path = os.path.relpath(file_path, self.loader.get_data_root())
                    self._wing_stories[material_id] = self.loader.get_text_file(relative_path)
            except Exception as e:
                logging.warning(f"无法解析风之翼故事文件 {file_path}: {e}")

        self._is_prepared = True
        logging.info("材料相关数据加载完成。")

    def get_all_material_ids(self) -> List[int]:
        """获取所有可解析的材料ID列表。"""
        self._prepare_data()
        # Filter to get non-test/non-dummy materials
        return [
            m_id for m_id, config in self._material_configs.items()
            if self._get_text(config.get("nameTextMapHash")) and "test" not in self._get_text(config.get("nameTextMapHash")).lower()
        ]

    def get_raw_data(self, material_id: int) -> Optional[Dict[str, Any]]:
        """获取单个材料的原始配置数据。"""
        self._prepare_data()
        return self._material_configs.get(material_id)

    def interpret(self, material_id: int) -> Optional[Material]:
        """解析单个材料的完整信息。"""
        self._prepare_data()

        material_config = self._material_configs.get(material_id)
        if not material_config:
            return None

        name = self._get_text(material_config.get("nameTextMapHash"))
        if not name or "test" in name.lower():
            return None

        is_book = False
        codex_id = None
        
        # Check if the material unlocks a codex entry, which is the definition of a book
        item_use = material_config.get("itemUse", [])
        if item_use and item_use[0].get("useOp") == "ITEM_USE_UNLOCK_CODEX":
            use_param = item_use[0].get("useParam")
            if use_param:
                is_book = True
                codex_id = int(use_param[0])

        material = Material(
            id=material_id,
            name=name,
            description=self._get_text(material_config.get("descTextMapHash")),
            material_type_raw=material_config.get("materialType", ""),
            type_name=self._get_text(material_config.get("typeDescTextMapHash")),
            story=self._wing_stories.get(material_id), # Story will only exist for wings
            is_book=is_book,
            codex_id=codex_id,
            set_id=material_config.get("setID")
        )

        return material