from __future__ import annotations
import dataclasses
from typing import List

@dataclasses.dataclass
class RelicPartStory:
    """代表单个圣遗物部件及其从WIKI抓取的故事。"""
    name: str
    story: str

@dataclasses.dataclass
class Relic:
    """
    代表一个完整的圣遗物套装, 融合了游戏内数据和抓取的故事。
    """
    id: int
    name: str
    parts: List[RelicPartStory]
