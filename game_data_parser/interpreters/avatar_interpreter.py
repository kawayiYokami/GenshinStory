import logging
from typing import Dict, Any, List, Optional

from ..dataloader import DataLoader
from ..models import Avatar, CVs, Story, VoiceLine
from ..utils.text_transformer import transform_text

class AvatarInterpreter:
    """
    负责将原始的角色相关数据解析成结构化的 Avatar 对象。
    """
    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
        self._text_map: Dict[str, str] = {}
        
        # Pre-processed data caches
        self._avatar_configs: Dict[int, Dict[str, Any]] = {}
        self._fetter_infos: Dict[int, Dict[str, Any]] = {}
        self._fetters: Dict[int, List[Dict[str, Any]]] = {}
        self._fetter_stories: Dict[int, List[Dict[str, Any]]] = {}
        
        self._is_prepared = False

    def _get_text(self, text_map_hash: Any, default: str = "") -> str:
        """根据哈希值安全地获取原始文本。"""
        # The transform_text function is not strictly needed for avatars, but we keep it for consistency
        text, _ = transform_text(self._text_map.get(str(text_map_hash), default))
        return text

    def _prepare_data(self):
        """一次性加载所有需要的数据并进行预处理。"""
        if self._is_prepared:
            return
        
        logging.info("加载角色相关数据 (Avatar, Fetter)...")
        self._text_map = self.loader.get_json("TextMap/TextMapCHS.json")

        # Load and map all configs by avatar ID for quick access
        avatar_config_list = self.loader.get_json("ExcelBinOutput/AvatarExcelConfigData.json")
        self._avatar_configs = {item['id']: item for item in avatar_config_list if 'id' in item}

        fetter_info_list = self.loader.get_json("ExcelBinOutput/FetterInfoExcelConfigData.json")
        self._fetter_infos = {item['avatarId']: item for item in fetter_info_list if 'avatarId' in item}

        fetters_list = self.loader.get_json("ExcelBinOutput/FettersExcelConfigData.json")
        for item in fetters_list:
            avatar_id = item.get('avatarId')
            if avatar_id not in self._fetters:
                self._fetters[avatar_id] = []
            self._fetters[avatar_id].append(item)

        fetter_story_list = self.loader.get_json("ExcelBinOutput/FetterStoryExcelConfigData.json")
        for item in fetter_story_list:
            avatar_id = item.get('avatarId')
            if avatar_id not in self._fetter_stories:
                self._fetter_stories[avatar_id] = []
            self._fetter_stories[avatar_id].append(item)

        self._is_prepared = True
        logging.info("角色相关数据加载完成。")

    def get_all_avatar_ids(self) -> List[int]:
        """获取所有可解析的角色ID列表。"""
        self._prepare_data()
        # Filter for playable characters (e.g., exclude test avatars)
        return [
            avatar_id for avatar_id, config in self._avatar_configs.items()
            if len(self._get_text(config.get("nameTextMapHash"))) > 0 and config.get("skillDepotId", 0) > 1000
        ]

    def get_raw_data(self, avatar_id: int) -> Optional[Dict[str, Any]]:
        """获取单个角色的原始配置数据。"""
        self._prepare_data()
        return self._avatar_configs.get(avatar_id)

    def interpret(self, avatar_id: int) -> Optional[Avatar]:
        """解析单个角色的完整信息。"""
        self._prepare_data()

        avatar_config = self._avatar_configs.get(avatar_id)
        if not avatar_config:
            return None

        # --- Basic Info ---
        name = self._get_text(avatar_config.get("nameTextMapHash"))
        if not name: # Skip non-playable characters
            return None
        
        avatar = Avatar(
            id=avatar_id,
            name=name,
            description=self._get_text(avatar_config.get("descTextMapHash")),
            skill_depot_id=avatar_config.get("skillDepotId")
        )

        # --- Fetter Info ---
        fetter_info = self._fetter_infos.get(avatar_id, {})
        if fetter_info:
            avatar.title = self._get_text(fetter_info.get("avatarTitleTextMapHash"))
            
            # Combine birthday month and day
            birth_month = fetter_info.get('infoBirthMonth')
            birth_day = fetter_info.get('infoBirthDay')
            if birth_month and birth_day:
                avatar.birthday = f"{birth_month}-{birth_day}"

            avatar.constellation = self._get_text(fetter_info.get("avatarConstellationBeforTextMapHash"))
            avatar.nation = self._get_text(fetter_info.get("avatarNativeTextMapHash"))
            avatar.vision = self._get_text(fetter_info.get("visionBeforTextMapHash")) # Element
            
            avatar.cvs = CVs(
                chinese=self._get_text(fetter_info.get("cvChineseTextMapHash")),
                japanese=self._get_text(fetter_info.get("cvJapaneseTextMapHash")),
                english=self._get_text(fetter_info.get("cvEnglishTextMapHash")),
                korean=self._get_text(fetter_info.get("cvKoreanTextMapHash")),
            )

        # --- Fetter Stories ---
        if avatar_id in self._fetter_stories:
            for story_data in self._fetter_stories[avatar_id]:
                avatar.stories.append(Story(
                    title=self._get_text(story_data.get("storyTitleTextMapHash")),
                    text=self._get_text(story_data.get("storyContextTextMapHash"))
                ))

        # --- Fetter Voice Lines ---
        if avatar_id in self._fetters:
            for fetter_data in self._fetters[avatar_id]:
                avatar.voice_lines.append(VoiceLine(
                    title=self._get_text(fetter_data.get("voiceTitleTextMapHash")),
                    text=self._get_text(fetter_data.get("voiceFileTextTextMapHash"))
                ))

        return avatar