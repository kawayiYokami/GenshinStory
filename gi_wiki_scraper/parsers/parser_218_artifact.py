"""
Parser for Genshin Impact wiki pages under the 'Artifact' (圣遗物) category.
ID: 218_artifact
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser218Artifact(BaseParser):
    """
    Specific parser for 'Artifact' wiki pages.
    Extracts artifact details including set name, type, basic info, artifact list, and pairing recommendations.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of an artifact page.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)

        # Initialize the result dictionary with default values
        result = {
            "套装名称": "",
            "类型": "圣遗物套装",  # Default type based on the sample
            "基础信息": {
                "稀有度": "",
                "获取途径": [],
                "2件套效果": "",
                "4件套效果": ""
            },
            "圣遗物列表": {},
            "搭配推荐": {
                "角色推荐": [],
                "成长数据链接": ""
            }
        }

        # 1. Extract artifact set name
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["套装名称"] = name_tag.get_text(strip=True)

        # 2. Extract basic information
        self._extract_basic_info(soup, result)

        # 3. Extract artifact list
        self._extract_artifact_list(soup, result)

        # 4. Extract pairing recommendations
        self._extract_pairing_recommendations(soup, result)

        return result

    def _extract_basic_info(self, soup, result: Dict[str, Any]) -> None:
        """Extract basic artifact information."""
        # Find the rich base info table
        info_table = soup.select_one('.obc-tmpl-richBaseInfo table')
        if not info_table:
            return

        rows = info_table.select('tbody tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                key_cell = cells[0]
                value_cell = cells[1]

                key = key_cell.get_text(strip=True)
                value = value_cell.get_text(strip=True)

                # Map keys to result structure
                if "稀有度" in key:
                    result["基础信息"]["稀有度"] = value
                elif "获取途径" in key:
                    # Extract acquisition methods
                    method_tags = value_cell.select('p')
                    for tag in method_tags:
                        text = tag.get_text(strip=True)
                        if text:
                            result["基础信息"]["获取途径"].append(text)
                elif "2件套效果" in key:
                    result["基础信息"]["2件套效果"] = value
                elif "4件套效果" in key:
                    result["基础信息"]["4件套效果"] = value

    def _extract_artifact_list(self, soup, result: Dict[str, Any]) -> None:
        """Extract artifact list information."""
        # Find all artifact list tables
        artifact_tables = soup.select('.obc-tmpl-artifactListV2')

        for table in artifact_tables:
            # Extract artifact part type from label
            label_tag = table.select_one('label')
            if not label_tag:
                continue

            part_type_text = label_tag.get_text(strip=True)
            # Remove the colon at the end
            part_type = part_type_text.rstrip('：')

            # Initialize artifact info
            artifact_info = {
                "名称": "",
                "描述": "",
                "故事": ""
            }

            # Extract name
            name_tag = table.select_one('span')
            if name_tag:
                artifact_info["名称"] = name_tag.get_text(strip=True)

            # Extract description
            desc_tag = table.select_one('p:contains("描述：")')
            if desc_tag:
                # Get text after "描述："
                desc_text = desc_tag.get_text(strip=True)
                if "：" in desc_text:
                    artifact_info["描述"] = desc_text.split("：", 1)[1].strip()

            # Extract story
            story_tags = table.select('.obc-tmpl-relic__story p')
            story_parts = []
            for tag in story_tags:
                text = tag.get_text(strip=True)
                if text:
                    story_parts.append(text)
            artifact_info["故事"] = "\n".join(story_parts)

            # Add to result
            result["圣遗物列表"][part_type] = artifact_info

    def _extract_pairing_recommendations(self, soup, result: Dict[str, Any]) -> None:
        """Extract pairing recommendations."""
        # Find the multi-table swiper
        swiper = soup.select_one('.obc-tmpl-multiTable .swiper-slide')
        if not swiper:
            return

        # Extract character recommendations (first slide)
        char_recommendations = []
        char_rows = swiper.select('table tbody tr')
        for row in char_rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                # Extract character name (this is a simplified approach)
                char_name = cells[0].get_text(strip=True)

                # Extract recommendation reason (this is a simplified approach)
                reason = cells[1].get_text(strip=True)

                # Extract affix pairing (this is a simplified approach)
                affix_pairing = {}
                if len(cells) >= 3:
                    affix_text = cells[2].get_text(strip=True)
                    # This would need more complex parsing to extract the specific affixes
                    # For now, we'll just store the text
                    affix_pairing["说明"] = affix_text

                char_recommendations.append({
                    "角色名称": char_name,
                    "推荐原因": reason,
                    "词缀搭配": affix_pairing
                })

        result["搭配推荐"]["角色推荐"] = char_recommendations

        # Extract growth data link (second slide)
        # This is a simplified approach - in reality, you'd need to handle the swiper pagination
        link_tag = swiper.select_one('a')
        if link_tag and link_tag.get('href'):
            result["搭配推荐"]["成长数据链接"] = link_tag['href']

    def get_template(self) -> Dict[str, Any]:
        """
        返回圣遗物解析器的JSON模板

        Returns:
            Dict[str, Any]: 圣遗物数据模板
        """
        return {
            "套装名称": "请填写套装名称",
            "类型": "圣遗物套装",
            "基础信息": {
                "稀有度": "请填写稀有度",
                "获取途径": [
                    "请填写获取途径1",
                    "请填写获取途径2"
                ],
                "2件套效果": "请填写2件套效果",
                "4件套效果": "请填写4件套效果"
            },
            "圣遗物列表": {
                "请填写圣遗物部位": {
                    "名称": "请填写圣遗物名称",
                    "描述": "请填写描述",
                    "故事": "请填写故事"
                }
            },
            "搭配推荐": {
                "角色推荐": [
                    {
                        "角色名称": "请填写角色名称",
                        "推荐原因": "请填写推荐原因",
                        "词缀搭配": {
                            "说明": "请填写词缀搭配说明"
                        }
                    }
                ],
                "成长数据链接": "请填写成长数据链接"
            }
        }