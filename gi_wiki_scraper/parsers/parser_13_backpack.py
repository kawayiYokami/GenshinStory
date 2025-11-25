"""
Parser for Genshin Impact wiki pages under the 'Backpack' (背包) category.
ID: 13_backpack
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser13Backpack(BaseParser):
    """
    Specific parser for 'Backpack' wiki pages.
    Extracts backpack item details including title, description, obtain method, and exchange requirements.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a backpack item page.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)

        # 1. Extract the main title
        title_tag = soup.find('h1', class_='detail__title')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

        # 2. Extract name (this seems to be the same as title, but we'll follow the guide)
        name = title  # Default to title
        name_tag = soup.select_one('.obc-tmpl-materialBaseInfo .material-td div:contains("名称") + div')
        if name_tag:
            name = name_tag.get_text(strip=True)

        # 3. Extract obtain method
        obtain_method = []
        obtain_tags = soup.select('.obc-tmpl-materialBaseInfo .material label:contains("获取方式") + .material-value-wrap p')
        for tag in obtain_tags:
            method = tag.get_text(strip=True)
            if method:
                obtain_method.append(method)

        # 4. Extract description
        description_parts = []
        desc_tags = soup.select('.obc-tmpl-materialBaseInfo .material-td-inner label:contains("描述") + .material-value-wrap-full p')
        for tag in desc_tags:
            text = tag.get_text(strip=True)
            if text:
                description_parts.append(text)
        description = "\n".join(description_parts)

        # 5. Extract exchange requirements
        exchange_requirements = []
        requirement_rows = soup.select('.obc-tmpl-multiTable tbody tr')
        for row in requirement_rows:
            tds = row.find_all('td')
            if len(tds) >= 2:
                # Extract item name
                name = ""
                name_wrapper = tds[0].select_one('.custom-entry-wrapper')
                if name_wrapper and name_wrapper.get('data-entry-name'):
                    name = name_wrapper['data-entry-name']
                else:
                    name_tag = tds[0].select_one('.name')
                    if name_tag:
                        name = name_tag.get_text(strip=True)

                # Extract count
                count = 0
                count_tag = tds[1].select_one('p')
                if count_tag:
                    count_text = count_tag.get_text(strip=True)
                    # Try to extract a number from the text
                    try:
                        count = int(count_text)
                    except ValueError:
                        # If it's not a simple number, we might need more complex parsing
                        # For now, we'll just leave it as 0
                        pass

                if name:
                    exchange_requirements.append({
                        "name": name,
                        "count": count
                    })

        # 6. Extract usage
        usage_parts = []
        usage_tags = soup.select('.obc-tmpl-materialBaseInfo .material-td-inner label:contains("用途") + .material-value-wrap-full p')
        for tag in usage_tags:
            text = tag.get_text(strip=True)
            if text:
                usage_parts.append(text)
        usage = "\n".join(usage_parts)

        # Assemble final data structure
        return {
            "title": title,
            "description": description,
            "obtain_method": obtain_method,
            "exchange_requirements": exchange_requirements,
            "usage": usage
        }

    def get_template(self) -> Dict[str, Any]:
        """
        返回背包物品解析器的JSON模板

        Returns:
            Dict[str, Any]: 背包物品数据模板
        """
        return {
            "title": "请填写物品名称",
            "description": "请填写物品描述",
            "obtain_method": [
                "请填写获取方式1",
                "请填写获取方式2"
            ],
            "exchange_requirements": [
                {
                    "name": "请填写交换物品名称",
                    "count": 1
                }
            ],
            "usage": "请填写用途说明"
        }