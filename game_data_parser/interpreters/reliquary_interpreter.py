import logging
import os
import re
from typing import Dict, Any, List, Optional

from ..dataloader import DataLoader
from ..models import Reliquary, ReliquarySet
from ..utils.text_transformer import transform_text

class ReliquaryInterpreter:
    """
    负责将原始的圣遗物相关数据解析成结构化的 ReliquarySet 和 Reliquary 对象。
    """
    # 将 EQUIP_TYPE 枚举值映射到中文名称
    POS_NAME_MAP = {
        "EQUIP_BRACER": "生之花",
        "EQUIP_NECKLACE": "死之羽",
        "EQUIP_SHOES": "时之沙",
        "EQUIP_RING": "空之杯",
        "EQUIP_DRESS": "理之冠",
    }

    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
        self._text_map: Dict[str, str] = {}
        
        # Pre-processed data caches
        self._reliquary_configs: Dict[int, Dict[str, Any]] = {}
        self._reliquary_set_configs: Dict[int, Dict[str, Any]] = {}
        self._equip_affix_configs: Dict[int, Dict[str, Any]] = {}
        self._relic_stories: Dict[str, str] = {} # Key: "SetID_Position", e.g., "15001_4"
        
        self._is_prepared = False

    def _get_text(self, text_map_hash: Any, default: str = "") -> str:
        """根据哈希值安全地获取原始文本。"""
        text, _ = transform_text(self._text_map.get(str(text_map_hash), default))
        return text

    def _prepare_data(self):
        """一次性加载所有需要的数据并进行预处理。"""
        if self._is_prepared:
            return
        
        logging.info("加载圣遗物相关数据 (Reliquary, Set, Affix)...")
        self._text_map = self.loader.get_json("TextMap/TextMapCHS.json")

        self._reliquary_configs = {item['id']: item for item in self.loader.get_json("ExcelBinOutput/ReliquaryExcelConfigData.json")}
        self._reliquary_set_configs = {item['setId']: item for item in self.loader.get_json("ExcelBinOutput/ReliquarySetExcelConfigData.json")}
        self._equip_affix_configs = {item['id']: item for item in self.loader.get_json("ExcelBinOutput/EquipAffixExcelConfigData.json") if 'id' in item}

        # Build the definitive map for set names from DisplayItemExcelConfigData
        self._set_id_to_name_hash: Dict[int, int] = {}
        display_items = self.loader.get_json("ExcelBinOutput/DisplayItemExcelConfigData.json")
        for item in display_items:
            if item.get("displayType") == "RELIQUARY_ITEM":
                set_id = item.get("param")
                name_hash = item.get("nameTextMapHash")
                if set_id and name_hash:
                    self._set_id_to_name_hash[set_id] = name_hash

        # Load all relic stories from Readable text files
        for relative_path in self.loader.get_all_file_paths_in_folder("Readable/CHS", "Relic"):
            try:
                # Filename is like "Relic15001_4.txt"
                file_name = self.loader.get_file_name(relative_path, with_extension=False)
                match = re.search(r"Relic(\d+_\d+)", file_name)
                if match:
                    story_key = match.group(1) # Extracts "15001_4"
                    # get_all_file_paths_in_folder now returns relative paths directly
                    self._relic_stories[story_key] = self.loader.get_text_file(relative_path)
            except Exception as e:
                logging.warning(f"无法解析圣遗物故事文件 {relative_path}: {e}")

        self._is_prepared = True
        logging.info("圣遗物相关数据加载完成。")

    def get_all_set_ids(self) -> List[int]:
        """获取所有圣遗物套装的ID列表。"""
        self._prepare_data()
        return list(self._reliquary_set_configs.keys())

    def get_all_relic_ids(self) -> List[int]:
        """获取所有单个圣遗物部件的ID列表。"""
        self._prepare_data()
        return list(self._reliquary_configs.keys())

    def get_set_raw_data(self, set_id: int) -> Optional[Dict[str, Any]]:
        """获取圣遗物套装的原始配置数据。"""
        self._prepare_data()
        return self._reliquary_set_configs.get(set_id)

    def get_relic_raw_data(self, relic_id: int) -> Optional[Dict[str, Any]]:
        """获取单个圣遗物部件的原始配置数据。"""
        self._prepare_data()
        return self._reliquary_configs.get(relic_id)

    def interpret_single(self, relic_id: int) -> Optional[Reliquary]:
        """解析单个圣遗物部件的完整信息。"""
        self._prepare_data()
        relic_config = self._reliquary_configs.get(relic_id)
        if not relic_config:
            return None
            
        set_id = relic_config.get("setId")
        set_info = self.interpret(set_id) if set_id else None
        set_name = set_info.name if set_info else ""

        # Find the matching relic in the full set to get its pos_index
        pos_index = -1
        if set_info:
            for relic in set_info.reliquaries:
                if relic.id == relic_id:
                    pos_index = relic.pos_index
                    break
        
        story_key = f"{set_id}_{pos_index}"

        return Reliquary(
            id=relic_id,
            name=self._get_text(relic_config.get("nameTextMapHash")),
            description=self._get_text(relic_config.get("descTextMapHash")),
            story=self._relic_stories.get(story_key, ""),
            set_id=set_id,
            set_name=set_name,
            pos_name=self._get_text(relic_config.get("equipType")),
            pos_index=pos_index,
        )

    def interpret(self, set_id: int) -> Optional[ReliquarySet]:
        """解析单个圣遗物套装的完整信息，包括其所有部件。"""
        self._prepare_data()

        set_config = self._reliquary_set_configs.get(set_id)
        if not set_config:
            return None
        
        # --- Get Set Name from the new definitive mapping ---
        set_name_hash = self._set_id_to_name_hash.get(set_id)
        set_name = self._get_text(set_name_hash) if set_name_hash else ""

        # --- Get Set Effects from EquipAffix (this part remains the same) ---
        effect_2_piece = ""
        effect_4_piece = ""
        affix_id = set_config.get("EquipAffixId")
        if affix_id and affix_id in self._equip_affix_configs:
            affix_config = self._equip_affix_configs[affix_id]
            description = self._get_text(affix_config.get("descTextMapHash"))
            parts = description.split("\\n")
            if len(parts) >= 2:
                effect_2_piece = parts[0]
                effect_4_piece = parts[1]
            elif len(parts) == 1:
                effect_2_piece = parts[0]

        reliquary_set = ReliquarySet(
            id=set_id,
            name=set_name,
            effect_2_piece=effect_2_piece,
            effect_4_piece=effect_4_piece,
        )

        # --- Interpret Individual Reliquaries ---
        # Using enumerate to get a reliable position index (1-based)
        for i, relic_id in enumerate(set_config.get("containsList", [])):
            pos_index = i + 1
            relic_config = self._reliquary_configs.get(relic_id)
            if not relic_config:
                continue
            
            story_key = f"{set_id}_{pos_index}"
            
            equip_type_str = relic_config.get("equipType", "")
            pos_name = self.POS_NAME_MAP.get(equip_type_str, "") # 从映射中获取中文名

            reliquary = Reliquary(
                id=relic_id,
                name=self._get_text(relic_config.get("nameTextMapHash")),
                description=self._get_text(relic_config.get("descTextMapHash")),
                story=self._relic_stories.get(story_key, ""),
                set_id=set_id,
                set_name=reliquary_set.name,
                pos_name=pos_name,
                pos_index=pos_index
            )
            reliquary_set.reliquaries.append(reliquary)
            
        # Sort reliquaries by their position index for consistent order
        reliquary_set.reliquaries.sort(key=lambda r: r.pos_index)

        # The fallback logic is no longer needed as DisplayItem provides the definitive name.
        return reliquary_set