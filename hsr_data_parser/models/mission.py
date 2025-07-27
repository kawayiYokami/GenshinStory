from dataclasses import dataclass, field
from typing import List, Optional

from .act import ActScript
from ._core import QuestStep, MainMission

@dataclass
class SubMissionScript:
    """A simplified representation of a SubMission, containing its logic script and UI text."""
    id: int
    script: Optional[ActScript] = None
    ui_info: Optional[QuestStep] = None # Field to hold target/description text


@dataclass
class MainMission:
    """A simplified representation of a Mission, containing a list of its sub-mission scripts."""
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    scripts: List[SubMissionScript] = field(default_factory=list)
