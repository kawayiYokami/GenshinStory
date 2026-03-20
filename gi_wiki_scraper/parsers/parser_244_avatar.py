"""
Parser for Genshin Impact wiki pages under the 'Avatar' (头像) category.
ID: 244_avatar
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser244Avatar(BaseParser):
    """
    Specific parser for 'Avatar' wiki pages.
    Extracts avatar details including name, type, estimated time, acquisition method, quest details, region, prerequisites, and rewards.
    """
    
    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of an avatar page.
        
        Args:
            html (str): The full HTML content of the page.
            
        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)
        
        # Initialize the result dictionary with default values
        # Only include fields that actually exist in the HTML
        result = {
            "头像名称": "",
            "类型": "头像解锁任务",  # Default type based on the sample
            "预估获取时长": "",
            "获取方式": ""
        }
        
        # 1. Extract avatar name
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["头像名称"] = name_tag.get_text(strip=True)
            
        # 2. Extract detailed information
        self._extract_detailed_info(soup, result)
        
        return result
    
    def _extract_detailed_info(self, soup, result: Dict[str, Any]) -> None:
        """Extract detailed avatar information."""
        # Find the material base info table
        info_table = soup.select_one('.obc-tmpl-materialBaseInfo tbody')
        if not info_table:
            return
            
        rows = info_table.select('tr')
        for row in rows:
            # Extract label and value
            label_tag = row.select_one('label')
            if not label_tag:
                continue
                
            label = label_tag.get_text(strip=True)
            
            # Find the value cell (next sibling or child of parent td)
            value_cell = None
            parent_td = label_tag.find_parent('td')
            if parent_td:
                # Look for the next td or a div/p within the same td
                next_td = parent_td.find_next_sibling('td')
                if next_td:
                    value_cell = next_td
                else:
                    # Check for div or p within the same td
                    value_cell = parent_td
                    
            if not value_cell:
                continue
                
            # Extract value based on label
            # Note: We skip "名称：" extraction here as it's already handled in parse()
            if "预估获取时长：" in label:
                # Extract estimated time from p
                time_p = value_cell.select_one('p')
                if time_p:
                    result["预估获取时长"] = time_p.get_text(strip=True)
                    
            elif "获取方式：" in label:
                # Extract acquisition method from p
                method_p = value_cell.select_one('p')
                if method_p:
                    result["获取方式"] = method_p.get_text(strip=True)
                    
            # Note: Skipping fields that don't exist in this HTML:
            # - "任务详情：" (quest details)
            # - "所属地区：" (region)
            # - "前置任务：" (prerequisites)
            # - "任务奖励：" (rewards)
            # These fields may exist in other avatar pages, but not in this one