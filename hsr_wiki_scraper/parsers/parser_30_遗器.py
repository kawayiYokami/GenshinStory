from .base_parser import BaseParser
from bs4 import BeautifulSoup, Tag

class RelicParser(BaseParser):
    """
    用于解析“遗器”类型页面的解析器，专注于提取剧情故事。
    """

    def parse(self, html: str) -> dict:
        """
        解析给定的遗器页面URL，提取套装故事和部件故事。
        """

        soup = self._create_soup(html)

        title = self._parse_title(soup)
        set_effects = self._parse_set_effects(soup)
        pieces = self._parse_pieces(soup)

        return {
            "title": title,
            "set_effects": set_effects,
            "pieces": pieces
        }

    def _parse_title(self, soup: BeautifulSoup) -> str:
        """解析遗器套装名称"""
        title_tag = soup.select_one('h1.detail__title')
        return title_tag.get_text(strip=True) if title_tag else ""

    def _parse_set_effects(self, soup: BeautifulSoup) -> list:
        """解析套装效果，原文输出"""
        effects = []
        title_tag = soup.find('div', class_='title', string='套装效果')
        if title_tag:
            box = title_tag.find_parent('div', class_='obc-tmpl-relic__box')
            if box:
                story_tag = box.select_one('.obc-tmpl-relic__story p')
                if story_tag:
                    effects.append(story_tag.get_text(strip=True))
        return effects

    def _parse_pieces(self, soup: BeautifulSoup) -> list:
        """解析各部件故事，通过结构识别，不依赖关键字"""
        pieces = []
        # 遍历所有可能的部件容器
        for container in soup.select('.obc-tmpl__part--main[data-tmpl="heritage"]'):
            # 结构化识别：只有包含“来历”的容器才被认为是部件
            story_title_tag = container.find('div', class_='title', string='来历')
            if not story_title_tag:
                continue

            # 提取部件名称 (名称是<label>的下一个<span>)
            name_tag = container.select_one('label + span')
            if not name_tag:
                continue

            # 提取故事
            story = ""
            story_box = story_title_tag.find_next_sibling('div', class_='obc-tmpl-relic__box')
            if story_box:
                story_content = story_box.select_one('.obc-tmpl-relic__story')
                if story_content:
                    story = story_content.get_text(separator='\n', strip=True)

            pieces.append({
                "name": name_tag.get_text(strip=True),
                "story": story
            })
        return pieces

    def get_template(self) -> dict:
        """
        返回遗器解析器的JSON模板

        Returns:
            dict: 遗器数据模板
        """
        return {
            "title": "请填写遗器套装名称",
            "set_effects": [
                "请填写套装效果1",
                "请填写套装效果2"
            ],
            "pieces": [
                {
                    "name": "请填写部件名称",
                    "story": "请填写部件故事"
                }
            ]
        }
