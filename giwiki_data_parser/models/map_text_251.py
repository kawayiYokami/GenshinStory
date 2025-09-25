"""地图文本数据模型"""
from typing import List, Optional
from pydantic import Field
from ._core import BaseWikiModel, WikiMetadata


class MapTextModel(BaseWikiModel):
    """地图文本模型"""
    
    title: str = Field(..., description="文本标题")
    type: Optional[str] = Field(None, description="类型")
    region: Optional[str] = Field(None, description="地区")
    location_images: List[str] = Field(default_factory=list, description="位置图片")
    content: List[str] = Field(default_factory=list, description="文本内容")
    
    # 元数据
    metadata: Optional[WikiMetadata] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "蒙德百货订货板",
                "type": "地图文本",
                "region": "",
                "location_images": ["https://example.com/image1.png"],
                "content": [
                    "【开场白】",
                    "请将希望进货的商品名写在便条上..."
                ]
            }
        }