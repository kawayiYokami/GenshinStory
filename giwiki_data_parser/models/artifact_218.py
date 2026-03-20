from typing import Optional
from pydantic import Field

from giwiki_data_parser.models._core import BaseWikiModel, WikiMetadata

class ArtifactPiece(BaseWikiModel):
    """圣遗物单件模型"""
    name: str = Field(..., description="圣遗物名称")
    description: str = Field(..., description="圣遗物描述")
    story: str = Field(..., description="圣遗物故事")

class ArtifactSet(BaseWikiModel):
    """圣遗物套装数据模型"""
    
    # 统一标题字段（用于文件名和H1标题）
    title: str = Field(..., description="圣遗物套装标题")
    
    # 基本信息
    set_name: str = Field(..., description="套装名称")
    artifact_type: Optional[str] = Field(None, description="圣遗物类型")
    
    # 五个部位的圣遗物
    flower: Optional[ArtifactPiece] = Field(None, description="生之花")
    feather: Optional[ArtifactPiece] = Field(None, description="死之羽")
    sands: Optional[ArtifactPiece] = Field(None, description="时之沙")
    goblet: Optional[ArtifactPiece] = Field(None, description="空之杯")
    circlet: Optional[ArtifactPiece] = Field(None, description="理之冠")
    
    # 元数据
    metadata: Optional[WikiMetadata] = None
    
    class Config:
        extra = "allow"