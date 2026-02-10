"""
Parser for Genshin Impact wiki pages under the 'Achievement' (成就) category.
ID: 252_achievement
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser252Achievement(BaseParser):
    """
    Specific parser for 'Achievement' wiki pages.
    Extracts achievement details including name, type, set, description, rewards, and release version.
    """
    
    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of an achievement page.
        
        Args:
            html (str): The full HTML content of the page.
            
        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)
        
        # Initialize the result dictionary with default values
        result = {
            "成就名称": "",
            "类型": "成就",
            "成就集": "",
            "描述": "",
            "奖励": [],
            "上线版本": "",
            "成就列表": []
        }
        
        # 1. Extract main title
        title_tag = soup.select_one('h1.detail__title')
        if title_tag:
            result["成就名称"] = title_tag.get_text(strip=True)
        
        # 2. Extract achievement set and description from the info table
        info_table = soup.select_one('table.obc-tmpl-materialBaseInfo')
        if info_table:
            # Find the row with "名片纹饰" label
            label_tag = info_table.find('label', string=lambda text: text and '名片纹饰：' in text)
            if label_tag:
                parent_td = label_tag.find_parent('td')
                if parent_td:
                    next_td = parent_td.find_next_sibling('td')
                    if next_td:
                        # Get the span text which contains the achievement set name
                        span_tag = next_td.select_one('span')
                        if span_tag:
                            result["成就集"] = span_tag.get_text(strip=True)
            
            # Find the description row
            desc_row = info_table.find('td', string=lambda text: text and '达成以下所有成就可领取名片纹饰' in text)
            if desc_row:
                result["描述"] = "达成以下所有成就可领取名片纹饰"
        
        # 3. Extract achievement list
        achievement_list_wrap = soup.select_one('#module-6101') or soup.find('h2', string='成就列表')
        if achievement_list_wrap:
            # Find the table containing achievements
            table = achievement_list_wrap.find_next('table') if achievement_list_wrap.name == 'h2' else achievement_list_wrap.find('table')
            if table:
                tbody = table.find('tbody')
                if tbody:
                    rows = tbody.select('tr')
                    for row in rows:
                        # Extract achievement name and description
                        cells = row.select('td')
                        if len(cells) >= 2:
                            name_cell = cells[0]
                            desc_cell = cells[1]
                            
                            name = name_cell.get_text(strip=True) if name_cell else ""
                            desc = desc_cell.get_text(strip=True) if desc_cell else ""
                            
                            if name:  # Only add if name is not empty
                                achievement = {
                                    "名称": name,
                                    "描述": desc
                                }
                                result["成就列表"].append(achievement)
        
        return result