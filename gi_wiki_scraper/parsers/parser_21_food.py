"""
Parser for Genshin Impact wiki pages under the 'Food' (食物) category.
ID: 21_food
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser21Food(BaseParser):
    """
    Specific parser for 'Food' wiki pages.
    Extracts food details including title and variations (Strange, Normal, Delicious) with their ingredients, descriptions, effects, etc.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a food page using simple and robust extraction.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)

        # 1. Extract the main food title
        title_tag = soup.find('h1', class_='detail__title')
        food_name = title_tag.get_text(strip=True) if title_tag else "Unknown Food"

        # 2. Extract all quality variations by finding name-description pairs
        variations = []

        # Find all elements containing "名称："
        name_elements = soup.find_all(text=lambda text: text and "名称：" in text)

        for name_element in name_elements:
            # Get the parent element and try to find the name value
            parent = name_element.parent
            if parent:
                # Look for the next sibling or nearby element containing the actual name
                name_value = ""

                # Try different approaches to find the name value
                next_sibling = parent.find_next_sibling()
                if next_sibling:
                    name_value = next_sibling.get_text(strip=True)
                else:
                    # Try to find within the same parent structure
                    parent_container = parent.parent
                    if parent_container:
                        divs = parent_container.find_all('div')
                        for i, div in enumerate(divs):
                            if div.get_text(strip=True) == "名称：" and i + 1 < len(divs):
                                name_value = divs[i + 1].get_text(strip=True)
                                break

                if name_value:
                    # Now look for the corresponding description
                    description = ""

                    # Search for "描述：" in the vicinity
                    container = parent.find_parent()
                    while container and not description:
                        desc_elements = container.find_all(text=lambda text: text and "描述：" in text)
                        for desc_element in desc_elements:
                            desc_parent = desc_element.parent
                            if desc_parent:
                                # Try to find the description value
                                desc_container = desc_parent.parent
                                if desc_container:
                                    # Look for <p> tags or similar containing the description
                                    desc_p = desc_container.find('p')
                                    if desc_p:
                                        description = desc_p.get_text(strip=True)
                                        break

                        # Move up one level if not found
                        container = container.parent
                        if not container or container.name == 'html':
                            break

                    # Add the variation if we found both name and description
                    if name_value and description:
                        # Filter out content in parentheses (player-added notes)
                        cleaned_description = self._clean_description(description)
                        variations.append({
                            "名称": name_value,
                            "描述": cleaned_description
                        })

        # Assemble final data structure
        return {
            "食物名称": food_name,
            "品质变体": variations
        }

    def _clean_description(self, description: str) -> str:
        """
        Clean description by removing content in parentheses (player-added notes).

        Args:
            description (str): Original description text

        Returns:
            str: Cleaned description without parenthetical content
        """
        import re

        # Remove content in both Chinese and English parentheses
        # Patterns to match: (content), （content）, [content], 【content】
        patterns = [
            r'\([^)]*\)',      # English parentheses
            r'（[^）]*）',      # Chinese parentheses
            r'\[[^\]]*\]',     # English square brackets
            r'【[^】]*】'       # Chinese square brackets
        ]

        cleaned = description
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned)

        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned

    def get_template(self) -> Dict[str, Any]:
        """
        返回食物解析器的JSON模板

        Returns:
            Dict[str, Any]: 食物数据模板
        """
        return {
            "食物名称": "请填写食物名称",
            "品质变体": [
                {
                    "名称": "请填写品质变体名称（如：奇怪的、普通的、美味的）",
                    "描述": "请填写描述"
                }
            ]
        }