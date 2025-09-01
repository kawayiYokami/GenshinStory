from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Option:
    """Represents a single player choice option."""
    text: str
    long_text: Optional[str]
    jump_to_sequence_id: int


@dataclass
class PlayerOptions:
    """Represents a group of player options for a stage."""
    message_id: int
    options: List[Option]
    unlocks_condition: Optional[int] = None


@dataclass
class Message:
    """Represents a single NPC or player message."""
    message_id: int
    speaker_id: int
    speaker_name: str
    text: str
    unlocks_condition: Optional[int] = None


@dataclass
class Stage:
    """Represents a conversation stage, identified by Sequence No."""
    sequence_id: int
    messages: List[Message] = field(default_factory=list)
    player_options: Optional[PlayerOptions] = None
    is_end_signal: bool = False


@dataclass
class Session:
    """Represents a complete conversation session."""
    session_id: int
    main_npc_id: int
    main_npc_name: str
    stages: Dict[int, Stage] = field(default_factory=dict)  # Key is sequence_id