"""
Parser for Genshin Impact wiki pages under the 'Spiral Abyss' (深境螺旋) category.
ID: 65_spiral_abyss
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser65SpiralAbyss(BaseParser):
    """
    Specific parser for 'Spiral Abyss' wiki pages.
    Extracts Spiral Abyss details including name, floor number, ley line disorders, and challenge rooms.
    """
    
    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a Spiral Abyss page.
        
        Args:
            html (str): The full HTML content of the page.
            
        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)
        
        # Initialize the result dictionary with default values
        result = {
            "名称": "",
            "层数": 0,
            "地脉异常": {
                "效果": ""
            },
            "挑战房间": []
        }
        
        # 1. Extract Spiral Abyss name and floor number
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["名称"] = name_tag.get_text(strip=True)
            # Extract floor number from the name
            import re
            floor_match = re.search(r'第(\d+)层', result["名称"])
            if floor_match:
                result["层数"] = self._safe_int(floor_match.group(1), 0)
                
        # 2. Extract ley line disorders
        self._extract_ley_line_disorders(soup, result)
        
        # 3. Extract challenge rooms
        self._extract_challenge_rooms(soup, result)
        
        return result
    
    def _extract_ley_line_disorders(self, soup, result: Dict[str, Any]) -> None:
        """Extract ley line disorders information."""
        # Extract ley line disorder effect
        effect_tags = soup.select('.obc-tmpl-multiTable .swiper-container .swiper-wrapper .swiper-slide table tbody tr td p')
        effect_parts = []
        for tag in effect_tags:
            text = tag.get_text(strip=True)
            if text:
                effect_parts.append(text)
        result["地脉异常"]["效果"] = "\n".join(effect_parts)
        
    def _extract_challenge_rooms(self, soup, result: Dict[str, Any]) -> None:
        """Extract challenge room information."""
        # Extract room numbers from pagination bullets
        room_numbers = []
        bullet_tags = soup.select('.obc-tmpl-spiralAbyssTarget .swiper-pagination-bullet')
        for tag in bullet_tags:
            room_number = tag.get_text(strip=True)
            if room_number:
                room_numbers.append(room_number)
                
        # Extract challenge details for each room
        room_slides = soup.select('.obc-tmpl-spiralAbyssTarget .swiper-slide')
        
        for i, slide in enumerate(room_slides):
            room_info = {
                "房间编号": room_numbers[i] if i < len(room_numbers) else "",
                "挑战条件": [],
                "敌人等级": 0,
                "上半": [],
                "下半": []
            }
            
            # Extract challenge conditions
            condition_tags = slide.select('td.pre-line')
            for tag in condition_tags:
                condition = tag.get_text(strip=True)
                if condition:
                    room_info["挑战条件"].append(condition)
                    
            # Extract enemy level
            enemy_level_tag = slide.select_one('td:contains("敌人等级")')
            if enemy_level_tag:
                level_text = enemy_level_tag.get_text(strip=True)
                # Extract the number from the text
                import re
                level_match = re.search(r'(\d+)', level_text)
                if level_match:
                    room_info["敌人等级"] = self._safe_int(level_match.group(1), 0)
                    
            # Extract enemies for both halves
            self._extract_enemies(slide, room_info)
            
            result["挑战房间"].append(room_info)
            
    def _extract_enemies(self, slide, room_info: Dict[str, Any]) -> None:
        """Extract enemy information for both halves of a challenge room."""
        # Find all rows in the enemy table
        enemy_rows = slide.select('tbody tr')
        
        # Track state for parsing
        is_upper_half = True  # Start with upper half
        current_round_index = -1  # Index of the current round in the half
        seen_first_round = False  # Flag to track if we've seen the first "第一轮"
        
        for row in enemy_rows:
            # Check if this row is a round header (e.g., "第一轮", "第二轮")
            round_header_tag = row.select_one('td.wiki-h3')
            if round_header_tag:
                round_text = round_header_tag.get_text(strip=True)
                
                # Check if this is "第一轮"
                if "第一轮" in round_text:
                    # If we've already seen "第一轮", this indicates the start of the lower half
                    if seen_first_round:
                        is_upper_half = False
                        current_round_index = -1  # Reset round index for lower half
                    else:
                        seen_first_round = True
                        
                # Increment round index
                current_round_index += 1
                
                # Create a new round entry for the current half
                round_entry = {
                    "轮次": round_text,
                    "敌人": []
                }
                
                # Add the round entry to the appropriate half
                if is_upper_half:
                    # Ensure the upper half list has enough rounds
                    while len(room_info["上半"]) <= current_round_index:
                        room_info["上半"].append({
                            "轮次": f"第{len(room_info['上半']) + 1}轮",
                            "敌人": []
                        })
                    # Update the round entry for the current round
                    room_info["上半"][current_round_index] = round_entry
                else:
                    # Ensure the lower half list has enough rounds
                    while len(room_info["下半"]) <= current_round_index:
                        room_info["下半"].append({
                            "轮次": f"第{len(room_info['下半']) + 1}轮",
                            "敌人": []
                        })
                    # Update the round entry for the current round
                    room_info["下半"][current_round_index] = round_entry
                    
                continue  # Move to the next row
                
            # If this is not a round header, it should contain enemy information
            # Find all enemy items in this row
            enemy_items = row.select('.obc-tmpl__material-item')
            
            enemies = []
            for item in enemy_items:
                name_tag = item.select_one('.obc-tmpl__material-name')
                num_tag = item.select_one('.obc-tmpl__material-num')
                link_tag = item.select_one('a.obc-tmpl__material-href')
                
                name = name_tag.get_text(strip=True) if name_tag else ""
                num = 0
                if num_tag:
                    num_text = num_tag.get_text(strip=True)
                    # Try to extract a number from the text
                    try:
                        num = int(num_text)
                    except ValueError:
                        # If conversion fails, leave as 0
                        pass
                        
                link = link_tag['href'] if link_tag and link_tag.get('href') else ""
                
                if name:
                    enemies.append({
                        "名称": name,
                        "数量": num,
                        "链接": link
                    })
                    
            # Add enemies to the current round of the current half
            if enemies:
                if is_upper_half and room_info["上半"]:
                    # Add to the last round in the upper half
                    room_info["上半"][current_round_index]["敌人"].extend(enemies)
                elif not is_upper_half and room_info["下半"]:
                    # Add to the last round in the lower half
                    room_info["下半"][current_round_index]["敌人"].extend(enemies)