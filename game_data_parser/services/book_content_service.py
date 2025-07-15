from typing import Any, Dict, List, Optional

from ..dataloader import DataLoader
from ..interpreters.book_content_interpreter import BookContentInterpreter
from ..models import BookContent
from .base_service import BaseService


class BookContentService(BaseService):
    """
    提供所有与“书籍内容(BookContent)”领域相关的查询和操作。
    它只处理来自 Readable 目录的 .txt 文件。
    """
    def __init__(self, loader: DataLoader):
        self.interpreter = BookContentInterpreter(loader)
        super().__init__({}, {})

    def list(self, **kwargs) -> List[Dict[str, Any]]:
        """获取所有已解析的书籍内容的ID列表。"""
        all_ids = self.interpreter.get_all_book_ids()
        # Per design, if a descriptive name doesn't exist, it should not be returned.
        return [{"id": content_id} for content_id in all_ids]

    def get(self, item_id: int) -> Optional[BookContent]:
        """根据文件名中的ID获取单本书籍的内容。"""
        return self.interpreter.interpret(item_id)

    def get_raw(self, item_id: int) -> Optional[str]:
        """获取书籍内容的原始文本。"""
        return self.interpreter.get_raw_data(item_id)

    def as_markdown(self, item_id: int) -> Optional[str]:
        """
        对于书籍内容，其Markdown表示就是其原始文本。
        """
        book_content = self.get(item_id)
        return book_content.content if book_content else None