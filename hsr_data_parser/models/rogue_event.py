from __future__ import annotations
import dataclasses
from typing import List, Optional

@dataclasses.dataclass
class RogueEventOption:
    """代表一个模拟宇宙事件中的选项及其效果。"""
    id: int
    text: str
    # 可能是奖励/消耗的描述，例如 "获得80宇宙碎片"
    description: str
    # 可能是选择后触发的内部信号
    trigger: Optional[str] = None
    
@dataclasses.dataclass
class RogueEventDialogue:
    """代表一个对话单元，可以是一段简单文本或一个带选项的互动。"""
    # 如果是简单对话，则该列表包含多行对话
    simple_talk: Optional[List[str]] = None
    # 如果是选项对话，则该列表包含多个选项
    options: Optional[List[RogueEventOption]] = None
    
@dataclasses.dataclass
class RogueEvent:
    """代表一个完整的模拟宇宙事件。"""
    id: int
    # 事件中的所有对话块，按顺序排列
    dialogues: List[RogueEventDialogue]
