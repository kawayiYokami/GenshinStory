"""
原神Wiki NPC数据模型

处理NPC相关的数据结构，专注于提取对话内容和角色背景故事。
"""

from typing import List, Optional
from pydantic import Field
from ._core import BaseWikiModel, WikiMetadata


class DialogueOption(BaseWikiModel):
    """对话选项模型"""

    option: str = Field(..., description="选项名称")
    content: List[str] = Field(default_factory=list, description="对话内容列表")


class DialogueGroup(BaseWikiModel):
    """对话组模型"""

    title: str = Field(..., description="对话组标题")
    dialogues: List[DialogueOption] = Field(default_factory=list, description="对话选项列表")


class NPCModel(BaseWikiModel):
    """NPC数据模型"""

    # 基础信息
    name: str = Field(..., description="NPC名称")
    gender: str = Field(default="", description="性别")
    location: str = Field(default="", description="位置")

    # 对话组
    dialogue_groups: List[DialogueGroup] = Field(default_factory=list, description="对话组列表")

    def get_character_name(self) -> str:
        """获取角色名称"""
        return self.name.strip()

    def has_story_content(self) -> bool:
        """判断是否包含故事内容"""
        # 检查是否有对话内容
        total_dialogues = sum(len(group.dialogues) for group in self.dialogue_groups)
        if total_dialogues > 3:
            return True

        # 检查对话内容长度
        total_content = sum(
            len(option.content)
            for group in self.dialogue_groups
            for option in group.dialogues
        )
        return total_content > 5

    def get_all_dialogue_content(self) -> List[str]:
        """获取所有对话内容"""
        all_content = []
        for group in self.dialogue_groups:
            for option in group.dialogues:
                all_content.extend(option.content)
        return all_content
    

class NPCCollection(BaseWikiModel):
    """NPC集合模型"""

    npcs: List[NPCModel] = Field(default_factory=list, description="NPC列表")
    metadata: WikiMetadata = Field(default_factory=WikiMetadata, description="元数据")

    def get_story_npcs(self) -> List[NPCModel]:
        """获取包含故事内容的NPC"""
        return [npc for npc in self.npcs if npc.has_story_content()]

    def group_by_location(self) -> dict:
        """按位置分组"""
        location_groups = {}

        for npc in self.npcs:
            location = npc.location if npc.location else "未知位置"
            if location not in location_groups:
                location_groups[location] = []
            location_groups[location].append(npc)

        return location_groups

    def search_by_keyword(self, keyword: str) -> List[NPCModel]:
        """按关键词搜索NPC"""
        results = []

        for npc in self.npcs:
            # 在名称和对话内容中搜索
            all_content = npc.get_all_dialogue_content()
            search_text = f"{npc.name} {' '.join(all_content)}"
            if keyword.lower() in search_text.lower():
                results.append(npc)

        return results