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

class AdventurerGuildSubTask(BaseWikiModel):
    """冒险家协会子任务数据模型"""

    # 基本信息
    name: str = Field(..., description="子任务名称", alias="名称")
    trigger_condition: Optional[str] = Field(None, description="触发条件", alias="触发条件")

    # 任务流程
    quest_steps: List[str] = Field(default_factory=list, description="任务过程", alias="任务过程")

    # 剧情内容
    dialogue_content: List[DialogueEntry] = Field(default_factory=list, description="剧情对话", alias="剧情对话")

    class Config:
        extra = "allow"
        populate_by_name = True

class AdventurerGuild(BaseWikiModel):
    """冒险家协会数据模型"""

    # 基本信息
    name: str = Field(..., description="任务标题", alias="任务标题")

    # 子任务列表
    sub_tasks: List[AdventurerGuildSubTask] = Field(default_factory=list, description="子任务列表", alias="任务列表")

    # 元数据
    metadata: Optional[WikiMetadata] = None

    class Config:
        extra = "allow"
        populate_by_name = True  # 允许使用字段名和别名