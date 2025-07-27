from typing import List

from ..models.book import Book
from ..services import DataLoader, TextMapService

class BookInterpreter:
    """
    Interprets book data from LocalbookConfig.json, turning it into a list of Book objects.
    """
    def __init__(self, loader: DataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map_service = text_map_service

    def interpret_all(self) -> List[Book]:
        """
        Parses the book config file and returns a list of Book objects.
        """
        books = []
        book_config_data = self.loader.get_json("LocalbookConfig.json")
        if not book_config_data:
            return books

        for book_info in book_config_data:
            book_id = book_info.get("BookID")
            name_hash = book_info.get("BookInsideName", {}).get("Hash")
            content_hash = book_info.get("BookContent", {}).get("Hash")
            series_id = book_info.get("BookSeriesID")

            if not all([book_id, name_hash, content_hash, series_id]):
                continue

            name = self.text_map_service.get(str(name_hash))
            content = self.text_map_service.get(str(content_hash))

            if name and content:
                books.append(Book(
                    id=book_id,
                    name=name,
                    content=content,
                    series_id=series_id
                ))
        
        return books