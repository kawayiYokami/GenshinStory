"""
原神Wiki 角色数据模型

处理角色相关的数据结构，专注于提取角色故事、语音、命座等丰富内容。
"""

from typing import List, Optional, Dict, Any
from pydantic import Field
from ._core import BaseWikiModel, WikiMetadata


class Constellation(BaseWikiModel):
    """命之座模型"""

    name: str = Field(..., description="命座名称")
    description: str = Field(..., description="命座描述")


class CharacterStory(BaseWikiModel):
    """角色故事模型"""

    title: str = Field(..., description="故事标题")
    content: str = Field(..., description="故事内容")


class VoiceActor(BaseWikiModel):
    """配音演员模型"""

    chinese: List[str] = Field(default_factory=list, description="汉语配音")
    japanese: List[str] = Field(default_factory=list, description="日语配音")
    korean: List[str] = Field(default_factory=list, description="韩语配音")
    english: List[str] = Field(default_factory=list, description="英语配音")


class CharacterVoice(BaseWikiModel):
    """角色语音模型"""

    scene: str = Field(..., description="语音场景")
    content: str = Field(..., description="语音内容")


class AssociatedVoice(BaseWikiModel):
    """角色关联语音模型"""

    character: str = Field(..., description="说话的角色")
    content: str = Field(..., description="语音内容")


class CharacterModel(BaseWikiModel):
    """角色数据模型"""

    # 基础信息
    name: str = Field(..., description="角色名称")
    rarity: int = Field(..., description="星级")
    basic_info: Dict[str, str] = Field(default_factory=dict, description="基础信息")

    # 命之座
    constellations: List[Constellation] = Field(default_factory=list, description="命之座列表")

    # 角色故事
    character_stories: List[CharacterStory] = Field(default_factory=list, description="角色故事列表")

    # 特殊料理
    special_dish: str = Field(default="", description="特殊料理")

    # 生日邮件
    birthday_mails: List[str] = Field(default_factory=list, description="生日邮件列表")

    # 配音
    voice_actors: VoiceActor = Field(default_factory=VoiceActor, description="配音演员")

    # 角色语音
    character_voices: List[CharacterVoice] = Field(default_factory=list, description="角色语音列表")

    # 角色关联语音
    associated_voices: List[AssociatedVoice] = Field(default_factory=list, description="角色关联语音列表")

    def get_character_name(self) -> str:
        """获取角色名称"""
        return self.name.strip()

    def get_element(self) -> str:
        """获取角色元素"""
        return self.basic_info.get("神之眼", self.basic_info.get("元素", ""))

    def get_weapon_type(self) -> str:
        """获取武器类型"""
        return self.basic_info.get("武器类型", self.basic_info.get("武器", ""))

    def get_region(self) -> str:
        """获取所属地区"""
        return self.basic_info.get("所属", "")

    def get_birthday(self) -> str:
        """获取生日"""
        return self.basic_info.get("生日", "")

    def has_story_content(self) -> bool:
        """判断是否包含故事内容"""
        # 角色数据通常都包含丰富的故事内容
        return len(self.character_stories) > 0 or len(self.character_voices) > 10

    def get_constellation_count(self) -> int:
        """获取命座数量"""
        return len(self.constellations)

    def get_voice_count(self) -> int:
        """获取语音数量"""
        return len(self.character_voices)

    def get_story_count(self) -> int:
        """获取故事数量"""
        return len(self.character_stories)

    def has_special_dish(self) -> bool:
        """是否有特殊料理"""
        return bool(self.special_dish.strip())

    def get_all_voice_actors(self) -> List[str]:
        """获取所有配音演员"""
        all_actors = []
        all_actors.extend(self.voice_actors.chinese)
        all_actors.extend(self.voice_actors.japanese)
        all_actors.extend(self.voice_actors.korean)
        all_actors.extend(self.voice_actors.english)
        return all_actors

    def search_in_content(self, keyword: str) -> bool:
        """在角色内容中搜索关键词"""
        search_text = f"{self.name} {self.special_dish}"

        # 搜索基础信息
        for key, value in self.basic_info.items():
            search_text += f" {key} {value}"

        # 搜索故事内容
        for story in self.character_stories:
            search_text += f" {story.title} {story.content}"

        # 搜索语音内容
        for voice in self.character_voices:
            search_text += f" {voice.scene} {voice.content}"

        # 搜索关联语音
        for voice in self.associated_voices:
            search_text += f" {voice.character} {voice.content}"

        return keyword.lower() in search_text.lower()


class CharacterCollection(BaseWikiModel):
    """角色集合模型"""

    characters: List[CharacterModel] = Field(default_factory=list, description="角色列表")
    metadata: WikiMetadata = Field(default_factory=WikiMetadata, description="元数据")

    def get_story_characters(self) -> List[CharacterModel]:
        """获取包含故事内容的角色"""
        return [char for char in self.characters if char.has_story_content()]

    def group_by_element(self) -> Dict[str, List[CharacterModel]]:
        """按元素分组"""
        element_groups = {}

        for character in self.characters:
            element = character.get_element()
            if not element:
                element = "未知元素"

            if element not in element_groups:
                element_groups[element] = []
            element_groups[element].append(character)

        return element_groups

    def group_by_rarity(self) -> Dict[int, List[CharacterModel]]:
        """按星级分组"""
        rarity_groups = {}

        for character in self.characters:
            rarity = character.rarity
            if rarity not in rarity_groups:
                rarity_groups[rarity] = []
            rarity_groups[rarity].append(character)

        return rarity_groups

    def group_by_region(self) -> Dict[str, List[CharacterModel]]:
        """按地区分组"""
        region_groups = {}

        for character in self.characters:
            region = character.get_region()
            if not region:
                region = "未知地区"

            if region not in region_groups:
                region_groups[region] = []
            region_groups[region].append(character)

        return region_groups

    def search_by_keyword(self, keyword: str) -> List[CharacterModel]:
        """按关键词搜索角色"""
        results = []

        for character in self.characters:
            if character.search_in_content(keyword):
                results.append(character)

        return results

    def get_characters_with_special_dish(self) -> List[CharacterModel]:
        """获取有特殊料理的角色"""
        return [char for char in self.characters if char.has_special_dish()]