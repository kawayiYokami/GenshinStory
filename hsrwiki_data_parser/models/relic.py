from pydantic import BaseModel, Field
from typing import List, Optional
from ._core import BaseWikiModel

class RelicPiece(BaseModel):
    """Represents a single piece of a relic set."""
    name: str
    story: str

class SetEffect(BaseModel):
    """Represents a set effect (e.g., 2-piece or 4-piece bonus)."""
    count: int
    description: str

class Relic(BaseWikiModel):
    """Represents a relic set loaded from the structured JSON files."""
    id: int
    name: str = Field(..., alias='title')
    set_effects: List[SetEffect]
    pieces: List[RelicPiece]
    source_url: str = Field(..., alias="source_url")
