"""
Parser for Genshin Impact wiki pages under the 'Book' (书籍) category.
ID: 68_book
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser68Book(BaseParser):
    """
    Specific parser for 'Book' wiki pages.
    Extracts book details including title, type, and chapter list with content.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a book page.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)

        # Initialize the result dictionary with default values
        result = {
            "书名": "",
            "类型": "书籍",  # Default type based on the sample
            "章节列表": []
        }

        # 1. Extract book title
        title_tag = soup.select_one('h1.detail__title')
        if title_tag:
            result["书名"] = title_tag.get_text(strip=True)

        # 2. Extract chapters
        self._extract_chapters(soup, result)

        return result

    def _extract_chapters(self, soup, result: Dict[str, Any]) -> None:
        """Extract chapter information."""
        # Find all book modules, each representing a chapter
        chapter_modules = soup.select('.obc-tmpl-module')

        for module in chapter_modules:
            chapter = {
                "章节标题": "",
                "名称": "",
                "星级": 0,
                "获得方式": "",
                "描述": "",
                "内容": ""
            }

            # Extract chapter title
            title_tag = module.select_one('.obc-tmpl-fold__title span')
            if title_tag:
                chapter["章节标题"] = title_tag.get_text(strip=True)
                chapter["名称"] = chapter["章节标题"]  # Based on the sample, these are the same

            # Extract basic information from the material base info table
            base_info_table = module.select_one('.obc-tmpl-materialBaseInfo')
            if base_info_table:
                # Extract name
                name_tag = base_info_table.select_one('td.material-td > div > div')
                if name_tag:
                    chapter["名称"] = name_tag.get_text(strip=True)

                # Extract rarity
                rarity_icons = base_info_table.select('.obc-tmpl__rate-icon')
                chapter["星级"] = len(rarity_icons)

                # Extract acquisition method
                acquire_tag = base_info_table.select_one('label:contains("获得方式") + .material-value-wrap p')
                if acquire_tag:
                    chapter["获得方式"] = acquire_tag.get_text(strip=True)

                # Extract description
                desc_tag = base_info_table.select_one('label:contains("描述") + .material-value-wrap-full p')
                if desc_tag:
                    chapter["描述"] = desc_tag.get_text(strip=True)

            # Extract content
            content_tags = module.select('.obc-tmpl__paragraph-box p')
            content_parts = []
            for tag in content_tags:
                text = tag.get_text(strip=True)
                if text:
                    content_parts.append(text)
            chapter["内容"] = "\n".join(content_parts)

            # Add chapter to the list if it has a title
            if chapter["章节标题"]:
                result["章节列表"].append(chapter)

    def get_template(self) -> Dict[str, Any]:
        """
        返回书籍解析器的JSON模板

        Returns:
            Dict[str, Any]: 书籍数据模板
        """
        return {
            "书名": "请填写书名",
            "类型": "书籍",
            "章节列表": [
                {
                    "章节标题": "请填写章节标题",
                    "名称": "请填写章节名称",
                    "星级": 1,
                    "获得方式": "请填写获得方式",
                    "描述": "请填写描述",
                    "内容": "请填写章节内容"
                }
            ]
        }