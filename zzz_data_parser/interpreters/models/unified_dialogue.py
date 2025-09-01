from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DialogueLine:
    """代表单行对话，包含所有可能的信息。"""
    male_text: Optional[str] = None
    female_text: Optional[str] = None
    speaker: Optional[str] = None
    options: Dict[str, str] = field(default_factory=dict)


@dataclass
class DialogueAct:
    """代表一个对话片段或活动，包含多行对话。"""
    id: str
    lines: Dict[str, DialogueLine] = field(default_factory=dict)
    speakers: Dict[str, str] = field(default_factory=dict)


@dataclass
class DialogueChapter:
    """代表一个完整的对话章节，包含元数据和多个活动。"""
    id: str
    category: str  # e.g., "Main", "Companion", "Activity"
    sub_category: Optional[str] = None # e.g., "Bubble", "Chat", "GalGame"
    acts: Dict[str, DialogueAct] = field(default_factory=dict)