"""
Parser for Genshin Impact wiki pages under the 'Namecard' (名片) category.
ID: 109_namecard
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser109Namecard(BaseParser):
    """
    Specific parser for 'Namecard' wiki pages.
    Extracts namecard details including name, type, icon image, and full image.
    """
    
    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a namecard page.
        
        Args:
            html (str): The full HTML content of the page.
            
        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)
        
        # Initialize the result dictionary with default values
        result = {
            "名称": "",
            "类型": "名片",  # Default type based on the sample
            "图标图片": "",
            "完整图片": ""
        }
        
        # 1. Extract namecard name
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["名称"] = name_tag.get_text(strip=True)
            
        # 2. Extract namecard images
        self._extract_images(soup, result)
        
        return result
    
    def _extract_images(self, soup, result: Dict[str, Any]) -> None:
        """Extract namecard images."""
        # Find all image sources in the business card section
        img_sources = soup.select('.obc-tmpl-businessCard .business-card-image picture source')
        
        # Extract icon image (first image)
        if len(img_sources) >= 1:
            icon_img = img_sources[0]
            if icon_img.get('srcset'):
                result["图标图片"] = icon_img['srcset']
                
        # Extract full image (second image)
        if len(img_sources) >= 2:
            full_img = img_sources[1]
            if full_img.get('srcset'):
                result["完整图片"] = full_img['srcset']