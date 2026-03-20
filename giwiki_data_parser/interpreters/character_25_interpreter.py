"""
原神Wiki 角色数据解释器

负责将JSON数据转换为角色数据模型，专注于提取角色故事、语音、命座等丰富内容。
"""

import logging
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.character_25 import (
    CharacterModel, Constellation, CharacterStory, VoiceActor,
    CharacterVoice, AssociatedVoice
)
from giwiki_data_parser.services.dataloader import DataLoader


class CharacterInterpreter:
    """角色数据解释器"""

    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)

    def interpret(self, data: Dict[str, Any]) -> Optional[CharacterModel]:
        """解析单个角色数据 - 公共接口"""
        return self._interpret_single(data)

    def interpret_all(self) -> List[CharacterModel]:
        """解析所有角色数据"""
        characters = []
        raw_data_iterator = self.loader.get_characters()

        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                character = self._interpret_single(data, file_path)
                if character:
                    characters.append(character)
            except Exception as e:
                self.logger.error(f"解析角色数据时出错: {e}")

        self.logger.info(f"成功解析 {len(characters)} 个角色")
        return characters

    def _interpret_single(self, data: Dict[str, Any], file_path: str = "") -> Optional[CharacterModel]:
        """解析单个角色数据"""
        try:
            # 基础信息提取
            name = data.get("名称", "").strip()
            if not name:
                self.logger.warning("角色名称为空，跳过")
                return None

            rarity = data.get("星级", 0)
            basic_info = data.get("基础信息", {})

            # 解析命之座
            constellations = []
            constellation_data = data.get("命之座", [])
            for const_item in constellation_data:
                if isinstance(const_item, dict) and "名称" in const_item and "描述" in const_item:
                    constellation = Constellation(
                        name=const_item["名称"],
                        description=const_item["描述"]
                    )
                    constellations.append(constellation)

            # 解析角色故事
            character_stories = []
            story_data = data.get("角色故事", [])
            for story_item in story_data:
                if isinstance(story_item, dict) and "标题" in story_item and "内容" in story_item:
                    story = CharacterStory(
                        title=story_item["标题"],
                        content=story_item["内容"]
                    )
                    character_stories.append(story)

            # 特殊料理
            special_dish = data.get("特殊料理", "")

            # 生日邮件
            birthday_mails = data.get("生日邮件", [])
            if not isinstance(birthday_mails, list):
                birthday_mails = [str(birthday_mails)] if birthday_mails else []

            # 解析配音
            voice_actor_data = data.get("配音", {})
            voice_actors = VoiceActor(
                chinese=voice_actor_data.get("汉语", []),
                japanese=voice_actor_data.get("日语", []),
                korean=voice_actor_data.get("韩语", []),
                english=voice_actor_data.get("英语", [])
            )

            # 解析角色语音
            character_voices = []
            voice_data = data.get("角色语音", [])
            for voice_item in voice_data:
                if isinstance(voice_item, dict) and "场景" in voice_item and "内容" in voice_item:
                    voice = CharacterVoice(
                        scene=voice_item["场景"],
                        content=voice_item["内容"]
                    )
                    character_voices.append(voice)

            # 解析角色关联语音
            associated_voices = []
            associated_voice_data = data.get("角色关联语音", [])
            for voice_item in associated_voice_data:
                if isinstance(voice_item, dict) and "角色" in voice_item and "内容" in voice_item:
                    # 跳过标题行
                    if voice_item["角色"] == "角色":
                        continue
                    voice = AssociatedVoice(
                        character=voice_item["角色"],
                        content=voice_item["内容"]
                    )
                    associated_voices.append(voice)

            # 创建角色对象
            character = CharacterModel(
                name=name,
                rarity=rarity,
                basic_info=basic_info,
                constellations=constellations,
                character_stories=character_stories,
                special_dish=special_dish,
                birthday_mails=birthday_mails,
                voice_actors=voice_actors,
                character_voices=character_voices,
                associated_voices=associated_voices
            )

            # 从文件路径设置ID
            if file_path:
                character.set_id_from_filename(file_path)
            elif "_file_path" in data:
                character.set_id_from_filename(data["_file_path"])
            elif "_file_id" in data:
                file_id = str(data["_file_id"])
                if file_id.isdigit():
                    character.id = file_id
                else:
                    self.logger.warning(f"非数字文件ID，跳过: {file_id}")
                    return None

            return character

        except Exception as e:
            self.logger.error(f"解析角色数据时出错: {e}")
            return None