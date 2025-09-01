from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MessageOption:
    """
    Represents an option in a message that the player can choose.
    """
    text_key: Optional[str] = None
    """The key to look up the option's text in the text map."""

    long_text_key: Optional[str] = None
    """The key to look up the option's longer description in the text map."""

    next_message_id: Optional[int] = None
    """The ID of the next message if this option is chosen."""


@dataclass
class Message:
    """
    Represents a single message in a phone conversation.
    """
    id: int
    """The unique numerical identifier for the message."""

    group_id: int
    """The ID of the message group/conversation this message belongs to."""

    text_key: Optional[str] = None
    """The key to look up the message's text in the text map."""

    sequence: int = 0
    """The order of this message within its group/conversation."""

    options: List[MessageOption] = field(default_factory=list)
    """A list of options available for this message."""

    is_player_message: bool = False
    """Indicates if this message was sent by the player."""

    sender_name: str = ""
    """The name of the sender of this message (e.g., '玩家' or an NPC's name)."""

    session_npc_id: Optional[int] = None
    """The ID of the NPC associated with this conversation session."""

    session_npc_name: str = ""
    """The name of the NPC associated with this conversation session."""


@dataclass
class MessageSession:
    """
    Represents a complete phone message conversation session.
    A session groups multiple related messages together.
    """
    session_id: int
    """The unique identifier for this message session (corresponds to group_id)."""

    messages: List[Message] = field(default_factory=list)
    """A list of messages in this session, ordered by their sequence."""

    main_npc_id: Optional[int] = None
    """The ID of the main NPC involved in this private conversation."""

    main_npc_name: str = ""
    """The name of the main NPC involved in this private conversation."""