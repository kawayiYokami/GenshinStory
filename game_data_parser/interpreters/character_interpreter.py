import logging
from typing import Dict, Any, List, Optional

from ..dataloader import DataLoader
from ..models.character import Character, CVs, Story, VoiceLine
from ..utils.text_transformer import transform_text

class CharacterInterpreter:
    """
    负责将原始的角色相关数据解析成结构化的 Character 对象。
    """
    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
        self._text_map: Dict[str, str] = {}
        
        # Pre-processed data caches
        self._character_configs: Dict[int, Dict[str, Any]] = {}
        self._fetter_infos: Dict[int, Dict[str, Any]] = {}
        self._fetters: Dict[int, List[Dict[str, Any]]] = {}
        self._fetter_stories: Dict[int, List[Dict[str, Any]]] = {}
        
        self._is_prepared = False

    def _get_text(self, text_map_hash: Any, default: str = "", index_context: Optional[Any] = None) -> str:
        """根据哈希值安全地获取原始文本。"""
        text_value = self._text_map.get(str(text_map_hash), default)
        
        if index_context and text_value:
            pass

        text, _ = transform_text(text_value)
        return text

    def _prepare_data(self, index_context: Optional[Any] = None):
        """一次性加载所有需要的数据并进行预处理。"""
        if self._is_prepared:
            return
        
        logging.info("加载角色相关数据 (Avatar, Fetter)...")
        self._text_map = self.loader.get_json("TextMap/TextMapCHS.json", index_context=index_context)

        # Load and map all configs by avatar ID for quick access
        # NOTE: The source file name 'AvatarExcelConfigData.json' and the field 'avatarId' are kept as is,
        # because they represent the raw data structure. We abstract them into 'Character' in this layer.
        avatar_config_list = self.loader.get_json("ExcelBinOutput/AvatarExcelConfigData.json", index_context=index_context)
        self._character_configs = {item['id']: item for item in avatar_config_list if 'id' in item}

        fetter_info_list = self.loader.get_json("ExcelBinOutput/FetterInfoExcelConfigData.json", index_context=index_context)
        self._fetter_infos = {item['avatarId']: item for item in fetter_info_list if 'avatarId' in item}

        fetters_list = self.loader.get_json("ExcelBinOutput/FettersExcelConfigData.json", index_context=index_context)
        for item in fetters_list:
            avatar_id = item.get('avatarId')
            if avatar_id not in self._fetters:
                self._fetters[avatar_id] = []
            self._fetters[avatar_id].append(item)

        fetter_story_list = self.loader.get_json("ExcelBinOutput/FetterStoryExcelConfigData.json", index_context=index_context)
        for item in fetter_story_list:
            avatar_id = item.get('avatarId')
            if avatar_id not in self._fetter_stories:
                self._fetter_stories[avatar_id] = []
            self._fetter_stories[avatar_id].append(item)

        self._is_prepared = True
        logging.info("角色相关数据加载完成。")

    def get_all_character_ids(self) -> List[int]:
        """获取所有可解析的角色ID列表。"""
        self._prepare_data()
        # Filter for playable characters (e.g., exclude test avatars)
        return [
            character_id for character_id, config in self._character_configs.items()
            if len(self._get_text(config.get("nameTextMapHash"))) > 0 and config.get("skillDepotId", 0) > 1000
        ]

    def get_raw_data(self, character_id: int) -> Optional[Dict[str, Any]]:
        """获取单个角色的原始配置数据。"""
        self._prepare_data()
        return self._character_configs.get(character_id)

    def interpret(self, character_id: int, index_context: Optional[Any] = None) -> Optional[Character]:
        """解析单个角色的完整信息。"""
        self._prepare_data(index_context=index_context)

        character_config = self._character_configs.get(character_id)
        if not character_config:
            return None

        # --- Basic Info ---
        name = self._get_text(character_config.get("nameTextMapHash"))
        if not name: # Skip non-playable characters
            return None
        
        character = Character(
            id=character_id,
            name=name,
            description=self._get_text(character_config.get("descTextMapHash")),
            skill_depot_id=character_config.get("skillDepotId")
        )

        # --- Fetter Info ---
        fetter_info = self._fetter_infos.get(character_id, {})
        if fetter_info:
            character.title = self._get_text(fetter_info.get("avatarTitleTextMapHash"))
            
            # Combine birthday month and day
            birth_month = fetter_info.get('infoBirthMonth')
            birth_day = fetter_info.get('infoBirthDay')
            if birth_month and birth_day:
                character.birthday = f"{birth_month}-{birth_day}"

            character.constellation = self._get_text(fetter_info.get("avatarConstellationBeforTextMapHash"))
            character.nation = self._get_text(fetter_info.get("avatarNativeTextMapHash"))
            character.vision = self._get_text(fetter_info.get("visionBeforTextMapHash")) # Element
            
            character.cvs = CVs(
                chinese=self._get_text(fetter_info.get("cvChineseTextMapHash")),
                japanese=self._get_text(fetter_info.get("cvJapaneseTextMapHash")),
                english=self._get_text(fetter_info.get("cvEnglishTextMapHash")),
                korean=self._get_text(fetter_info.get("cvKoreanTextMapHash")),
            )

        # --- Fetter Stories ---
        if character_id in self._fetter_stories:
            for story_data in self._fetter_stories[character_id]:
                character.stories.append(Story(
                    title=self._get_text(story_data.get("storyTitleTextMapHash")),
                    text=self._get_text(story_data.get("storyContextTextMapHash"))
                ))

        # --- Fetter Voice Lines ---
        if character_id in self._fetters:
            for fetter_data in self._fetters[character_id]:
                character.voice_lines.append(VoiceLine(
                    title=self._get_text(fetter_data.get("voiceTitleTextMapHash")),
                    text=self._get_text(fetter_data.get("voiceFileTextTextMapHash"))
                ))

        return character