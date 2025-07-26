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

    def _prepare_data(self, index_context: Optional[Any] = None):
        """一次性加载所有需要的数据并进行预处理。"""
        if self._is_prepared:
            return
        
        logging.info("加载材料相关数据 (Material)...")
        self._text_map = self.loader.get_json("TextMap/TextMapCHS.json", index_context=index_context)
        self._material_configs = {item['id']: item for item in self.loader.get_json("ExcelBinOutput/MaterialExcelConfigData.json", index_context=index_context)}
        
        # Build a mapping from Material ID to Codex ID for books
        books_codex_data = self.loader.get_json("ExcelBinOutput/BooksCodexExcelConfigData.json", index_context=index_context)
        for book_entry in books_codex_data:
            if book_entry.get("materialId"):
                self._codex_data[book_entry["materialId"]] = book_entry["id"]
        
        # Load wing stories from Readable text files
        for relative_path in self.loader.get_all_file_paths_in_folder("Readable/CHS", "Wings"):
            try:
                # Extract ID from filename like "Wings140001.txt"
                match = re.search(r"Wings(\d+)", relative_path)
                if match:
                    material_id = int(match.group(1))
                    # get_all_file_paths_in_folder now returns relative paths directly
                    self._wing_stories[material_id] = self.loader.get_text_file(relative_path)
            except Exception as e:
                logging.warning(f"无法解析风之翼故事文件 {relative_path}: {e}")

        self._is_prepared = True
        logging.info("材料相关数据加载完成。")

    def _is_material_invalid(self, config: Dict[str, Any]) -> (bool, str):
        """检查一个材料是否因为是测试或废弃物品而被跳过。"""
        name = self._get_text(config.get("nameTextMapHash"))
        description = self._get_text(config.get("descTextMapHash"))

        # 规则1: 描述文本检查 (统一为不区分大小写)
        desc_invalid_keywords = ["此道具废弃", "测试道具", "废弃", "测试礼包", "阅读物测试", "（测试）", "test"]
        description_lower = description.lower()
        for keyword in desc_invalid_keywords:
            if keyword.lower() in description_lower:
                return True, f"Description contains invalid keyword: '{keyword}'"
        
        # 规则2: 标题文本检查
        title_invalid_keywords = ["测试包", "（测试）", "测试礼包", "测试道具", "测试用", "阅读物测试", "测试随机宝箱", "测试固定宝箱", "test"]
        name_lower = name.lower()
        for keyword in title_invalid_keywords:
            if keyword.lower() in name_lower:
                return True, f"Name contains invalid keyword: '{keyword}'"
        
        return False, ""

    def get_all_material_ids(self) -> List[int]:
        """获取所有可解析的材料ID列表。"""
        self._prepare_data()
        valid_ids = []
        for m_id, config in self._material_configs.items():
            is_invalid, _ = self._is_material_invalid(config)
            if not is_invalid:
                valid_ids.append(m_id)
        return valid_ids

    def get_raw_data(self, material_id: int) -> Optional[Dict[str, Any]]:
        """获取单个材料的原始配置数据。"""
        self._prepare_data()
        return self._material_configs.get(material_id)

    def interpret(self, material_id: int, index_context: Optional[Any] = None) -> Optional[Material]:
        """解析单个材料的完整信息。"""
        self._prepare_data(index_context=index_context)

        material_config = self._material_configs.get(material_id)
        if not material_config:
            return None

        is_invalid, reason = self._is_material_invalid(material_config)
        if is_invalid:
            logging.debug(f"Skipping material {material_id}. Reason: {reason}")
            return None

        name = self._get_text(material_config.get("nameTextMapHash"))
        
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