import logging
import os
import re
from typing import Dict, Any, List, Optional

from ..dataloader import DataLoader
from ..models import Weapon, WeaponSkill
from ..utils.text_transformer import transform_text


WEAPON_TYPE_MAP = {
    "WEAPON_SWORD_ONE_HAND": "单手剑",
    "WEAPON_CLAYMORE": "双手剑",
    "WEAPON_POLE": "长柄武器",
    "WEAPON_BOW": "弓",
    "WEAPON_CATALYST": "法器",
}


class WeaponInterpreter:
    """
    负责将原始的武器相关数据解析成结构化的 Weapon 对象。
    """
    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
        self._text_map: Dict[str, str] = {}
        
        # Pre-processed data caches
        self._weapon_configs: Dict[int, Dict[str, Any]] = {}
        self._equip_affix_configs: Dict[int, List[Dict[str, Any]]] = {} # Maps skill ID to a list of affix levels
        self._weapon_stories: Dict[int, str] = {}

        self._is_prepared = False

    def _get_text(self, text_map_hash: Any, default: str = "") -> str:
        """根据哈希值安全地获取原始文本。"""
        text, _ = transform_text(self._text_map.get(str(text_map_hash), default))
        return text

    def _prepare_data(self):
        """一次性加载所有需要的数据并进行预处理。"""
        if self._is_prepared:
            return
        
        logging.info("加载武器相关数据 (Weapon, Affix)...")
        self._text_map = self.loader.get_json("TextMap/TextMapCHS.json")

        self._weapon_configs = {item['id']: item for item in self.loader.get_json("ExcelBinOutput/WeaponExcelConfigData.json")}
        
        # Group affix configs by their main ID
        affix_list = self.loader.get_json("ExcelBinOutput/EquipAffixExcelConfigData.json")
        for item in affix_list:
            main_id = item.get("id")
            if main_id:
                if main_id not in self._equip_affix_configs:
                    self._equip_affix_configs[main_id] = []
                self._equip_affix_configs[main_id].append(item)
        
        # Sort each affix group by level
        for main_id in self._equip_affix_configs:
            self._equip_affix_configs[main_id].sort(key=lambda x: x.get('level', 0))

        # Load all weapon stories from Readable text files
        for file_path in self.loader.get_all_file_paths_in_folder("Readable/CHS", "Weapon"):
            try:
                # Extract ID from filename like "Weapon11411.txt"
                match = re.search(r"Weapon(\d+)", file_path)
                if match:
                    weapon_id = int(match.group(1))
                    # Convert absolute path from get_all_file_paths_in_folder to relative for get_text_file
                    relative_path = os.path.relpath(file_path, self.loader.get_data_root())
                    self._weapon_stories[weapon_id] = self.loader.get_text_file(relative_path)
            except Exception as e:
                logging.warning(f"无法解析武器故事文件 {file_path}: {e}")

        self._is_prepared = True
        logging.info("武器相关数据加载完成。")

    def get_all_weapon_ids(self) -> List[int]:
        """获取所有可解析的武器ID列表。"""
        self._prepare_data()
        # Simple filter to get non-test weapons
        return [
            w_id for w_id, config in self._weapon_configs.items()
            if config.get("rankLevel", 0) > 1 and self._get_text(config.get("nameTextMapHash"))
        ]

    def get_raw_data(self, weapon_id: int) -> Optional[Dict[str, Any]]:
        """获取单个武器的原始配置数据。"""
        self._prepare_data()
        return self._weapon_configs.get(weapon_id)

    def interpret(self, weapon_id: int) -> Optional[Weapon]:
        """解析单个武器的完整信息。"""
        self._prepare_data()

        weapon_config = self._weapon_configs.get(weapon_id)
        if not weapon_config:
            return None

        weapon = Weapon(
            id=weapon_id,
            name=self._get_text(weapon_config.get("nameTextMapHash")),
            description=self._get_text(weapon_config.get("descTextMapHash")),
            story=self._weapon_stories.get(weapon_id, ""),
            type_name=WEAPON_TYPE_MAP.get(weapon_config.get("weaponType", ""), "未定义武器类型"),
            rank_level=weapon_config.get("rankLevel", 0)
        )

        # --- Interpret Weapon Skill ---
        skill_id = weapon_config.get("skillAffix", [0])[0]
        if skill_id in self._equip_affix_configs:
            affix_group = self._equip_affix_configs[skill_id]
            
            skill_name = ""
            skill_descriptions = []

            if affix_group:
                # Get the name from the first level
                skill_name = self._get_text(affix_group[0].get("nameTextMapHash"))
                
                # Get descriptions from all levels
                for affix_level in affix_group:
                    desc = self._get_text(affix_level.get("descTextMapHash"))
                    # Clean color tags often found in descriptions
                    cleaned_desc = re.sub(r"<color=#[0-9a-fA-F]+>|</color>", "", desc)
                    skill_descriptions.append(cleaned_desc)
            
            weapon.skill = WeaponSkill(
                name=skill_name,
                descriptions=skill_descriptions
            )

        return weapon