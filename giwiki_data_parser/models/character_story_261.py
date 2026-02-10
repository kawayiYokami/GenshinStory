from typing import Optional, List, Dict, Any
from pydantic import Field

from giwiki_data_parser.models._core import BaseWikiModel, WikiMetadata

class DialogueContent(BaseWikiModel):
    """对话内容模型"""
    character: str = Field(..., description="角色名称")
    content: str = Field(..., description="对话内容")

class DialogueBranch(BaseWikiModel):
    """对话分支模型"""
    option: str = Field(..., description="选项文本")
    dialogue_content: List[DialogueContent] = Field(default_factory=list, description="对话内容")
    sub_branches: List['DialogueBranch'] = Field(default_factory=list, description="子分支")

class DialogueSection(BaseWikiModel):
    """对话章节模型"""
    title: str = Field(..., description="章节标题")
    summary: Optional[str] = Field(None, description="章节简介")
    dialogues: List[DialogueBranch] = Field(default_factory=list, description="对话分支")

class GiftDialogue(BaseWikiModel):
    """角色赠礼对话模型"""
    title: str = Field(..., description="赠礼标题")
    summary: Optional[str] = Field(None, description="赠礼简介")
    dialogue_content: List[DialogueContent] = Field(default_factory=list, description="对话内容")

class CharacterStory(BaseWikiModel):
    """角色逸闻数据模型"""
    
    # 统一标题字段（用于文件名和H1标题）
    title: str = Field(..., description="角色逸闻标题")
    
    # 基本信息
    character_name: str = Field(..., description="角色名称")
    story_type: Optional[str] = Field(None, description="逸闻类型")
    birthday: Optional[str] = Field(None, description="生日")
    affiliation: Optional[str] = Field(None, description="所属组织")
    character_intro: Optional[str] = Field(None, description="角色介绍")
    
    # 对话内容
    teapot_dialogues: List[DialogueSection] = Field(default_factory=list, description="角色洞天对话")
    gift_dialogues: List[GiftDialogue] = Field(default_factory=list, description="角色赠礼对话")
    
    # 其他可能的故事内容
    anecdotes: List[str] = Field(default_factory=list, description="逸闻纪事")
    easter_eggs: List[str] = Field(default_factory=list, description="剧情彩蛋")
    birthday_mails: List[Dict[str, Any]] = Field(default_factory=list, description="生日邮件")
    
    # 元数据
    metadata: Optional[WikiMetadata] = None
    
    class Config:
        extra = "allow"

# 更新前向引用
DialogueBranch.model_rebuild()