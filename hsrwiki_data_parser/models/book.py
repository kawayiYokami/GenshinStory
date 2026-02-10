from pydantic import BaseModel, Field
from typing import List, Optional
from ._core import BaseWikiModel

class BookContent(BaseModel):
    heading: Optional[str] = None
    text: str

class Book(BaseWikiModel):
    """Represents a book or readable item."""
    id: int
    name: str = Field(..., alias='title')
    description: Optional[str] = None
    content: List[BookContent]
