from dataclasses import dataclass, field
from typing import List, Optional, Union

@dataclass
class DialogueSentence:
    """表示单行对话。"""
    text: str
    speaker: Optional[str] = None
    id: Optional[int] = None # 用于存储原始的 TalkSentenceID 以便追溯

@dataclass
class DialogueOption:
    """表示玩家的对话选择及其后续的对话流。"""
    text: str
    trigger_string: str # 由此选项触发的内部信号
    follow_up: List['DialogueElement'] = field(default_factory=list)

@dataclass
class DialogueOptionGroup:
    """表示呈现给玩家的一组对话选项。"""
    options: List[DialogueOption] = field(default_factory=list)

# 为对话块内的元素定义递归类型别名
DialogueElement = Union[DialogueSentence, DialogueOptionGroup]

@dataclass
class DialogueBlock:
    """
    表示一个对话块，现在可以包含句子和嵌套选项组的混合，
    形成一个递归结构。
    """
    sentences: List[DialogueElement] = field(default_factory=list)

@dataclass
class ActScript:
    """
    Act、Mission 或 Talk 文件的简化表示，
    仅包含对话块的序列。
    """
    dialogue_blocks: List[DialogueBlock] = field(default_factory=list)