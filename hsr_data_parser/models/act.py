from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class DialogueSentence:
    """Represents a single line of dialogue, which can be a statement or an option."""
    text: str
    speaker: Optional[str] = None
    is_option: bool = False

@dataclass
class DialogueBlock:
    """
    Represents a block of dialogue, which can be a sequence of sentences
    or a set of choices for the player.
    """
    # A block contains either a list of sentences or a list of options, not both.
    sentences: List[DialogueSentence] = field(default_factory=list)

@dataclass
class ActScript:
    """
    A simplified representation of an Act, Mission, or Talk file,
    containing only the sequence of dialogue blocks.
    """
    dialogue_blocks: List[DialogueBlock] = field(default_factory=list)