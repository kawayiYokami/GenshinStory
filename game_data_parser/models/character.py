from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class VoiceLine:
    """代表一条角色的语音台词。"""
    title: str
    text: str

@dataclass
class Story:
    """代表一个角色的故事。"""
    title: str
    text: str

@dataclass
class CVs:
    """存储角色的多语言CV信息。"""
    chinese: Optional[str] = None
    japanese: Optional[str] = None
    english: Optional[str] = None
    korean: Optional[str] = None


@dataclass
class Character:
    """代表一个完整的角色及其所有相关信息。"""
    id: int
    name: str
    description: str
    
    # Fetter Info
    title: Optional[str] = None          # 称号
    birthday: Optional[str] = None       # 生日 (格式 "月-日")
    constellation: Optional[str] = None  # 命之座
    nation: Optional[str] = None         # 所属国家/地区
    vision: Optional[str] = None         # 神之眼
    cvs: CVs = field(default_factory=CVs)
    
    # Detailed stories and sayings
    stories: List[Story] = field(default_factory=list)
    voice_lines: List[VoiceLine] = field(default_factory=list)
    
    # Raw related IDs
    skill_depot_id: Optional[int] = None