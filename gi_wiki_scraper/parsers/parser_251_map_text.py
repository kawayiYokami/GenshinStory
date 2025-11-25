"""
Parser for Genshin Impact wiki pages under the 'Map Text' (地图文本) category.
ID: 251_map_text
"""
from typing import Dict, Any, List
import re
from .base_parser import BaseParser


class Parser251MapText(BaseParser):
    """
    Specific parser for 'Map Text' wiki pages.
    Extracts map text details including title, type, region, location images, and text content.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a map text page.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)

        # Initialize the result dictionary with default values
        result = {
            "文本标题": "",
            "类型": "地图文本",  # Default type based on the sample
            "地区": "",
            "文本内容": []
        }

        # 1. Extract map text title and region
        self._extract_title_and_region(soup, result)

        # 2. Extract text content
        self._extract_text_content(soup, result)

        # 3. Extract location images
        self._extract_location_images(soup, result)

        return result

    def _extract_title_and_region(self, soup, result: Dict[str, Any]) -> None:
        """Extract map text title and region."""
        title_tag = soup.select_one('h1.detail__title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            result["文本标题"] = title

            # Extract region from title using regex
            # Look for text within brackets like 【采樵谷】
            region_matches = re.findall(r'【([^】]+)】', title)
            # According to the guide, "地区" should be a string, not a list
            # So we take the first match if it exists
            if region_matches:
                result["地区"] = region_matches[0]

    def _extract_text_content(self, soup, result: Dict[str, Any]) -> None:
        """Extract text content."""
        # Find all content paragraphs in the interactive dialogue section
        content_paragraphs = soup.select('.obc-tmpl-interactiveDialogue .content-box p')

        for p_tag in content_paragraphs:
            text = p_tag.get_text(strip=True)
            # Skip empty paragraphs and image placeholders
            if text and not text.startswith('span'):
                result["文本内容"].append(text)

    def _extract_location_images(self, soup, result: Dict[str, Any]) -> None:
        """Extract location images - 仅解析但不输出"""
        # Find all image sources in the map description section
        img_sources = soup.select('.obc-tmpl-mapDesc .swiper-slide picture source')

        # 解析图片但不存储到结果中
        for img_source in img_sources:
            if img_source.get('srcset'):
                # 解析完成但不添加到result
                pass

    def get_template(self) -> Dict[str, Any]:
        """
        返回地图文本解析器的JSON模板

        Returns:
            Dict[str, Any]: 地图文本数据模板
        """
        return {
            "文本标题": "请填写文本标题",
            "类型": "地图文本",
            "地区": "请填写地区",
            "文本内容": [
                "请填写文本内容1",
                "请填写文本内容2"
            ]
        }