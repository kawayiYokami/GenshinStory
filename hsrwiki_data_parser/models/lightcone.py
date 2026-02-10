from pydantic import BaseModel, Field
from typing import Optional
from ._core import BaseWikiModel


class LightconeMetadata(BaseModel):
    """光锥元数据"""
    type: Optional[str] = None


class Lightcone(BaseWikiModel):
    """Represents a lightcone's data loaded from the structured JSON files."""
    id: int
    name: str = Field(..., alias='title')
    path: str = Field(..., description="光锥的命途，如巡猎、虚无等")
    rarity: str = Field(..., description="光锥星级，如4星、5星")
    description: str = Field(..., description="光锥的背景描述")
    source_url: str = Field(..., alias="source_url")
    metadata: Optional[LightconeMetadata] = None