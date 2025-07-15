import logging
import re
from typing import Dict, List, Optional

from ..dataloader import DataLoader
from ..models import BookContent

class BookContentInterpreter:
    """
    负责将原始的书籍内容文件（.txt）解析成结构化的 BookContent 对象。
    """
    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
        
        # Pre-processed data caches
        self._book_contents: Dict[int, BookContent] = {}
        
        self._is_prepared = False

    def _prepare_data(self):
        """一次性加载所有需要的数据并进行预处理。"""
        if self._is_prepared:
            return
        
        logging.info("加载书籍内容文件 (BookContent)...")
        
        content_files = self.loader.get_all_file_paths_in_folder("Readable/CHS", name_contains="Book")
        
        for file_path in content_files:
            try:
                # Extract ID from filename like "Book37.txt"
                match = re.search(r"Book(\d+)\.txt", self.loader.get_file_name(file_path))
                if not match:
                    continue
                
                book_id = int(match.group(1))
                full_content = self.loader.get_text_file(file_path)

                if not full_content:
                    continue
                
                # The entire file is the content, there is no separate title.
                self._book_contents[book_id] = BookContent(
                    id=book_id,
                    content=full_content.strip()
                )

            except Exception as e:
                logging.warning(f"无法解析书籍内容文件 {file_path}: {e}")

        self._is_prepared = True
        logging.info(f"书籍内容文件加载完成，共找到 {len(self._book_contents)} 本。")

    def get_all_book_ids(self) -> List[int]:
        """获取所有书籍内容ID列表。"""
        self._prepare_data()
        return list(self._book_contents.keys())

    def interpret(self, book_id: int) -> Optional[BookContent]:
        """解析单个书籍内容的完整信息。"""
        self._prepare_data()
        return self._book_contents.get(book_id)

    def get_raw_data(self, book_id: int) -> Optional[str]:
        """获取书籍内容的原始文本。"""
        book_content = self.interpret(book_id)
        return book_content.content if book_content else None