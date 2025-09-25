"""
Parser for Genshin Impact wiki pages under the 'Teapot' (洞天) category.
ID: 130_teapot
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser130Teapot(BaseParser):
    """
    Specific parser for 'Teapot' wiki pages.
    Extracts teapot details including name, type, rarity, materials, description, attributes, and map info.
    """
    
    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a teapot page.
        
        Args:
            html (str): The full HTML content of the page.
            
        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)
        
        # Initialize the result dictionary with default values
        result = {
            "名称": "",
            "摆设名称": "",
            "类型": "洞天摆设",  # Default type based on the sample
            "星级": 0,
            "合成材料": "",
            "物品描述": {
                "描述": "",
                "获取途径": []
            },
            "基础属性": {
                "洞天仙力": 0,
                "摆放区域": "",
                "一级分类": "",
                "二级分类": "",
                "相关套装": ""
            },
            "地图说明": {
                "图片": []
            }
        }
        
        # 1. Extract teapot name
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["名称"] = name_tag.get_text(strip=True)
            
        # 2. Extract basic teapot information
        self._extract_basic_info(soup, result)
        
        # 3. Extract item description
        self._extract_item_description(soup, result)
        
        # 4. Extract base attributes
        self._extract_base_attributes(soup, result)
        
        # 5. Extract map descriptions
        self._extract_map_descriptions(soup, result)
        
        return result
    
    def _extract_basic_info(self, soup, result: Dict[str, Any]) -> None:
        """Extract basic teapot information."""
        # Extract decoration name
        name_tag = soup.select_one('label:contains("名称：")')
        if name_tag:
            # Get the parent td and extract text
            parent_td = name_tag.find_parent('td')
            if parent_td:
                # Get the text content, excluding the label itself
                text_parts = []
                for content in parent_td.contents:
                    if content != name_tag and hasattr(content, 'strip'):
                        text = content.strip()
                        if text:
                            text_parts.append(text)
                result["摆设名称"] = ''.join(text_parts).strip()
                
        # Extract rarity
        rarity_icons = soup.select('.obc-tmpl__rate-icon')
        result["星级"] = len(rarity_icons)
        
        # Extract crafting materials
        materials_tag = soup.select_one('label:contains("合成材料：") + span')
        if materials_tag:
            result["合成材料"] = materials_tag.get_text(strip=True)
            
    def _extract_item_description(self, soup, result: Dict[str, Any]) -> None:
        """Extract item description and acquisition methods."""
        # Extract all description paragraphs
        desc_section = soup.select_one('.obc-tmpl-goodDesc table tbody tr .obc-tmpl__rich-text')
        if desc_section:
            desc_paragraphs = desc_section.select('p')
            desc_parts = []
            for p in desc_paragraphs:
                text = p.get_text(strip=True)
                if text:
                    desc_parts.append(text)
            result["物品描述"]["描述"] = "\n".join(desc_parts)
            
        # Extract acquisition methods
        acquisition_section = soup.select_one('.obc-tmpl-goodDesc table tbody tr .obc-color-td')
        if acquisition_section:
            acquisition_tags = acquisition_section.select('p')
            for tag in acquisition_tags:
                text = tag.get_text(strip=True)
                if text and "获取途径" not in text:  # Skip the header
                    result["物品描述"]["获取途径"].append(text)
                
    def _extract_base_attributes(self, soup, result: Dict[str, Any]) -> None:
        """Extract base attributes."""
        # Find the rich base info table
        attr_rows = soup.select('.obc-tmpl-richBaseInfo table tbody tr')
        
        for row in attr_rows:
            # Extract attribute name and value
            attr_name_tag = row.select_one('td.wiki-h3')
            attr_value_tag = row.select_one('td:not(.wiki-h3)')  # Get the value cell (not the key cell)
            
            if attr_name_tag and attr_value_tag:
                attr_name = attr_name_tag.get_text(strip=True)
                attr_value = attr_value_tag.get_text(strip=True)
                
                # Map attribute names to result structure
                if "洞天仙力" in attr_name:
                    # Convert to integer
                    try:
                        result["基础属性"]["洞天仙力"] = int(attr_value)
                    except ValueError:
                        result["基础属性"]["洞天仙力"] = 0
                elif "摆放区域" in attr_name or "室外摆放区域" in attr_name or "室内摆放区域" in attr_name:
                    # Handle different types of placement areas
                    current_area = result["基础属性"]["摆放区域"]
                    if current_area:
                        result["基础属性"]["摆放区域"] = f"{current_area}, {attr_value}"
                    else:
                        result["基础属性"]["摆放区域"] = attr_value
                elif "一级分类" in attr_name:
                    result["基础属性"]["一级分类"] = attr_value
                elif "二级分类" in attr_name:
                    result["基础属性"]["二级分类"] = attr_value
                elif "相关套装" in attr_name:
                    result["基础属性"]["相关套装"] = attr_value
                    
    def _extract_map_descriptions(self, soup, result: Dict[str, Any]) -> None:
        """Extract map description images."""
        img_tags = soup.select('.obc-tmpl-mapDesc .swiper-slide picture source')
        for img_tag in img_tags:
            if img_tag.get('srcset'):
                result["地图说明"]["图片"].append(img_tag['srcset'])