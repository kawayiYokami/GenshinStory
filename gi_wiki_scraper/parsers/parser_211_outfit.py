"""
Parser for Genshin Impact wiki pages under the 'Outfit' (装扮) category.
ID: 211_outfit
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser211Outfit(BaseParser):
    """
    Specific parser for 'Outfit' wiki pages.
    Extracts outfit name and story.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of an outfit page.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)

        result = {
            "名称": "",
            "简介": "",
            "故事": ""
        }

        # 1. Extract outfit name
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["名称"] = name_tag.get_text(strip=True)

        # 2. Extract introduction and story from fold panels
        self._extract_fold_content(soup, result)

        return result

    def _extract_fold_content(self, soup, result: Dict[str, Any]) -> None:
        """Extract introduction and story from fold panels."""
        fold_sections = soup.select('.obc-tmpl-fold')

        for section in fold_sections:
            title_tag = section.select_one('.obc-tmpl-fold__title span')
            if not title_tag:
                continue

            title_text = title_tag.get_text(strip=True)

            # Extract content from paragraph box
            content_tags = section.select('.obc-tmpl__paragraph-box p')
            content_parts = []
            for tag in content_tags:
                text = tag.get_text(strip=True)
                if text:
                    content_parts.append(text)
            content = "".join(content_parts)

            # Determine content type based on title
            if "简介" in title_text or "衣装简介" in title_text:
                result["简介"] = content
            elif "故事" in title_text or "衣装故事" in title_text or "风之翼故事" in title_text:
                result["故事"] = content

    def get_template(self) -> Dict[str, Any]:
        """
        返回装扮解析器的JSON模板

        Returns:
            Dict[str, Any]: 装扮数据模板
        """
        return {
            "名称": "请填写装扮名称",
            "简介": "请填写装扮简介",
            "故事": "请填写装扮故事"
        }