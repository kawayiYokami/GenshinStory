from pydantic import BaseModel, Field
from typing import List, Optional
from ._core import BaseEntity

class Message(BaseModel):
    id: int
    sender: str
    text: str

class MessageThread(BaseEntity):
    id: int # GroupID
    name: str # Combination of participants
    messages: List[Message]