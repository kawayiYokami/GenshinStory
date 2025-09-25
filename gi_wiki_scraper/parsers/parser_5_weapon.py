"""
Parser for Genshin Impact wiki pages under the 'Weapon' (武器) category.
ID: 5_weapon
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser5Weapon(BaseParser):
    """
    Specific parser for 'Weapon' wiki pages.
    Extracts weapon details including title, description, rarity, type, growth info, story, recommended roles, and display images.
    """
    
    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a weapon page.
        
        Args:
            html (str): The full HTML content of the page.
            
        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)
        
        # 1. Extract the main title
        title_tag = soup.find('h1', class_='detail__title')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
        
        # 2. Extract description
        description = ""
        desc_tag = soup.select_one('.obc-tmpl-goodDesc table .obc-tmpl__rich-text p')
        if desc_tag:
            description = desc_tag.get_text(strip=True)
            
        # 3. Extract base info (type and rarity)
        type_ = ""
        rarity = 0
        
        # Extract type
        type_tag = soup.select_one('.obc-tmpl-equipmentBaseInfo td:contains("装备类型") + td')
        if type_tag:
            type_ = type_tag.get_text(strip=True)
            
        # Extract rarity
        rarity_icons = soup.select('.obc-tmpl-equipmentBaseInfo .obc-tmpl__rate-icon')
        rarity = len(rarity_icons)
        
        # 4. Extract growth info
        growth_info = []
        growth_slides = soup.select('.obc-tmpl-equipmentGrowthInfo .swiper-slide')
        
        for slide in growth_slides:
            # Extract level
            level_tag = slide.select_one('table th')
            level = level_tag.get_text(strip=True) if level_tag else ""
            
            # Extract base ATK
            base_atk = ""
            base_atk_tag = slide.find('p', string=lambda text: text and '基础攻击力' in text)
            if base_atk_tag:
                base_atk = base_atk_tag.get_text(strip=True)
                
            # Extract secondary stat
            secondary_stat = ""
            secondary_stat_tag = slide.find('p', string=lambda text: text and ('攻击力:' in text or '元素' in text))
            if secondary_stat_tag:
                secondary_stat = secondary_stat_tag.get_text(strip=True)
                
            # Extract materials
            materials = []
            material_tags = slide.select('tbody .obc-tmpl__icon-text-num')
            for mat_tag in material_tags:
                name_tag = mat_tag.select_one('span.obc-tmpl__icon-text')
                count_tag = mat_tag.select_one('span.obc-tmpl__icon-num')
                name = name_tag.get_text(strip=True) if name_tag else ""
                count_text = count_tag.get_text(strip=True) if count_tag else ""
                count = self._safe_int(count_text, 0)
                if name:
                    materials.append({"name": name, "count": count})
                    
            growth_info.append({
                "level": level,
                "base_atk": base_atk,
                "secondary_stat": secondary_stat,
                "materials": materials
            })
            
        # 5. Extract story
        story_parts = []
        story_tags = soup.select('.obc-tmpl-fold .obc-tmpl__paragraph-box p')
        for tag in story_tags:
            text = tag.get_text(strip=True)
            if text:
                story_parts.append(text)
        story = "\n".join(story_parts)
        
        # 6. Extract recommended roles
        recommended_roles = []
        role_rows = soup.select('.obc-tmpl-multiTable tbody tr')
        for row in role_rows:
            tds = row.find_all('td')
            if len(tds) >= 2:
                # Extract role name
                name = ""
                name_wrapper = tds[0].select_one('.custom-entry-wrapper')
                if name_wrapper and name_wrapper.get('data-entry-name'):
                    name = name_wrapper['data-entry-name']
                else:
                    name_tag = tds[0].select_one('a .name')
                    if name_tag:
                        name = name_tag.get_text(strip=True)
                        
                # Extract description
                desc_tag = tds[1].select_one('p')
                description = desc_tag.get_text(strip=True) if desc_tag else ""
                
                if name:
                    recommended_roles.append({
                        "name": name,
                        "description": description
                    })
                    
        # 7. Extract display images
        display_images = []
        img_tags = soup.select('.obc-tmpl-mapDesc picture source')
        for img_tag in img_tags:
            if img_tag.get('srcset'):
                display_images.append(img_tag['srcset'])
                
        # Assemble final data structure
        return {
            "title": title,
            "description": description,
            "rarity": rarity,
            "type": type_,
            "growth_info": growth_info,
            "story": story,
            "recommended_roles": recommended_roles,
            "display_images": display_images
        }