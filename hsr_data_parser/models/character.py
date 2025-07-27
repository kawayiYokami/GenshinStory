from dataclasses import dataclass, field
from typing import List

@dataclass
class CharacterStory:
    """Represents a single character story entry."""
    id: int
    text: str

@dataclass
class CharacterVoiceLine:
    """Represents a single character voice line."""
    id: int
    title: str
    text: str

@dataclass
class Character:
    """Represents a complete character with stories and voice lines."""
    id: int
    name: str
    stories: List[CharacterStory] = field(default_factory=list)
    voice_lines: List[CharacterVoiceLine] = field(default_factory=list)