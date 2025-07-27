from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class TalkSentence:
    """Represents a single sentence of dialogue from TalkSentenceConfig.json."""
    sentence_id: int
    text: Optional[str] = None

@dataclass
class QuestStep:
    """Represents a single sub-mission with its UI text."""
    step_id: int
    target_text: Optional[str] = None
    description_text: Optional[str] = None

@dataclass
class Quest:
    """Represents a quest from ExcelOutput, containing its steps."""
    quest_id: int
    steps: List[QuestStep] = field(default_factory=list)

@dataclass
class MainMission:
    """Represents the metadata for a main mission."""
    id: int
    name: Optional[str] = None
    description: Optional[str] = None