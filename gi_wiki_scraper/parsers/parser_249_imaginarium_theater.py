
"""
Parser for Genshin Impact wiki pages under the 'Imaginarium Theater' (幻想真境剧诗) category.
ID: 249_imaginarium_theater
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser249ImaginariumTheater(BaseParser):
    """
    Specific parser for 'Imaginarium Theater' wiki pages.
    Extracts theater details including name, type, tokens, rules, blessings, events, and stage effects.
    """
    
    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of an imaginarium theater page.
        
        Args:
            html (str): The full HTML content of the page.
            
        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)
        
        # Initialize the result dictionary with default values
        result = {
            "活动名称": "",
            "类型": "幻想真境剧诗活动",
            "代币与规则": {
                "幻剧之花": "",
                "重置之骰": "",
                "刷新规则": ""
            },
            "辉彩祝福": {
                "描述": "",
                "祝福列表": []
            },
            "伙伴事件": {
                "描述": "",
                "事件列表": []
            },
            "神秘收获": {
                "描述": "",
                "事件列表": []
            },
            "战斗事件": {
                "描述": "",
                "奖励一览": [],
                "演出一览": []
            },
            "舞台效果": []
        }
        
        # Extract activity name
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["活动名称"] = name_tag.get_text(strip=True)
            
        # First extract tokens and rules from non-fold structure
        self._extract_tokens_and_rules_direct(soup, result)
        
        # Extract modules from fold panels
        self._extract_modules(soup, result)
        
        return result
    
    def _extract_tokens_and_rules_direct(self, soup, result: Dict[str, Any]) -> None:
        """Extract tokens and rules from direct baseInfo structure (not in fold)."""
        # Look for the baseInfo section containing tokens and rules
        base_info_section = soup.select_one('.obc-tmpl-baseInfo:has(h2:contains("代币与规则"))')
        if not base_info_section:
            return
            
        info_table = base_info_section.select_one('table')
        if not info_table:
            return
            
        rows = info_table.select('tbody tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                
                if "幻剧之花" in key:
                    result["代币与规则"]["幻剧之花"] = value
                elif "重置之骰" in key:
                    result["代币与规则"]["重置之骰"] = value
                elif "刷新规则" in key:
                    result["代币与规则"]["刷新规则"] = value
    
    def _extract_modules(self, soup, result: Dict[str, Any]) -> None:
        """Extract different modules of the imaginarium theater page."""
        # Find all fold panels
        fold_panels = soup.select('.obc-tmpl-fold')
        
        for panel in fold_panels:
            title_tag = panel.select_one('.obc-tmpl-fold__title span')
            if not title_tag:
                continue
                
            title = title_tag.get_text(strip=True)
            
            # Dispatch to appropriate extraction function based on title
            if "奇妙助益/辉彩祝福" in title:
                self._extract_radiant_blessings(panel, result)
            elif "伙伴事件" in title:
                self._extract_partner_events(panel, result)
            elif "神秘收获" in title:
                self._extract_mysterious_harvests(panel, result)
            elif "战斗事件" in title:
                self._extract_battle_events(panel, result)
            elif "舞台效果" in title:
                self._extract_stage_effects(panel, result)
                
    def _extract_tokens_and_rules(self, panel, result: Dict[str, Any]) -> None:
        """Extract token and rule information."""
        info_table = panel.select_one('.obc-tmpl-baseInfo table')
        if not info_table:
            return
            
        rows = info_table.select('tbody tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                
                if "幻剧之花" in key:
                    result["代币与规则"]["幻剧之花"] = value
                elif "重置之骰" in key:
                    result["代币与规则"]["重置之骰"] = value
                elif "刷新规则" in key:
                    result["代币与规则"]["刷新规则"] = value
    
    def _extract_radiant_blessings(self, panel, result: Dict[str, Any]) -> None:
        """Extract radiant blessings information."""
        # Extract description
        desc_box = panel.select_one('.obc-tmpl__paragraph-box')
        if desc_box:
            desc_parts = []
            for p in desc_box.select('p'):
                text = p.get_text(strip=True)
                if text:
                    desc_parts.append(text)
            result["辉彩祝福"]["描述"] = "\n".join(desc_parts)
    
    def _extract_partner_events(self, panel, result: Dict[str, Any]) -> None:
        """Extract partner events information."""
        # Extract description
        desc_box = panel.select_one('.obc-tmpl__paragraph-box')
        if desc_box:
            desc_parts = []
            for p in desc_box.select('p'):
                text = p.get_text(strip=True)
                if text:
                    desc_parts.append(text)
            result["伙伴事件"]["描述"] = "\n".join(desc_parts)
            
        # Extract event list
        event_table = panel.select_one('table')
        if event_table:
            event_rows = event_table.select('tbody tr')
            for row in event_rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    name = cells[0].get_text(strip=True)
                    effect = cells[1].get_text(strip=True)
                    
                    # Skip header rows
                    if name and name != "事件名称" and effect and effect != "事件效果":
                        result["伙伴事件"]["事件列表"].append({
                            "名称": name,
                            "效果": effect
                        })
    
    def _extract_mysterious_harvests(self, panel, result: Dict[str, Any]) -> None:
        """Extract mysterious harvests information."""
        # Extract description
        desc_box = panel.select_one('.obc-tmpl__paragraph-box')
        if desc_box:
            desc_parts = []
            for p in desc_box.select('p'):
                text = p.get_text(strip=True)
                if text:
                    desc_parts.append(text)
            result["神秘收获"]["描述"] = "\n".join(desc_parts)
            
        # Extract event list
        event_table = panel.select_one('table')
        if event_table:
            event_rows = event_table.select('tbody tr')
            for row in event_rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    name = cells[0].get_text(strip=True)
                    effect = cells[1].get_text(strip=True)
                    
                    # Skip header rows
                    if name and name != "事件名称" and effect != "事件效果":
                        result["神秘收获"]["事件列表"].append({
                            "名称": name,
                            "效果": effect
                        })
    
    def _extract_battle_events(self, panel, result: Dict[str, Any]) -> None:
        """Extract battle events information."""
        # Extract description
        desc_box = panel.select_one('.obc-tmpl__paragraph-box')
        if desc_box:
            desc_parts = []
            for p in desc_box.select('p'):
                text = p.get_text(strip=True)
                if text:
                    desc_parts.append(text)
            result["战斗事件"]["描述"] = "\n".join(desc_parts)
            
        # Extract tables
        tables = panel.select('table')
        
        # Extract reward list (first table)
        if len(tables) >= 1:
            reward_table = tables[0]
            reward_rows = reward_table.select('tbody tr')
            for row in reward_rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    event_type = cells[0].get_text(strip=True)
                    base_reward = cells[1].get_text(strip=True)
                    star_reward = cells[2].get_text(strip=True)
                    
                    # Skip header rows
                    if event_type and event_type != "演出类型" and base_reward and base_reward != "基础奖励" and star_reward and star_reward != "明星奖励":
                        result["战斗事件"]["奖励一览"].append({
                            "演出类型": event_type,
                            "基础奖励": base_reward,
                            "明星奖励": star_reward
                        })
                    
        # Extract performance list (second table)
        if len(tables) >= 2:
            performance_table = tables[1]
            performance_rows = performance_table.select('tbody tr')
            for row in performance_rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    event_type = cells[0].get_text(strip=True)
                    base_goal = cells[1].get_text(strip=True)
                    star_challenge = cells[2].get_text(strip=True)
                    
                    # Skip header rows
                    if event_type and event_type != "演出类型" and base_goal and base_goal != "基础目标" and star_challenge and star_challenge != "明星挑战":
                        result["战斗事件"]["演出一览"].append({
                            "演出类型": event_type,
                            "基础目标": base_goal,
                            "明星挑战": star_challenge
                        })
    
    def _extract_stage_effects(self, panel, result: Dict[str, Any]) -> None:
        """Extract stage effects information."""
        effect_table = panel.select_one('table')
        if effect_table:
            effect_rows = effect_table.select('tbody tr')
            for row in effect_rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    name = cells[0].get_text(strip=True)
                    description = cells[1].get_text(strip=True)
                    
                    # Skip header rows
                    if name and name != "效果名称" and description != "效果描述":
                        result["舞台效果"].append({
                            "效果名称": name,
                            "效果描述": description
                        })