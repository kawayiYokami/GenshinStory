from typing import Any, Dict, List, Optional
from dataclasses import asdict

from ..dataloader import DataLoader
from ..interpreters.material_interpreter import MaterialInterpreter
from ..interpreters.book_suit_interpreter import BookSuitInterpreter
from ..models import Material, BookSuit
from ..formatters.book_formatter import BookFormatter


class BookService:
    """
    提供所有与“书籍物料(Book Item)”领域相关的查询和操作。
    """
    def __init__(self, loader: DataLoader):
        # Service owns its interpreters and formatters
        self.material_interpreter = MaterialInterpreter(loader)
        self.book_suit_interpreter = BookSuitInterpreter(loader)
        self.formatter = BookFormatter()

    def list_books(self) -> List[Dict[str, Any]]:
        """获取所有被识别为“书籍”的物料的简明列表。"""
        all_books = []
        all_material_ids = self.material_interpreter.get_all_material_ids()
        for material_id in all_material_ids:
            material = self.material_interpreter.interpret(material_id)
            if material and material.is_book:
                all_books.append({
                    "id": material.id,
                    "name": material.name
                })
        return all_books

    def get_book_by_id(self, item_id: int) -> Optional[Material]:
        """获取单个书籍物料的完整信息。"""
        material = self.material_interpreter.interpret(item_id)
        if material and material.is_book:
            return material
        return None

    def get_book_as_json(self, item_id: int) -> Optional[Dict]:
        """获取单个书籍物料的JSON兼容字典。"""
        book = self.get_book_by_id(item_id)
        return asdict(book) if book else None

    def get_book_as_markdown(self, item_id: int) -> Optional[str]:
        """获取单本书籍的格式化Markdown文档。"""
        book_material = self.get_book_by_id(item_id)
        if not book_material:
            return None
        
        book_suit = None
        if book_material.set_id:
            book_suit = self.book_suit_interpreter.interpret(book_material.set_id)

        return self.formatter.format_book(book_material, suit=book_suit)

    def list_book_series(self) -> List[BookSuit]:
        """获取所有书籍系列。"""
        all_series = []
        all_suit_ids = self.book_suit_interpreter.get_all_suit_ids()
        for suit_id in all_suit_ids:
            series = self.book_suit_interpreter.interpret(suit_id)
            if series:
                all_series.append(series)
        return all_series

    def get_book_series_by_id(self, series_id: int) -> Optional[BookSuit]:
        """获取单个书籍系列的详细信息，现在会包含所有分卷。"""
        return self.book_suit_interpreter.interpret(series_id)

    def get_book_series_as_markdown(self, series_id: int) -> Optional[str]:
        """获取单个书籍系列的完整Markdown文档，包括所有分卷内容。"""
        book_suit = self.get_book_series_by_id(series_id)
        if not book_suit:
            return None
        return self.formatter.format_book_series(book_suit)

    def _get_all_book_materials(self) -> List[Material]:
        """获取所有被识别为“书籍”的完整物料对象列表。"""
        books = []
        all_material_ids = self.material_interpreter.get_all_material_ids()
        for mid in all_material_ids:
            material = self.material_interpreter.interpret(mid)
            if material and material.is_book:
                books.append(material)
        return books

    def get_tree(self) -> List[Dict[str, Any]]:
        """获取书籍的树状结构图 (书籍系列 -> 书籍)。"""
        all_series = self.list_book_series()
        all_books = self._get_all_book_materials()
        
        series_map: Dict[int, List[Material]] = {s.id: [] for s in all_series}
        orphan_books: List[Material] = []
        
        for book in all_books:
            if book.set_id and book.set_id in series_map:
                series_map[book.set_id].append(book)
            else:
                orphan_books.append(book)
        
        result_tree = []
        for series in sorted(all_series, key=lambda s: s.id):
            # 只显示有书的系列
            if not series_map.get(series.id):
                continue

            series_node = {
                "id": series.id,
                "title": series.name,
                "children": sorted(
                    [{"id": b.id, "title": b.name} for b in series_map[series.id]],
                    key=lambda x: x['id']
                )
            }
            result_tree.append(series_node)
            
        if orphan_books:
            orphan_node = {
                "id": "ORPHAN_BOOKS",
                "title": "零散书籍",
                "children": sorted(
                    [{"id": b.id, "title": b.name} for b in orphan_books],
                    key=lambda x: x['id']
                )
            }
            result_tree.append(orphan_node)
            
        return result_tree