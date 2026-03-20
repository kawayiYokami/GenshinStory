"""
Parser for Genshin Impact wiki pages under the 'Animal' (动物) category.
ID: 49_animal
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser49Animal(BaseParser):
    """
    Specific parser for 'Animal' wiki pages.
    Extracts animal details including name, strategy, drops, background story, notes, and images.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of an animal page.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)

        # Initialize the result dictionary with default values
        result = {
            "名称": "",
            "攻略方法": "",
            "掉落物品": [],
            "背景故事": "",
            "备注": "",
            "images": []
        }

        # 1. Extract animal name
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["名称"] = name_tag.get_text(strip=True)

        # 2. Extract basic information
        self._extract_basic_info(soup, result)

        # 3. Extract drop items
        self._extract_drop_items(soup, result)

        # 4. Extract background story and notes
        self._extract_background_story(soup, result)

        # 5. Extract images
        self._extract_images(soup, result)

        return result

    def _extract_basic_info(self, soup, result: Dict[str, Any]) -> None:
        """Extract basic animal information."""
        # Extract strategy
        strategy_tag = soup.select_one('td:contains("攻略方法") + td .obc-tmpl__rich-text p')
        if strategy_tag:
            result["攻略方法"] = strategy_tag.get_text(strip=True)

    def _extract_drop_items(self, soup, result: Dict[str, Any]) -> None:
        """Extract drop items information."""
        drop_items = soup.select('td:contains("掉落物品") + td .obc-tmpl__material .obc-tmpl__material-item')
        for item in drop_items:
            name_tag = item.select_one('.obc-tmpl__material-name')
            link_tag = item.select_one('a.obc-tmpl__material-href')

            name = name_tag.get_text(strip=True) if name_tag else ""
            link = link_tag['href'] if link_tag and link_tag.get('href') else ""

            if name:
                result["掉落物品"].append({
                    "名称": name,
                    "链接": link
                })

    def _extract_background_story(self, soup, result: Dict[str, Any]) -> None:
        """Extract background story and notes."""
        # Extract background story
        story_tags = soup.select('.obc-tmpl-goodDesc table tbody td.obc-tmpl__rich-text p')
        story_parts = []
        for tag in story_tags:
            text = tag.get_text(strip=True)
            if text:
                story_parts.append(text)
        result["背景故事"] = "\n".join(story_parts)

        # Extract notes
        note_tags = soup.select('.obc-tmpl-goodDesc table tbody .obc-color-td p')
        note_parts = []
        for tag in note_tags:
            text = tag.get_text(strip=True)
            if text and "备注：" in text:
                # Remove the "备注：" prefix
                note_text = text.replace("备注：", "").strip()
                note_parts.append(note_text)
        result["备注"] = "\n".join(note_parts)

    def _extract_images(self, soup, result: Dict[str, Any]) -> None:
        """Extract images."""
        img_tags = soup.select('.obc-tmpl-monsterBaseInfo .swiper-slide picture source')
        for img_tag in img_tags:
            if img_tag.get('srcset'):
                result["images"].append(img_tag['srcset'])

    def get_template(self) -> Dict[str, Any]:
        """
        返回动物解析器的JSON模板

        Returns:
            Dict[str, Any]: 动物数据模板
        """
        return {
            "名称": "请填写动物名称",
            "攻略方法": "请填写攻略方法",
            "掉落物品": [
                {
                    "名称": "请填写掉落物品名称",
                    "链接": "请填写物品链接"
                }
            ],
            "背景故事": "请填写背景故事",
            "备注": "请填写备注信息",
            "images": [
                "请填写图片链接"
            ]
        }