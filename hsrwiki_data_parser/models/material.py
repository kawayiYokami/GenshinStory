from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from ._core import BaseWikiModel

class MaterialMetadata(BaseModel):
    type: Optional[str] = None

class Material(BaseWikiModel):
    """Represents a material, which can be of various types."""
    id: int
    name: str = Field(..., alias='title')
    description: Optional[str] = None
    metadata: Optional[MaterialMetadata] = None
    # Add other potential fields from other material types as optional
    lore: Optional[str] = None
    source: Optional[List[Dict[str, Any]]] = None # For source, drop, etc.

    # We need a way to know which original directory this came from
    # We can add this field in the interpreter
    main_type: str = Field(default="材料", exclude=True) # Exclude from serialization
