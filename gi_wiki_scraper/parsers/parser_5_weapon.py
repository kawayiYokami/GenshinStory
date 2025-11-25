"""
Parser for Genshin Impact wiki pages under the 'Weapon' (武器) category.
ID: 5_weapon
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser5Weapon(BaseParser):
    """
    Specific parser for 'Weapon' wiki pages.
    Extracts weapon details including title, description, rarity, type, growth info, story, recommended roles, and display images.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a weapon page.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)

        # 1. Extract the main title
        title_tag = soup.find('h1', class_='detail__title')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

        # 2. Extract description
        description = ""
        desc_tag = soup.select_one('.obc-tmpl-goodDesc table .obc-tmpl__rich-text p')
        if desc_tag:
            description = desc_tag.get_text(strip=True)

        # 3. Extract base info (type and rarity)
        type_ = ""
        rarity = 0

        # Extract type
        type_tag = soup.select_one('.obc-tmpl-equipmentBaseInfo td:contains("装备类型") + td')
        if type_tag:
            type_ = type_tag.get_text(strip=True)

        # Extract rarity
        rarity_icons = soup.select('.obc-tmpl-equipmentBaseInfo .obc-tmpl__rate-icon')
        rarity = len(rarity_icons)

        # 4. Extract story - 只需要故事部分
        story_parts = []
        story_tags = soup.select('.obc-tmpl-fold .obc-tmpl__paragraph-box p')
        for tag in story_tags:
            text = tag.get_text(strip=True)
            if text:
                story_parts.append(text)
        story = "\n".join(story_parts)

        # 5. 解析成长数值和推荐角色（但不输出）
        growth_slides = soup.select('.obc-tmpl-equipmentGrowthInfo .swiper-slide')
        for slide in growth_slides:
            # 解析成长信息但不存储
            pass

        role_rows = soup.select('.obc-tmpl-multiTable tbody tr')
        for row in role_rows:
            # 解析推荐角色但不存储
            pass

        # 7. Extract display images - 仅解析但不输出
        img_tags = soup.select('.obc-tmpl-mapDesc picture source')
        for img_tag in img_tags:
            if img_tag.get('srcset'):
                # 解析完成但不存储
                pass

        # Assemble final data structure (只输出需要的字段)
        return {
            "title": title,
            "description": description,
            "rarity": rarity,
            "type": type_,
            "story": story
        }

    def get_template(self) -> Dict[str, Any]:
        """
        返回武器解析器的JSON模板

        Returns:
            Dict[str, Any]: 武器数据模板
        """
        return {
            "title": "请填写武器名称",
            "description": "请填写武器描述",
            "rarity": 5,
            "type": "请填写武器类型",
            "story": "请填写武器故事"
        }