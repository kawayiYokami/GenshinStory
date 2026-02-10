import logging
from typing import List
from pydantic import ValidationError

from hsrwiki_data_parser.models.book import Book
from hsrwiki_data_parser.services.dataloader import DataLoader
from hsrwiki_data_parser.models._core import GlobalTagManager

class BookInterpreter:
    def __init__(self, loader: DataLoader):
        self.loader = loader

    def interpret_all(self) -> List[Book]:
        """Loads, validates, and interprets all book data."""
        books = []
        raw_data_iterator = self.loader.get_books()

        for data in raw_data_iterator:
            try:
                # The source_url is not in the model, so we pop it.
                data.pop('source_url', None)
                book = Book(**data)
                # 手动加载标签
                if book.id:
                    book.tags = GlobalTagManager.get_tags(str(book.id))
                books.append(book)
            except ValidationError as e:
                logging.error(f"Validation error for book with id {data.get('id', 'N/A')}: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for book id {data.get('id', 'N/A')}: {e}")

        logging.info(f"Successfully interpreted {len(books)} books.")
        return books
