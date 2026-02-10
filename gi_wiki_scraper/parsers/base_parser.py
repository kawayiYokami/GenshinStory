"""
Base class for all wiki page parsers.
Defines the common interface that all specific parsers must implement.
"""

from abc import ABC, abstractmethod
from bs4 import BeautifulSoup


class BaseParser(ABC):
    """
    Abstract base class for parsing wiki pages.
    All specific parser classes should inherit from this class and implement the `parse` method.
    """

    @abstractmethod
    def parse(self, html: str) -> dict:
        """
        Parses the given HTML content and returns structured data.

        Args:
            html (str): The full HTML content of the wiki page, after all sections are expanded.

        Returns:
            dict: A dictionary containing the structured data extracted from the page.
                  The structure of this dictionary will vary depending on the specific parser.
        """
        pass

    @abstractmethod
    def get_template(self) -> dict:
        """
        返回该解析器的JSON模板结构，包含中文占位符

        Returns:
            dict: 包含默认值和占位符的模板字典
        """
        pass

    def _create_soup(self, html: str) -> BeautifulSoup:
        """
        Helper method to create a BeautifulSoup object from HTML string.
        Uses 'html.parser' as the default parser.

        Args:
            html (str): The HTML content to parse.

        Returns:
            BeautifulSoup: A BeautifulSoup object representing the parsed HTML.
        """
        return BeautifulSoup(html, 'html.parser')

    def _safe_int(self, text: str, default: int = 0) -> int:
        """
        Safely converts text to integer, handling common wiki formatting issues.

        Args:
            text (str): The text to convert to integer.
            default (int): The default value to return if conversion fails.

        Returns:
            int: The converted integer value or default if conversion fails.
        """
        if not text:
            return default

        # Strip whitespace
        text = text.strip()

        # Remove common prefixes like '*', '+', '-' at the beginning
        if text.startswith(('*', '+', '-')):
            text = text[1:].strip()

        # Remove common suffixes like '%', 'x', '倍'
        text = text.rstrip('%x倍')

        # Remove commas for large numbers
        text = text.replace(',', '')

        try:
            return int(text)
        except ValueError:
            # Try to extract just the numeric part
            import re
            numbers = re.findall(r'\d+', text)
            if numbers:
                try:
                    return int(numbers[0])
                except ValueError:
                    pass
            return default