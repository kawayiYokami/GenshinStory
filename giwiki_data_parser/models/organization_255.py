from typing import Optional, List, Dict, Any, Union
from pydantic import Field

from giwiki_data_parser.models._core import BaseWikiModel, WikiMetadata

class OrganizationBranch(BaseWikiModel):
    """组织的分支信息或特性"""
    name: str = Field(..., description="分支或特性的名称")
    description: str = Field(..., description="对应的详细描述")

class OrganizationEvent(BaseWikiModel):
    """组织的重大事件"""
    event: str = Field(..., description="事件名称或标题")
    description: str = Field(..., description="事件详细描述")

class OrganizationSubordinate(BaseWikiModel):
    """组织的下属机构"""
    name: str = Field(..., description="下属机构名称")
    description: str = Field(..., description="下属机构描述")
    details: Optional[List[str]] = Field(default_factory=list, description="详细信息")

class Organization(BaseWikiModel):
    """组织数据模型"""
    
    # 基本信息
    name: str = Field(..., description="组织名称")
    org_type: Optional[str] = Field(None, description="组织类型")
    
    # 核心简介
    summary: Optional[str] = Field(None, description="组织的摘要性描述或引言")
    
    # 详细设定
    branches: List[OrganizationBranch] = Field(default_factory=list, description="组织的分支、特性或传统")
    
    # 其他信息
    subordinates: List[Union[str, OrganizationSubordinate]] = Field(default_factory=list, description="下属机构")
    anecdotes: List[str] = Field(default_factory=list, description="趣闻")
    major_events: List[Union[str, OrganizationEvent]] = Field(default_factory=list, description="重大事迹")
    
    # 元数据
    metadata: Optional[WikiMetadata] = None
    
    class Config:
        extra = "allow"