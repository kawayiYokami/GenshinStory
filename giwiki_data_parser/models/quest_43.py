from typing import Optional, List, Union, Any
from pydantic import Field

from giwiki_data_parser.models._core import BaseWikiModel, WikiMetadata

class DialogueChoice(BaseWikiModel):
    """对话选择项模型"""
    text: str = Field(..., description="选择文本")

class DialogueEntry(BaseWikiModel):
    """对话条目模型"""
    speaker: Optional[str] = Field(None, description="说话者")
    text: Optional[str] = Field(None, description="对话内容")
    choices: Optional[List[str]] = Field(None, description="选择项（如果有）")
    dialogue_type: Optional[str] = Field(None, description="对话类型", alias="type")
    reply: Optional[List[Union['DialogueEntry', Any]]] = Field(None, description="回复选项")
    special_type: Optional[str] = Field(None, description="特殊对话类型")

    class Config:
        extra = "allow"
        populate_by_name = True

# 更新前向引用
DialogueEntry.model_rebuild()

class QuestNPC(BaseWikiModel):
    """任务NPC模型"""
    name: str = Field(..., description="NPC名称", alias="名称")
    link: Optional[str] = Field(None, description="NPC链接", alias="链接")
    
    class Config:
        extra = "allow"
        populate_by_name = True

class SubQuest(BaseWikiModel):
    """子任务数据模型"""

    # 基本信息
    name: str = Field(..., description="子任务名称", alias="名称")
    special_requirements: Optional[str] = Field(None, description="特殊限制", alias="特殊限制")

    # 任务流程
    quest_steps: List[str] = Field(default_factory=list, description="任务过程", alias="任务过程")

    # NPC信息
    start_npc: Optional[QuestNPC] = Field(None, description="起始NPC", alias="起始NPC")
    end_npc: Optional[QuestNPC] = Field(None, description="结束NPC", alias="结束NPC")

    # 剧情内容
    dialogue_content: List[DialogueEntry] = Field(default_factory=list, description="剧情对话", alias="剧情对话")

    class Config:
        extra = "allow"
        populate_by_name = True

class Quest(BaseWikiModel):
    """任务数据模型"""

    # 基本信息
    name: str = Field(..., description="任务名称", alias="名称")

    # 子任务列表
    sub_quests: List[SubQuest] = Field(default_factory=list, description="子任务列表")

    # 元数据
    metadata: Optional[WikiMetadata] = None

    class Config:
        extra = "allow"
        populate_by_name = True  # 允许使用字段名和别名