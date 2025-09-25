from typing import Optional, List
from pydantic import Field

from giwiki_data_parser.models._core import BaseWikiModel, WikiMetadata

class Enemy(BaseWikiModel):
    """敌人数据模型"""
    
    # 基本信息
    name: str = Field(..., description="敌人名称")
    element: Optional[str] = Field(None, description="元素属性")
    
    # 攻击方式
    attack_methods: List[str] = Field(default_factory=list, description="攻击方式名称列表")
    
    # 背景故事
    background_story: Optional[str] = Field(None, description="敌人背景故事")
    
    # 元数据
    metadata: Optional[WikiMetadata] = None
    
    class Config:
        extra = "allow"