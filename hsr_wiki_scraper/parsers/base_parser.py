from abc import ABC, abstractmethod
from bs4 import BeautifulSoup

class BaseParser(ABC):
    """
    所有页面解析器的抽象基类。
    每个具体的解析器都必须继承此类并实现 parse 方法。
    """

    @abstractmethod
    def parse(self, html: str) -> dict:
        """
        解析给定的HTML内容，并返回结构化的数据字典。

        Args:
            html (str): 已完全加载和交互后的页面HTML内容。

        Returns:
            dict: 包含解析出的结构化数据的字典。
                  如果解析失败，应返回一个空字典 {} 或包含错误信息的字典。
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