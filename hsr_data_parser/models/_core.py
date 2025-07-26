from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class QuestStep:
    """Represents a single step (a SubMission) in a quest."""
    step_id: int
    title: Optional[str] = None
    description: Optional[str] = None

@dataclass
class Quest:
    """Represents a single quest."""
    quest_id: int
    quest_title: Optional[str] = None
    steps: List[QuestStep] = field(default_factory=list)