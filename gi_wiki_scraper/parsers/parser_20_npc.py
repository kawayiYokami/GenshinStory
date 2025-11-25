"""
Parser for Genshin Impact wiki pages under the 'NPC & Shop' (NPC&商店) category.
ID: 20_npc
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser20Npc(BaseParser):
    """
    Specific parser for 'NPC & Shop' wiki pages.
    Extracts NPC name, gender, location, and dialogue groups.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of an NPC page.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)

        result = {
            "名称": "",
            "性别": "",
            "位置": "",
            "对话组": []
        }

        # 1. Extract NPC name
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["名称"] = name_tag.get_text(strip=True)

        # 2. Extract basic information
        self._extract_basic_info(soup, result)

        # 3. Extract dialogue groups
        self._extract_dialogue_groups(soup, result)

        return result

    def _extract_basic_info(self, soup, result: Dict[str, Any]) -> None:
        """Extract basic NPC information."""
        gender_tag = soup.select_one('.obc-tmpl-npcBaseInfo table tbody td.wiki-h3:contains("性别") + td p')
        if gender_tag:
            result["性别"] = gender_tag.get_text(strip=True)

        location_tag = soup.select_one('.obc-tmpl-npcBaseInfo table tbody td.wiki-h3:contains("位置") + td p')
        if location_tag:
            result["位置"] = location_tag.get_text(strip=True)

    def _extract_dialogue_groups(self, soup, result: Dict[str, Any]) -> None:
        """Extract all dialogue groups."""
        dialogue_sections = soup.select('.obc-tmpl-interactiveDialogue')

        for section in dialogue_sections:
            title_tag = section.select_one('h2.wiki-h2')
            title = title_tag.get_text(strip=True) if title_tag else ""

            dialogues = []
            tree_nodes = section.select('.tree-node')

            for node in tree_nodes:
                option_tag = node.select_one('.option-content span')
                option = option_tag.get_text(strip=True) if option_tag else ""

                content_tags = node.select('.content-box ul li p')
                content = [tag.get_text(strip=True) for tag in content_tags if tag.get_text(strip=True)]

                if option or content:
                    dialogues.append({
                        "选项": option,
                        "内容": content
                    })

            if title or dialogues:
                result["对话组"].append({
                    "标题": title,
                    "对话": dialogues
                })

    def get_template(self) -> Dict[str, Any]:
        """
        返回NPC解析器的JSON模板

        Returns:
            Dict[str, Any]: NPC数据模板
        """
        return {
            "名称": "请填写NPC名称",
            "性别": "请填写性别",
            "位置": "请填写位置",
            "对话组": [
                {
                    "标题": "请填写对话组标题",
                    "对话": [
                        {
                            "选项": "请填写对话选项",
                            "内容": [
                                "请填写对话内容1",
                                "请填写对话内容2"
                            ]
                        }
                    ]
                }
            ]
        }