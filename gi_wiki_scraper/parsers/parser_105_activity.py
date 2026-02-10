"""
Parser for Genshin Impact wiki pages under the 'Activity' (活动) category.
ID: 105_activity
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser105Activity(BaseParser):
    """
    Specific parser for 'Activity' wiki pages.
    Extracts activity details including name, type, images, rules, descriptions, tips, phase content, and strategy recommendations.
    """
    
    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of an activity page.
        
        Args:
            html (str): The full HTML content of the page.
            
        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)
        
        # Initialize the result dictionary with only essential fields
        result = {
            "活动名称": "",
            "活动图片": [],
            "活动规则": {
                "规则图片": [],
                "介绍文本": ""
            },
            "活动说明": {
                "活动说明": [],
                "活动时间": {
                    "整体活动时间": "",
                    "紊乱爆发期": ""
                },
                "参与条件": {
                    "冒险等阶": "",
                    "任务要求": "",
                    "推荐任务": ""
                },
                "活动奖励": {
                    "图片": ""
                }
            },
            "小贴士": {
                "介绍": "",
                "贴士图片": [],
                "相关链接": ""
            },
            "二期内容": {
                "标题": "",
                "战场信息": []
            },
            "攻略推荐": []
        }
        
        # 1. Extract activity name
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["活动名称"] = name_tag.get_text(strip=True)
            
        # 2. Extract modules
        self._extract_modules(soup, result)
        
        return result
    
    def _extract_modules(self, soup, result: Dict[str, Any]) -> None:
        """Extract different modules of the activity page."""
        # Find all fold panels
        fold_panels = soup.select('.obc-tmpl-fold')
        
        for panel in fold_panels:
            title_tag = panel.select_one('.obc-tmpl-fold__title span')
            if not title_tag:
                continue
                
            title = title_tag.get_text(strip=True)
            
            # Dispatch to appropriate extraction function based on title
            if "活动规则" in title:
                self._extract_activity_rules(panel, result)
            elif "活动说明" in title or "说明" in title:
                self._extract_activity_description(panel, result)
            elif "小贴士" in title:
                self._extract_tips(panel, result)
            elif "二期" in title or "第二期" in title:
                self._extract_phase_content(panel, result)
            elif "玩法" in title:
                self._extract_gameplay_description(panel, result)
                
        # Extract strategy recommendations (outside of fold panels)
        self._extract_strategies(soup, result)
        
        # Extract activity images (these might be in various places)
        self._extract_activity_images(soup, result)
        
        # Extract activity type from the page content (this is a simplified approach)
        type_tag = soup.select_one('.obc-tmpl-baseInfo table tbody tr td:contains("类型") + td')
        if type_tag:
            result["类型"] = type_tag.get_text(strip=True)
            
    def _extract_activity_rules(self, panel, result: Dict[str, Any]) -> None:
        """Extract activity rules information."""
        # Extract introduction text
        intro_tags = panel.select('.obc-tmpl__paragraph-box p')
        intro_parts = []
        for tag in intro_tags:
            text = tag.get_text(strip=True)
            if text:
                intro_parts.append(text)
        result["活动规则"]["介绍文本"] = "\n".join(intro_parts)
        
        # Extract rule images
        img_tags = panel.select('.custom-image-view[data-image-url]')
        for img_tag in img_tags:
            if img_tag.get('data-image-url'):
                result["活动规则"]["规则图片"].append(img_tag['data-image-url'])
                
    def _extract_activity_description(self, panel, result: Dict[str, Any]) -> None:
        """Extract activity description information."""
        # Extract text content
        desc_tags = panel.select('.obc-tmpl__paragraph-box p')
        desc_parts = []
        for tag in desc_tags:
            text = tag.get_text(strip=True)
            if text:
                desc_parts.append(text)
                
                # Check for special markers like "〓" to structure the data
                if "〓" in text:
                    # Split by "〓" to get structured data
                    parts = text.split("〓")
                    for part in parts:
                        part = part.strip()
                        if not part:
                            continue
                            
                        # Try to identify structured fields
                        if "整体活动时间" in part:
                            time_parts = part.split("：", 1)
                            if len(time_parts) > 1:
                                result["活动说明"]["活动时间"]["整体活动时间"] = time_parts[1].strip()
                        elif "紊乱爆发期" in part:
                            time_parts = part.split("：", 1)
                            if len(time_parts) > 1:
                                result["活动说明"]["活动时间"]["紊乱爆发期"] = time_parts[1].strip()
                        elif "冒险等阶" in part:
                            level_parts = part.split("：", 1)
                            if len(level_parts) > 1:
                                result["活动说明"]["参与条件"]["冒险等阶"] = level_parts[1].strip()
                        elif "任务要求" in part and "完成魔神任务" in part:
                            task_parts = part.split("：", 1)
                            if len(task_parts) > 1:
                                result["活动说明"]["参与条件"]["任务要求"] = task_parts[1].strip()
                        elif "推荐任务" in part and "完成魔神任务" in part:
                            task_parts = part.split("：", 1)
                            if len(task_parts) > 1:
                                result["活动说明"]["参与条件"]["推荐任务"] = task_parts[1].strip()
                                
        # Add general description text (excluding the structured parts)
        # This is a simplified approach - in reality, you'd want to exclude the parts that were already parsed
        result["活动说明"]["活动说明"] = desc_parts
        
        # Extract reward images
        reward_img_tags = panel.select('.obc-tmpl__paragraph-box .custom-image-view[data-image-url]')
        for img_tag in reward_img_tags:
            if img_tag.get('data-image-url'):
                result["活动说明"]["活动奖励"]["图片"] = img_tag['data-image-url']
                
    def _extract_tips(self, panel, result: Dict[str, Any]) -> None:
        """Extract tips information."""
        # Extract introduction text
        intro_tags = panel.select('.obc-tmpl__paragraph-box p')
        intro_parts = []
        for tag in intro_tags:
            text = tag.get_text(strip=True)
            if text:
                intro_parts.append(text)
        result["小贴士"]["介绍"] = "\n".join(intro_parts)
        
        # Extract tip images
        img_tags = panel.select('.custom-image-view[data-image-url]')
        for img_tag in img_tags:
            if img_tag.get('data-image-url'):
                result["小贴士"]["贴士图片"].append(img_tag['data-image-url'])
                
        # Extract related links (this is a simplified approach)
        link_tags = panel.select('a')
        for link_tag in link_tags:
            href = link_tag.get('href', '')
            if href and 'miyoushe.com' in href:
                result["小贴士"]["相关链接"] = href
                break  # Take the first relevant link
                
    def _extract_gameplay_description(self, panel, result: Dict[str, Any]) -> None:
        """Extract gameplay description information."""
        # This panel contains gameplay images and description
        # Extract description text
        desc_tags = panel.select('.obc-tmpl__paragraph-box p')
        desc_parts = []
        for tag in desc_tags:
            text = tag.get_text(strip=True)
            if text and not text.startswith('旅行者好呀'):
                desc_parts.append(text)
        
        # Store in activity rules as this contains gameplay information
        if desc_parts:
            result["活动规则"]["介绍文本"] = "\n".join(desc_parts)
            
        # Extract gameplay images
        img_tags = panel.select('.custom-image-view[data-image-url]')
        for img_tag in img_tags:
            if img_tag.get('data-image-url'):
                result["活动规则"]["规则图片"].append(img_tag['data-image-url'])
                
    def _extract_phase_content(self, panel, result: Dict[str, Any]) -> None:
        """Extract phase content information."""
        # Extract phase title
        title_tag = panel.select_one('.obc-tmpl-fold__title span')
        if title_tag:
            result["二期内容"]["标题"] = title_tag.get_text(strip=True)
            
        # Extract battlefield information
        battlefield_items = panel.select('ul li')
        for item in battlefield_items:
            battlefield = {
                "战场": "",
                "敌人": {
                    "名称": "",
                    "链接": "",
                    "图片": ""
                },
                "战斗机制": ""
            }
            
            # Extract battlefield name (this is a simplified approach)
            battlefield["战场"] = item.get_text(strip=True)[:5]  # First 5 characters as placeholder
            
            # Extract enemy information (this is a simplified approach)
            enemy_link_tag = item.select_one('a')
            if enemy_link_tag:
                battlefield["敌人"]["链接"] = enemy_link_tag.get('href', '')
                
            # Extract enemy name (this is a simplified approach)
            enemy_name_tag = item.select_one('.name')
            if enemy_name_tag:
                battlefield["敌人"]["名称"] = enemy_name_tag.get_text(strip=True)
                
            # Extract enemy image (this is a simplified approach)
            enemy_img_tag = item.select_one('.custom-image-view[data-image-url]')
            if enemy_img_tag and enemy_img_tag.get('data-image-url'):
                battlefield["敌人"]["图片"] = enemy_img_tag['data-image-url']
                
            # Extract battle mechanics (this is a simplified approach)
            mech_text = item.get_text(strip=True)
            if "战斗" in mech_text:
                battlefield["战斗机制"] = mech_text
                
            result["二期内容"]["战场信息"].append(battlefield)
            
    def _extract_strategies(self, soup, result: Dict[str, Any]) -> None:
        """Extract strategy recommendations."""
        strategy_cards = soup.select('.obc-tmpl-strategy__card')
        for card in strategy_cards:
            strategy = {
                "标题": "",
                "链接": ""
            }
            
            # Extract title
            title_tag = card.select_one('.obc-tmpl-strategy__card--text')
            if title_tag:
                strategy["标题"] = title_tag.get_text(strip=True)
                
            # Extract link
            link_tag = card.select_one('a.obc-tmpl-strategy__url')
            if link_tag:
                strategy["链接"] = link_tag.get('href', '')
                
            if strategy["标题"]:
                result["攻略推荐"].append(strategy)
                
    def _extract_activity_images(self, soup, result: Dict[str, Any]) -> None:
        """Extract activity images from various parts of the page."""
        img_tags = soup.select('.custom-image-view[data-image-url]')
        for img_tag in img_tags:
            if img_tag.get('data-image-url'):
                # Avoid duplicates
                if img_tag['data-image-url'] not in result["活动图片"]:
                    result["活动图片"].append(img_tag['data-image-url'])