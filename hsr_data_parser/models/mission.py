from dataclasses import dataclass, field
from typing import List, Optional

from .act import ActScript
from ._core import QuestStep, MainMission

@dataclass
class SubMissionScript:
    """SubMission 的简化表示，包含其逻辑脚本和 UI 文本。"""
    id: int
    script: Optional[ActScript] = None
    ui_info: Optional[QuestStep] = None # 用于保存目标/描述文本的字段
    summary: Optional[str] = None # 用于保存来自 PerformanceSkipOverride 的任务摘要的字段


@dataclass
class MainMission:
    """Mission 的简化表示，包含其子任务脚本的列表。"""
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    scripts: List[SubMissionScript] = field(default_factory=list)
