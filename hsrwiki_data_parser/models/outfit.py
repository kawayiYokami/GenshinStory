from pydantic import BaseModel, Field
from typing import Optional
from ._core import BaseWikiModel

class OutfitMetadata(BaseModel):
    type: Optional[str] = None

class Outfit(BaseWikiModel):
    """Represents an outfit, avatar, or other cosmetic item."""
    id: int
    name: str = Field(..., alias='title')
    description: Optional[str] = None
    metadata: Optional[OutfitMetadata] = None
