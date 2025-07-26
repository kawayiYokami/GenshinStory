# 在文件顶部添加对 DataLoader 的类型引用
from dataclasses import dataclass, field
from typing import List, Optional, Literal, TYPE_CHECKING
from pathlib import Path
import re

if TYPE_CHECKING:
    from .dataloader import DataLoader


@dataclass
class DialogueNode:
    """代表对话图中的一个节点，可以是单句对话、玩家选项或旁白。"""
    
    # 核心内容
    speaker: str
    content: str
    
    # 类型标识
    node_type: Literal["dialogue", "option", "narratage"] = "dialogue"

    # 结构化信息
    id: Optional[int] = None  # 对应 TalkId 或 itemId
    
    # 用于分支对话 (玩家选项)
    options: List['DialogueNode'] = field(default_factory=list)


@dataclass
class QuestStep:
    """代表任务中的一个子任务或一个主要步骤。"""
    step_id: int  # 对应 subId
    
    # 新增：用于存储 subQuestTitle
    title: Optional[str] = None
    
    # 保留：用于存储旧格式的描述
    step_description: Optional[str] = None
    
    # 修改：使用新的 DialogueNode 来存储对话流
    dialogue_nodes: List[DialogueNode] = field(default_factory=list)
    
    # 新增：用于惰性加载，存储需要解析的TalkID
    talk_ids: List[int] = field(default_factory=list)


@dataclass
class Quest:
    """代表一个单独的任务及其所有内容。"""
    quest_id: int
    quest_title: str
    quest_description: str
    
    # Context from Chapter
    chapter_id: Optional[int] = None
    chapter_title: Optional[str] = None

    # Context from Quest Series
    series_id: Optional[int] = None

    # Optional fields with defaults
    chapter_num: Optional[str] = None
    quest_type: Optional[str] = None
    steps: List[QuestStep] = field(default_factory=list)
    suggest_track_main_quest_list: Optional[List[int]] = None

    # Metadata for traceability
    source_json: Optional[str] = None # The original filename, e.g., "72105.json" or "090fef58.json"


@dataclass
class Chapter:
    """代表一个章节（Chapter）的元数据，来源于ChapterExcelConfigData.json。"""
    id: int
    title: str
    
    # Core Quest Info
    entry_quest_ids: List[int] = field(default_factory=list)
    quest_type: Optional[str] = None  # e.g., "WQ", "AQ"
    
    # Categorization
    city_id: Optional[int] = None
    group_id: Optional[int] = None
    
    # Requirements & Dependencies
    required_player_level: Optional[int] = None
    required_activity_id: Optional[int] = None
    
    # UI Text (but not images/icons)
    chapter_num_text: Optional[str] = None
    image_title: Optional[str] = None
    
    # Linked Quests
    quests: List['Quest'] = field(default_factory=list)


# ==============================================================================
# Misc Models (Reliquary, Weapon, Material)
# ==============================================================================

@dataclass
class Reliquary:
    """代表一件单独的圣遗物。"""
    id: int
    name: str
    description: str
    story: str
    
    set_id: int
    set_name: str
    
    pos_name: str  # e.g., 生之花, 死之羽
    pos_index: int # 1-5

@dataclass
class ReliquarySet:
    """代表一个圣遗物套装及其效果。"""
    id: int
    name: str
    
    # The actual set effect descriptions
    effect_2_piece: Optional[str] = None
    effect_4_piece: Optional[str] = None
    
    # List of the 5 reliquaries that belong to this set
    reliquaries: List[Reliquary] = field(default_factory=list)

@dataclass
class WeaponSkill:
    """代表武器的技能描述，包含所有精炼等级。"""
    name: str
    descriptions: List[str] = field(default_factory=list) # 5 descriptions from rank 1 to 5

@dataclass
class Weapon:
    """代表一把武器。"""
    id: int
    name: str
    description: str
    story: str

    type_name: str # e.g., 单手剑, 双手剑
    rank_level: int # Star rating (1-5)
    
    skill: Optional[WeaponSkill] = None

@dataclass
class Material:
    """代表一个材料或道具。"""
    id: int
    name: str
    description: str
    
    # 存储原始枚举，如 "MATERIAL_CHARACTER_MATERIAL"
    material_type_raw: str
    
    # 存储二级分类描述，如 "角色培养素材"
    type_name: str
    
    # For wings, this will contain the story
    story: Optional[str] = None
    
    # Book-specific fields
    is_book: bool = False
    codex_id: Optional[int] = None
    set_id: Optional[int] = None # For books, this is the BookSuit ID




# ==============================================================================
# Book Models
# ==============================================================================

@dataclass
class BookVolume:
    """代表书籍系列中的一个分卷，支持内容懒加载。"""
    # Core metadata from our JSON
    volume_title: str
    introduction: str
    book_txt_id: int
    
    # Internal state for lazy loading
    _content: Optional[str] = field(default=None, repr=False)
    _loader: 'DataLoader' = field(default=None, repr=False)

    def get_content(self) -> str:
        """
        获取分卷的具体内容。
        第一次调用时会从文件读取，后续调用会返回缓存的内容。
        """
        if self._content is not None:
            return self._content
        
        if self._loader and self.book_txt_id:
            try:
                # 修正：直接传递相对路径给 get_text_file
                relative_path = f"Readable/CHS/Book{self.book_txt_id}.txt"
                raw_content = self._loader.get_text_file(relative_path)
                if raw_content is not None:
                    # 将换行符替换为HTML换行标签以进行诊断
                    self._content = raw_content.replace('\n', '<br>')
                    return self._content
                else:
                    return f"错误：文件 '{relative_path}' 读取返回None。"
            except Exception as e:
                return f"错误：加载内容ID {self.book_txt_id} 时发生异常。原因: {e}"
        
        return "错误：内容加载器未初始化或缺少内容ID。"


@dataclass
class BookSuit:
    """代表一个书籍系列。"""
    id: int
    name: str
    volumes: List[BookVolume] = field(default_factory=list)

@dataclass
class Book:
    """代表一本书籍的元数据。"""
    id: int
    name: str
    description: str
    
    suit_id: Optional[int] = None      # 关联到 BookSuit 的 ID

# ==============================================================================
# Readable Models
# ==============================================================================
@dataclass
class Readable:
    """代表一个从 'Readable/' 目录加载的独立文本文件，支持内容懒加载。"""
    id: str      # 相对路径作为唯一ID
    title: str   # 根据内容动态生成的标题
    path: str    # 完整的相对路径
    
    _content: Optional[str] = field(default=None, repr=False)
    _loader: 'DataLoader' = field(default=None, repr=False)

    def get_content(self) -> str:
        """按需加载并返回文件内容。"""
        if self._content is not None:
            return self._content
        
        if self._loader and self.path:
            try:
                raw_content = self._loader.get_text_file(self.path)
                self._content = raw_content.strip() if raw_content else ""
                return self._content
            except Exception as e:
                return f"错误：加载内容 '{self.path}' 时发生异常: {e}"
        
        return "错误：内容加载器未初始化或缺少路径。"

@dataclass(frozen=True)
class SearchResult:
    """代表一个统一的搜索结果条目。"""
    id: int
    name: str
    type: str  # e.g., "Character", "Quest", "Weapon"
    match_source: str # 匹配到的字段名，如 "description" 或 "name"
