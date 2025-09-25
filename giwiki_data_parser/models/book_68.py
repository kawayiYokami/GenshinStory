from typing import Optional, List
from pydantic import Field

from giwiki_data_parser.models._core import BaseWikiModel, WikiMetadata

class BookChapter(BaseWikiModel):
    """书籍章节模型"""
    chapter_title: str = Field(..., description="章节标题")
    chapter_name: Optional[str] = Field(None, description="章节名称")
    description: Optional[str] = Field(None, description="章节描述")
    content: str = Field(..., description="章节内容")

class Book(BaseWikiModel):
    """书籍数据模型"""
    
    # 统一标题字段（用于文件名和H1标题）
    title: str = Field(..., description="书籍标题")
    
    # 基本信息
    book_name: str = Field(..., description="书籍名称")
    book_type: Optional[str] = Field(None, description="书籍类型")
    
    # 章节内容
    chapters: List[BookChapter] = Field(default_factory=list, description="章节列表")
    
    # 元数据
    metadata: Optional[WikiMetadata] = None
    
    class Config:
        extra = "allow"