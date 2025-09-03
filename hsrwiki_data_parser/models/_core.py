from pydantic import BaseModel
from typing import Any

class BaseEntity(BaseModel):
    """A base model for all data entities, providing common fields like id and name."""
    id: Any
    name: str

