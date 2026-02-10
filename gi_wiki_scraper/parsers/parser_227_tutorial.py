"""
Parser for Genshin Impact wiki pages under the 'Tutorial' (教程) category.
ID: 227_tutorial
"""

from typing import Dict, Any
from .base_parser import BaseParser


class Parser227Tutorial(BaseParser):
    """
    Specific parser for 'Tutorial' wiki pages.
    Extracts the main title and content modules (text and images).
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a tutorial page.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)

        # 1. Extract the main title
        title_tag = soup.find('h1', class_='detail__title')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

        # 2. Extract content modules
        modules_data = []
        content_modules = soup.find_all('div', class_='obc-tmpl-fold')

        for module in content_modules:
            module_title_tag = module.find('div', class_='obc-tmpl-fold__title')
            if not module_title_tag:
                continue

            module_title = module_title_tag.get_text(strip=True)

            # 3. Extract text paragraphs
            paragraphs = [
                p.get_text(strip=True)
                for p in module.select('.obc-tmpl__paragraph-box p')
                if p.get_text(strip=True)  # Filter out empty paragraphs
            ]

            # 4. Extract image URLs
            images = [
                img['data-image-url']
                for img in module.select('.custom-image-view[data-image-url]')
            ]

            # 5. Determine module type and add to list
            if images:
                modules_data.append({
                    "title": module_title,
                    "content_type": "images",
                    "data": images
                })
            elif paragraphs:
                modules_data.append({
                    "title": module_title,
                    "content_type": "text",
                    "data": paragraphs
                })

        # 6. Assemble final data structure
        return {
            "title": title,
            "modules": modules_data
        }