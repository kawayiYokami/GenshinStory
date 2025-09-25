"""
Parser for Genshin Impact wiki pages under the 'Adventurers' Guild' (冒险家协会) category.
ID: 55_adventurers_guild
"""
from typing import Dict, Any, List
from .base_parser import BaseParser
from bs4 import Tag


class Parser55AdventurersGuild(BaseParser):
    """
    Specific parser for 'Adventurers' Guild' wiki pages.
    Extracts guild details including name, type, trigger conditions, map info, dialogue trees, process, and rewards.
    """
    
    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of an Adventurers' Guild page.
        
        Args:
            html (str): The full HTML content of the page.
            
        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)
        
        # Initialize the result dictionary with default values
        result = {
            "名称": "",
            "类型": "每日委托",  # Default type based on the sample
            "触发条件": "",
            "地图说明": {
                "图片": []
            },
            "剧情对话": {
                "对话树": []
            },
            "任务过程": [],
            "任务奖励": {
                "奖励表格": []
            }
        }
        
        # 1. Extract guild name
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["名称"] = name_tag.get_text(strip=True)
            
        # 2. Extract basic information
        self._extract_basic_info(soup, result)
        
        # 3. Extract map descriptions
        self._extract_map_descriptions(soup, result)
        
        # 4. Extract dialogue tree (recursive structure)
        self._extract_dialogue_tree(soup, result)
        
        # 5. Extract quest process
        self._extract_quest_process(soup, result)
        
        # 6. Extract quest rewards
        self._extract_quest_rewards(soup, result)
        
        return result
    
    def _extract_basic_info(self, soup, result: Dict[str, Any]) -> None:
        """Extract basic guild information."""
        # Extract trigger conditions
        trigger_tags = soup.select('.obc-tmpl-baseInfo table tbody tr')
        for tag in trigger_tags:
            cells = tag.find_all('td')
            if len(cells) >= 2:
                # Check if the first cell contains "触发条件"
                if "触发条件" in cells[0].get_text(strip=True):
                    result["触发条件"] = cells[1].get_text(strip=True)
                    break
                    
    def _extract_map_descriptions(self, soup, result: Dict[str, Any]) -> None:
        """Extract map description information."""
        # Extract map images
        img_tags = soup.select('.obc-tmpl-mapDesc .swiper-container .swiper-wrapper .swiper-slide picture source')
        for img_tag in img_tags:
            if img_tag.get('srcset'):
                result["地图说明"]["图片"].append(img_tag['srcset'])
                
    def _extract_dialogue_tree(self, soup, result: Dict[str, Any]) -> None:
        """Extracts the dialogue tree using a simplified linear parsing method."""
        tree_container = soup.select_one('.obc-tmpl-interactiveDialogue .tree-wrapper')
        if not tree_container:
            return

        # Get all top-level dialogue and option nodes
        nodes = tree_container.find_all(['div'], class_=['content-box', 'tree-node'], recursive=False)
        
        # Handle cases where nodes are nested one level deeper
        if not nodes:
            nested_container = tree_container.find('div', class_='tree-node', recursive=False)
            if nested_container:
                nodes = nested_container.find_all(['div'], class_=['content-box', 'tree-node'], recursive=False)

        if nodes:
            result["剧情对话"]["对话树"] = self._parse_linear_flow(nodes)

    def _parse_linear_flow(self, nodes: List[Tag]) -> List[Dict[str, Any]]:
        """Parses a linear sequence of dialogue and option nodes."""
        flow = []
        for node in nodes:
            # Case 1: Standard dialogue block
            if 'content-box' in node.get('class', []):
                flow.extend(self._parse_dialogue_block(node))
                continue

            # Case 2: Option selection block
            if 'tree-node' in node.get('class', []):
                option_items = node.find_all('div', class_='option-item', recursive=False)
                if option_items:
                    options_group = {
                        "type": "options",
                        "choices": [item.get_text(strip=True) for item in option_items],
                        "reply": []
                    }
                    
                    # The reply content-box is a CHILD of the option's tree-node
                    reply_node = node.find('div', class_='content-box', recursive=False)
                    if reply_node:
                        options_group["reply"] = self._parse_dialogue_block(reply_node)
                    
                    flow.append(options_group)
                
                # Handle nested nodes if any
                nested_nodes = node.find_all(['div'], class_=['content-box', 'tree-node'], recursive=False)
                if nested_nodes and not option_items: # Avoid re-parsing the reply node
                    flow.extend(self._parse_linear_flow(nested_nodes))

        return flow

    def _parse_dialogue_block(self, content_box: Tag) -> List[Dict[str, Any]]:
        """Parses a content-box into a list of dialogue items using a robust text extraction method."""
        dialogues = []
        for p_tag in content_box.find_all('p'):
            full_text = p_tag.get_text(strip=True)
            if not full_text:
                continue

            speaker_tag = p_tag.find('strong')
            
            if speaker_tag:
                speaker = speaker_tag.get_text(strip=True)
                # Robustly remove the speaker and the following colon (half/full width) from the full text.
                text = full_text.replace(speaker, '', 1).lstrip('：:').strip()
                dialogues.append({"speaker": speaker, "text": text})
            else:
                # This handles action descriptions like '(提交丢失的快件)'
                dialogues.append({"speaker": "旁白", "text": full_text})
        return dialogues
    
    def _extract_quest_process(self, soup, result: Dict[str, Any]) -> None:
        """Extract quest process information."""
        process_tags = soup.select('.obc-tmpl-collapsePanel:contains("任务过程") .obc-tmpl__paragraph-box p')
        for tag in process_tags:
            text = tag.get_text(strip=True)
            if text:
                result["任务过程"].append(text)
                
    def _extract_quest_rewards(self, soup, result: Dict[str, Any]) -> None:
        """Extract quest rewards information."""
        # Extract reward table rows (skip header)
        reward_rows = soup.select('.obc-tmpl-collapsePanel:contains("任务奖励") .table-wrapper table tbody tr')[1:]
        for row in reward_rows:
            cells = row.find_all('td')
            if len(cells) >= 6:
                # Extract reward data
                adventure_rank = cells[0].get_text(strip=True)
                primogems = cells[1].get_text(strip=True)
                exp = cells[2].get_text(strip=True)
                mora = cells[3].get_text(strip=True)
                friendship_exp = cells[4].get_text(strip=True)
                forging_materials = cells[5].get_text(strip=True)
                
                # Convert text values to appropriate types where possible
                try:
                    primogems = int(primogems) if primogems.isdigit() else primogems
                except ValueError:
                    pass
                    
                try:
                    exp = int(exp) if exp.isdigit() else exp
                except ValueError:
                    pass
                    
                try:
                    mora = int(mora) if mora.isdigit() else mora
                except ValueError:
                    pass
                    
                try:
                    friendship_exp = int(friendship_exp) if friendship_exp.isdigit() else friendship_exp
                except ValueError:
                    pass
                    
                result["任务奖励"]["奖励表格"].append({
                    "冒险等阶": adventure_rank,
                    "原石": primogems,
                    "冒险阅历": exp,
                    "摩拉": mora,
                    "好感经验": friendship_exp,
                    "精锻用矿物": forging_materials
                })