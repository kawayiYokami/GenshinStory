from typing import Optional
from pydantic import Field

from giwiki_data_parser.models._core import BaseWikiModel, WikiMetadata

class Weapon(BaseWikiModel):
    """武器数据模型"""
    
    # 基本信息
    name: str = Field(..., description="武器名称")
    description: Optional[str] = Field(None, description="武器描述")
    rarity: Optional[int] = Field(None, description="稀有度")
    weapon_type: Optional[str] = Field(None, description="武器类型")
    
    # 武器故事
    story: Optional[str] = Field(None, description="武器背景故事")
    
    # 元数据
    metadata: Optional[WikiMetadata] = None
    
    class Config:
        extra = "allow"