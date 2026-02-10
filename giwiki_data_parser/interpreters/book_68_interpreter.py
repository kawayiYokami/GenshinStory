import logging
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.book_68 import Book, BookChapter
from giwiki_data_parser.services.dataloader import DataLoader

class BookInterpreter:
    """书籍解释器"""
    
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)
    
    def interpret(self, data: Dict[str, Any]) -> Optional[Book]:
        """解析单个书籍数据 - 公共接口"""
        return self._interpret_single(data)
    
    def interpret_all(self) -> List[Book]:
        """解析所有书籍数据"""
        books = []
        raw_data_iterator = self.loader.get_books()
        
        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                book = self._interpret_single(data, file_path)
                if book:
                    books.append(book)
            except Exception as e:
                self.logger.error(f"解析书籍数据时出错: {e}")
        
        self.logger.info(f"成功解析 {len(books)} 本书籍")
        return books
    
    def _interpret_single(self, data: Dict[str, Any], file_path: str = "") -> Optional[Book]:
        """解析单个书籍数据"""
        try:
            # 解析章节列表
            chapters = []
            chapter_list = data.get("章节列表", [])
            
            for chapter_data in chapter_list:
                if isinstance(chapter_data, dict):
                    chapter = BookChapter(
                        chapter_title=chapter_data.get("章节标题", ""),
                        chapter_name=chapter_data.get("名称"),
                        description=chapter_data.get("描述"),
                        content=chapter_data.get("内容", "")
                    )
                    chapters.append(chapter)
            
            # 创建书籍对象
            book_name = data.get("书名", "")
            book = Book(
                name=book_name,
                title=book_name,  # 使用书名作为标题
                book_name=book_name,
                book_type=data.get("类型"),
                chapters=chapters
            )
            
            # 从文件路径设置ID
            if file_path:
                book.set_id_from_filename(file_path)
            elif "_file_path" in data:
                book.set_id_from_filename(data["_file_path"])
            elif "_file_id" in data:
                file_id = str(data["_file_id"])
                if file_id.isdigit():
                    book.id = file_id
                else:
                    self.logger.warning(f"非数字文件ID，跳过: {file_id}")
                    return None
            
            return book
            
        except Exception as e:
            self.logger.error(f"解析单个书籍数据时出错: {e}")
            return None