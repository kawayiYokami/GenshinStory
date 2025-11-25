from .base_parser import BaseParser
from bs4 import BeautifulSoup

class ReadingMaterialParser(BaseParser):
    """
    用于解析“阅读物”类型页面的解析器。
    """

    def parse(self, html: str) -> dict:
        """
        解析给定的阅读物页面HTML，提取相关信息。
        """

        soup = self._create_soup(html)

        title = self._parse_title(soup)
        description = self._parse_description(soup)
        content = self._parse_content(soup)

        return {
            "title": title,
            "description": description,
            "content": content
        }

    def _parse_title(self, soup: BeautifulSoup) -> str:
        title_tag = soup.select_one('h1.detail__title')
        return title_tag.get_text(strip=True) if title_tag else ""

    def _parse_description(self, soup: BeautifulSoup) -> str:
        desc_tag = soup.select_one('.obc-tmpl__part--read .obc-tmpl__rich-text')
        return desc_tag.get_text(strip=True) if desc_tag else ""

    def _parse_content(self, soup: BeautifulSoup) -> list:
        content_parts = []
        for fold_part in soup.select('.obc-tmpl__part--fold'):
            heading_tag = fold_part.select_one('.obc-tmpl-fold__title')
            text_box = fold_part.select_one('.obc-tmpl__paragraph-box')

            heading = heading_tag.get_text(strip=True) if heading_tag else ""
            text = text_box.get_text(separator='\n', strip=True) if text_box else ""

            if heading or text:
                content_parts.append({
                    "heading": heading,
                    "text": text
                })
        return content_parts

    def get_template(self) -> dict:
        """
        返回阅读物解析器的JSON模板

        Returns:
            dict: 阅读物数据模板
        """
        return {
            "title": "请填写阅读物名称",
            "description": "请填写描述",
            "content": [
                {
                    "heading": "请填写标题",
                    "text": "请填写内容"
                }
            ]
        }
