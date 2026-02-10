"""
Parser for Genshin Impact wiki pages under the 'Sumeru Rose' (空月之歌) category.
ID: 257_sumeru_rose
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser257SumeruRose(BaseParser):
    """
    Specific parser for 'Sumeru Rose' wiki pages.
    Extracts Sumeru Rose details including title, type, map overview, and map introductions.
    """
    
    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a Sumeru Rose page.
        
        Args:
            html (str): The full HTML content of the page.
            
        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)
        
        # Initialize the result dictionary with default values
        result = {
            "标题": "",
            "类型": "空月之歌",  # Default type based on the sample
            "地图总览": {
                "图片": "",
                "描述": ""
            },
            "地图介绍": []
        }
        
        # 1. Extract title
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["标题"] = name_tag.get_text(strip=True)
            
        # 2. Extract map overview
        self._extract_map_overview(soup, result)
        
        # 3. Extract map introductions
        self._extract_map_introductions(soup, result)
        
        return result
    
    def _extract_map_overview(self, soup, result: Dict[str, Any]) -> None:
        """Extract map overview."""
        # Find the map overview fold panel
        overview_panel = soup.select_one('.obc-tmpl-fold:contains("地图总览")')
        if not overview_panel:
            return
            
        # Extract image
        image_view = overview_panel.select_one('.custom-image-view')
        if image_view and image_view.get('data-image-url'):
            result["地图总览"]["图片"] = image_view['data-image-url']
            
        # Extract description from p tags
        desc_tags = overview_panel.select('.obc-tmpl__paragraph-box p')
        desc_parts = []
        for tag in desc_tags:
            text = tag.get_text(strip=True)
            if text:
                desc_parts.append(text)
        result["地图总览"]["描述"] = "\n".join(desc_parts)
        
    def _extract_map_introductions(self, soup, result: Dict[str, Any]) -> None:
        """Extract map introductions."""
        # Find the map introduction fold panel
        intro_panel = soup.select_one('.obc-tmpl-fold:contains("地图介绍") .obc-tmpl__paragraph-box')
        if not intro_panel:
            return
            
        # Extract region headings (h1)
        region_headings = intro_panel.select('h1.custom-heading-cls')
        
        for i, heading in enumerate(region_headings):
            region = {
                "区域标题": "",
                "副标题": "",
                "图片": [],
                "描述": ""
            }
            
            # Extract region title
            region["区域标题"] = heading.get_text(strip=True)
            
            # Extract subtitle from blockquote
            subtitle_tag = heading.find_next('blockquote')
            if subtitle_tag:
                strong_tag = subtitle_tag.select_one('p strong')
                if strong_tag:
                    region["副标题"] = strong_tag.get_text(strip=True)
                    
            # Extract images
            # Find all image views between this heading and the next heading (or end of panel)
            next_heading = heading.find_next('h1') if i < len(region_headings) - 1 else None
            current_element = heading.find_next_sibling()
            while current_element and current_element != next_heading:
                if current_element.name == 'div' and 'custom-image-view' in current_element.get('class', []):
                    if current_element.get('data-image-url'):
                        region["图片"].append(current_element['data-image-url'])
                current_element = current_element.find_next_sibling()
                
            # Extract description from p tags
            # Find all p tags between this heading and the next heading (or end of panel)
            desc_tags = []
            current_element = heading.find_next_sibling()
            while current_element and current_element != next_heading:
                if current_element.name == 'p':
                    desc_tags.append(current_element)
                current_element = current_element.find_next_sibling()
                
            desc_parts = []
            for tag in desc_tags:
                text = tag.get_text(strip=True)
                if text:
                    desc_parts.append(text)
            region["描述"] = "\n".join(desc_parts)
            
            # Add to map introductions list if region title is not empty
            if region["区域标题"]:
                result["地图介绍"].append(region)
                
    def _extract_images(self, soup, result: Dict[str, Any]) -> None:
        """Extract images."""
        # Find all image sources in the map description section
        img_sources = soup.select('.obc-tmpl-mapDesc .swiper-slide picture source')
        
        for img_source in img_sources:
            if img_source.get('srcset'):
                result["图片"].append(img_source['srcset'])