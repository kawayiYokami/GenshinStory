from pydantic import BaseModel, Field
from typing import List, Optional
from ._core import BaseWikiModel

class Message(BaseModel):
    id: int
    sender: str
    text: str

class MessageThread(BaseWikiModel):
    id: int # GroupID
    name: str # Combination of participants
    messages: List[Message]