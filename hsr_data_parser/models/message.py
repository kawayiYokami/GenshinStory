from dataclasses import dataclass, field
from typing import List

@dataclass
class Message:
    """Represents a single message item in a conversation."""
    id: int
    sender: str
    text: str

@dataclass
class MessageThread:
    """Represents a complete conversation thread with a contact."""
    id: int  # This will be the SectionID
    contact_id: int
    contact_name: str
    title: str
    messages: List[Message] = field(default_factory=list)