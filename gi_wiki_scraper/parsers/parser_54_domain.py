"""
Parser for Genshin Impact wiki pages under the 'Domain' (秘境) category.
ID: 54_domain
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser54Domain(BaseParser):
    """
    Specific parser for 'Domain' wiki pages.
    Extracts domain name and brief descriptions.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a domain page.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)

        result = {
            "名称": "",
            "简述": []
        }

        # 1. Extract domain name
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["名称"] = name_tag.get_text(strip=True)

        # 2. Extract brief descriptions
        self._extract_brief(soup, result)

        return result

    def _extract_brief(self, soup, result: Dict[str, Any]) -> None:
        """Extract brief descriptions from swiper slides."""
        brief_section = soup.select_one('.obc-tmpl-multiTable')
        if brief_section:
            slides = brief_section.select('.swiper-slide')
            bullets = brief_section.select('.swiper-pagination-bullet')

            for i, slide in enumerate(slides):
                name = bullets[i].get_text(strip=True) if i < len(bullets) else ""
                desc_tag = slide.select_one('table td p')
                desc = desc_tag.get_text(strip=True) if desc_tag else ""

                if name or desc:
                    result["简述"].append({
                        "名称": name,
                        "描述": desc
                    })

    def get_template(self) -> Dict[str, Any]:
        """
        返回秘境解析器的JSON模板

        Returns:
            Dict[str, Any]: 秘境数据模板
        """
        return {
            "名称": "请填写秘境名称",
            "简述": [
                {
                    "名称": "请填写简述名称",
                    "描述": "请填写简述描述"
                }
            ]
        }