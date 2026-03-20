from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from ._core import BaseWikiModel

class CharacterMetadata(BaseModel):
    name: Optional[str] = None
    city_state: Optional[str] = Field(None, alias="city_state")

class VoiceLine(BaseModel):
    title: str
    text: str

class Character(BaseWikiModel):
    """Represents a character's data loaded from the structured JSON files."""
    id: int
    name: str = Field(..., alias='title')
    metadata: Optional[CharacterMetadata] = None
    summary: str
    story: List[str]
    voices: Dict[str, List[VoiceLine]]
    source_url: str = Field(..., alias="source_url")
