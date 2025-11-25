"""
Parser for Genshin Impact wiki pages under the 'Enemy' (敌人) category.
ID: 6_enemy
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser6Enemy(BaseParser):
    """
    Specific parser for 'Enemy' wiki pages.
    Extracts enemy details including title, element, attack methods, drops, strategy, background story, data reference, distribution map, and images.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of an enemy page.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)

        # 1. Extract the main title
        title_tag = soup.find('h1', class_='detail__title')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

        # 2. Extract element
        element = ""
        element_tag = soup.select_one('.obc-tmpl-monsterBaseInfo table td:contains("元素") + td p')
        if element_tag:
            element = element_tag.get_text(strip=True)

        # 3. Extract attack methods
        attack_methods = []
        attack_methods_tag = soup.select_one('.obc-tmpl-monsterBaseInfo table td:contains("攻击方式") + td p')
        if attack_methods_tag:
            attack_methods_text = attack_methods_tag.get_text(strip=True)
            # Split by comma or newline
            attack_methods = [method.strip() for method in attack_methods_text.replace('\n', ',').split(',') if method.strip()]

        # 4. Extract drops
        drops = []
        drop_tags = soup.select('.obc-tmpl-monsterBaseInfo .obc-tmpl__material-name')
        for tag in drop_tags:
            drop_name = tag.get_text(strip=True)
            if drop_name:
                drops.append(drop_name)

        # 5. Extract strategy
        strategy_parts = []
        strategy_tags = soup.select('.obc-tmpl-fold:contains("攻略方法") .obc-tmpl__paragraph-box')
        for tag in strategy_tags:
            text = tag.get_text(strip=True)
            if text:
                strategy_parts.append(text)
        strategy = "\n".join(strategy_parts)

        # 6. Extract background story
        background_story_parts = []
        story_tags = soup.select('.obc-tmpl-goodDesc table .obc-tmpl__rich-text p')
        for tag in story_tags:
            text = tag.get_text(strip=True)
            if text:
                background_story_parts.append(text)
        background_story = "\n".join(background_story_parts)

        # 7. Extract data reference
        data_reference = {
            "hp_world8": "",
            "hp_world9": "",
            "hp_spiral": "",
            "resistances": ""
        }

        # Extract HP and resistance data
        data_rows = soup.select('.obc-tmpl-equipmentGrowthInfo table tbody tr')
        for row in data_rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                # Assuming the structure: World Level, HP, Resistances
                world_level = cells[0].get_text(strip=True)
                hp = cells[1].get_text(strip=True)
                resistances = cells[2].get_text(strip=True)

                if "8" in world_level:
                    data_reference["hp_world8"] = hp
                elif "9" in world_level:
                    data_reference["hp_world9"] = hp

                # For spiral abyss, we might need a different selector or logic
                # This is a simplified approach - in reality, you might need to check more specific conditions
                if "深渊" in world_level:
                    data_reference["hp_spiral"] = hp

                # Update resistances (this might need refinement based on actual HTML structure)
                if resistances:
                    data_reference["resistances"] = resistances

        # 8. Extract distribution map
        distribution_map = ""
        map_tag = soup.select_one('.wiki-map-card')
        if map_tag:
            # Try to get href first, then iframe src
            if map_tag.get('href'):
                distribution_map = map_tag['href']
            else:
                iframe_tag = map_tag.select_one('iframe')
                if iframe_tag and iframe_tag.get('src'):
                    distribution_map = iframe_tag['src']

        # 9. Extract images
        images = []
        img_tags = soup.select('.obc-tmpl-monsterBaseInfo .swiper-slide picture source')
        for img_tag in img_tags:
            if img_tag.get('srcset'):
                images.append(img_tag['srcset'])

        # Assemble final data structure
        return {
            "title": title,
            "element": element,
            "attack_methods": attack_methods,
            "drops": drops,
            "strategy": strategy,
            "background_story": background_story,
            "data_reference": data_reference,
            "distribution_map": distribution_map,
            "images": images
        }

    def get_template(self) -> Dict[str, Any]:
        """
        返回敌人解析器的JSON模板

        Returns:
            Dict[str, Any]: 敌人数据模板
        """
        return {
            "title": "请填写敌人名称",
            "element": "请填写元素属性",
            "attack_methods": [
                "请填写攻击方式1",
                "请填写攻击方式2"
            ],
            "drops": [
                "请填写掉落物1",
                "请填写掉落物2"
            ],
            "strategy": "请填写攻略方法",
            "background_story": "请填写背景故事",
            "data_reference": {
                "hp_world8": "请填写世界等级8的HP",
                "hp_world9": "请填写世界等级9的HP",
                "hp_spiral": "请填写深境螺旋的HP",
                "resistances": "请填写抗性信息"
            },
            "distribution_map": "请填写分布地图链接",
            "images": [
                "请填写图片链接1",
                "请填写图片链接2"
            ]
        }