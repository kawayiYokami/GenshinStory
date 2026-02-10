"""
Parser for Genshin Impact wiki pages under the 'Quest' (任务) category.
ID: 43_quest
"""
from typing import Dict, Any, List
import bs4
from .base_parser import BaseParser


class Parser43Quest(BaseParser):
    """
    Specific parser for 'Quest' wiki pages.
    Extracts quest details including name, conditions, NPCs, process, rewards, map info, and dialogue trees.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a quest page.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data with multiple quests.
        """
        soup = self._create_soup(html)

        # Extract main quest series title
        quest_title = ""
        title_tag = soup.select_one('h1.detail__title')
        if title_tag:
            quest_title = title_tag.get_text(strip=True)

        # Find all module groups
        module_groups = soup.select('div[id^="module-group-"]')

        if not module_groups:
            # Fallback to old behavior if no module groups found
            quest_data = self._parse_single_quest(soup)
            return {
                "任务标题": quest_title,
                "任务列表": [quest_data] if quest_data and quest_data.get("名称") else [],
                "任务数量": 1 if quest_data and quest_data.get("名称") else 0
            }

        # Parse each module group as a separate quest
        quests = []
        for group in module_groups:
            quest_data = self._parse_single_quest(group, soup)
            if quest_data and quest_data.get("名称"):  # Only add if quest has a name
                quests.append(quest_data)

        # Return structure with multiple quests
        return {
            "任务标题": quest_title,
            "任务列表": quests,
            "任务数量": len(quests)
        }

    def _parse_single_quest(self, scope, full_soup=None) -> Dict[str, Any]:
        """
        Parses a single quest from the given scope.

        Args:
            scope: The BeautifulSoup element to search within
            full_soup: The full soup object for fallback searches

        Returns:
            Dict[str, Any]: A dictionary containing the parsed quest data.
        """
        # Initialize the result dictionary with default values
        result = {
            "名称": "",
            "任务概述": {
                "前置任务": [],
                "起始NPC": {"名称": ""},
                "结束NPC": {"名称": ""},
                "后续任务": []
            },
            "触发条件": "",
            "等级限制": "",
            "特殊限制": "",
            "任务过程": [],
            "剧情对话": []
        }

        # 1. Extract quest name - look for h2 within baseInfo section
        name_tag = scope.select_one('.obc-tmpl-part.obc-tmpl-baseInfo h2.wiki-h2')
        if name_tag:
            result["名称"] = name_tag.get_text(strip=True)

        # 2. Extract basic information
        self._extract_basic_info(scope, result)

        # 3. Extract quest overview
        self._extract_quest_overview(scope, result)

        # 4. Extract quest process
        self._extract_quest_process(scope, result)

        # 5. Extract dialogue tree (complex interactive structure)
        self._extract_dialogue_tree(scope, result)

        return result

    def _extract_basic_info(self, scope, result: Dict[str, Any]) -> None:
        """Extract basic quest information."""
        # Extract trigger condition
        trigger_tag = scope.select_one('td:contains("触发条件") + td')
        if trigger_tag:
            result["触发条件"] = trigger_tag.get_text(strip=True)

        # Extract level restriction
        level_tag = scope.select_one('td:contains("等级限制") + td')
        if level_tag:
            result["等级限制"] = level_tag.get_text(strip=True)

        # Extract special restrictions
        special_tag = scope.select_one('td:contains("特殊限制") + td')
        if special_tag:
            result["特殊限制"] = special_tag.get_text(strip=True)

    def _extract_quest_overview(self, scope, result: Dict[str, Any]) -> None:
        """Extract quest overview information with updated selectors and format."""

        # Extract prerequisite quests - updated selector for new HTML structure
        prereq_row = scope.select_one('td:contains("前置任务")')
        if prereq_row:
            prereq_cell = prereq_row.find_next_sibling('td')
            if prereq_cell:
                # Look for .custom-entry-wrapper or .name elements
                name_tags = prereq_cell.select('.custom-entry-wrapper .name, .name')
                for tag in name_tags:
                    name = tag.get_text(strip=True)
                    if name:
                        result["任务概述"]["前置任务"].append({"名称": name})

                # If no name tags found, check for plain text
                if not name_tags:
                    text = prereq_cell.get_text(strip=True)
                    if text and text != "无":
                        result["任务概述"]["前置任务"].append({"名称": text})
                    elif text == "无":
                        result["任务概述"]["前置任务"].append({"名称": "无"})

        # Extract starting NPC
        start_npc_row = scope.select_one('td:contains("起始NPC"), td:contains("起始npc")')
        if start_npc_row:
            start_npc_cell = start_npc_row.find_next_sibling('td')
            if start_npc_cell:
                name_tag = start_npc_cell.select_one('.custom-entry-wrapper .name, .name')
                if name_tag:
                    name = name_tag.get_text(strip=True)
                    result["任务概述"]["起始NPC"] = {"名称": name}
                else:
                    text = start_npc_cell.get_text(strip=True)
                    if text:
                        result["任务概述"]["起始NPC"] = {"名称": text}

        # Extract ending NPC
        end_npc_row = scope.select_one('td:contains("结束NPC"), td:contains("结束npc")')
        if end_npc_row:
            end_npc_cell = end_npc_row.find_next_sibling('td')
            if end_npc_cell:
                name_tag = end_npc_cell.select_one('.custom-entry-wrapper .name, .name')
                if name_tag:
                    name = name_tag.get_text(strip=True)
                    result["任务概述"]["结束NPC"] = {"名称": name}
                else:
                    text = end_npc_cell.get_text(strip=True)
                    if text:
                        result["任务概述"]["结束NPC"] = {"名称": text}

        # Extract follow-up quests
        followup_row = scope.select_one('td:contains("后续任务")')
        if followup_row:
            followup_cell = followup_row.find_next_sibling('td')
            if followup_cell:
                name_tags = followup_cell.select('.custom-entry-wrapper .name, .name')
                for tag in name_tags:
                    name = tag.get_text(strip=True)
                    if name:
                        result["任务概述"]["后续任务"].append({"名称": name})

                # If no name tags found, check for plain text
                if not name_tags:
                    text = followup_cell.get_text(strip=True)
                    if text:
                        result["任务概述"]["后续任务"].append({"名称": text})

    def _extract_quest_process(self, scope, result: Dict[str, Any]) -> None:
        """Extract quest process information."""
        process_tags = scope.select('.obc-tmpl-collapsePanel:contains("任务过程") .obc-tmpl__paragraph-box p')
        for tag in process_tags:
            text = tag.get_text(strip=True)
            if text:
                result["任务过程"].append(text)

    def _extract_dialogue_tree(self, scope: bs4.BeautifulSoup, result: Dict[str, Any]) -> None:
        """Extracts dialogue from both interactive and non-interactive dialogue modules."""
        all_dialogues = []

        # 1. Extract interactive dialogues
        interactive_modules = scope.select('.obc-tmpl-interactiveDialogue')
        for module in interactive_modules:
            tree_container = module.select_one('.tree-wrapper')
            if not tree_container:
                continue

            nodes = tree_container.find_all(['div'], class_=['content-box', 'tree-node'], recursive=False)
            if not nodes:
                nested_container = tree_container.find('div', class_='tree-node', recursive=False)
                if nested_container:
                    nodes = nested_container.find_all(['div'], class_=['content-box', 'tree-node'], recursive=False)

            if nodes:
                all_dialogues.extend(self._parse_linear_flow(nodes))

        # 2. Extract non-interactive dialogues
        collapse_modules = scope.select('.obc-tmpl-collapsePanel')
        for module in collapse_modules:
            # Check if this is a dialogue module by looking for "剧情对话" in title
            title_elem = module.select_one('.obc-tmpl-fold__title')
            if title_elem and '剧情对话' in title_elem.get_text(strip=True):
                paragraph_box = module.select_one('.obc-tmpl__paragraph-box')
                if paragraph_box:
                    all_dialogues.extend(self._parse_non_interactive_dialogue(paragraph_box))

        if all_dialogues:
            result["剧情对话"] = all_dialogues

    def _parse_linear_flow(self, nodes: List[bs4.Tag]) -> List[Dict[str, Any]]:
        """Parses a linear sequence of dialogue and option nodes."""
        flow = []
        for node in nodes:
            if 'content-box' in node.get('class', []):
                flow.extend(self._parse_dialogue_block(node))
                continue

            if 'tree-node' in node.get('class', []):
                option_items = node.find_all('div', class_='option-item', recursive=False)
                if option_items:
                    options_group = {
                        "type": "options",
                        "choices": [item.get_text(strip=True) for item in option_items],
                        "reply": []
                    }

                    # Look for direct reply content
                    reply_node = node.find('div', class_='content-box', recursive=False)
                    if reply_node:
                        options_group["reply"] = self._parse_dialogue_block(reply_node)

                    # Also look for nested reply content in tree-nodes
                    nested_reply_nodes = node.find_all('div', class_=['content-box', 'tree-node'], recursive=False)
                    if nested_reply_nodes:
                        nested_replies = self._parse_linear_flow(nested_reply_nodes)
                        options_group["reply"].extend(nested_replies)

                    flow.append(options_group)

                nested_nodes = node.find_all(['div'], class_=['content-box', 'tree-node'], recursive=False)
                if nested_nodes and not option_items:
                    flow.extend(self._parse_linear_flow(nested_nodes))

        return flow

    def _parse_dialogue_block(self, content_box: bs4.Tag) -> List[Dict[str, Any]]:
        """Parses a content-box into a list of dialogue items, handling multiple structures."""
        dialogues = []
        # Process h2 tags as scene separators
        for header in content_box.find_all('h2'):
            header_text = header.get_text(strip=True)
            if header_text:
                dialogues.append({"speaker": "场景标题", "text": header_text})

        for p_tag in content_box.find_all('p'):
            full_text = p_tag.get_text(strip=True)
            if not full_text:
                continue

            # Check for centered scene titles with strong tags
            if p_tag.get('style') and 'text-align: center' in p_tag.get('style', ''):
                strong_tag = p_tag.find('strong')
                if strong_tag:
                    dialogues.append({"speaker": "场景标题", "text": strong_tag.get_text(strip=True)})
                    continue

            # Check if this is wrapped in <em> for special dialogue
            em_tag = p_tag.find('em')
            is_special_dialogue = em_tag and em_tag.get_text(strip=True) == full_text

            speaker_tag = p_tag.find('strong')

            # Case 1: Speaker in <strong> tag
            if speaker_tag and not is_special_dialogue:
                speaker = speaker_tag.get_text(strip=True)
                text = full_text.replace(speaker, '', 1).lstrip('：:').strip()
                dialogues.append({"speaker": speaker, "text": text})
            # Case 2: Handle dialogue with colon separator (both span-wrapped and direct)
            elif '：' in full_text or ':' in full_text:
                # Split on the first colon (Chinese or English)
                colon = '：' if '：' in full_text else ':'
                parts = full_text.split(colon, 1)
                if len(parts) == 2:
                    potential_speaker = parts[0].strip()
                    dialogue_text = parts[1].strip()

                    # Only treat as speaker if it's a reasonable length (not a long sentence)
                    # and doesn't contain common punctuation that would indicate it's not a name
                    # Allow special speakers like "？？？", "???", etc.
                    is_special_speaker = potential_speaker in ['？？？', '???', '？', '?']
                    has_forbidden_punct = any(punct in potential_speaker for punct in ['。', '！', '，', '…', '.', '!', ','])

                    if (len(potential_speaker) <= 10 and
                        (is_special_speaker or not has_forbidden_punct) and
                        dialogue_text):  # Make sure there's actual dialogue content

                        # Mark as special dialogue if wrapped in <em>
                        if is_special_dialogue:
                            dialogues.append({"speaker": potential_speaker, "text": dialogue_text, "type": "special"})
                        else:
                            dialogues.append({"speaker": potential_speaker, "text": dialogue_text})
                    else:
                        speaker_type = "特殊对话" if is_special_dialogue else "旁白"
                        dialogues.append({"speaker": speaker_type, "text": full_text})
                else:
                    speaker_type = "特殊对话" if is_special_dialogue else "旁白"
                    dialogues.append({"speaker": speaker_type, "text": full_text})
            # Case 3: Narrator/Action text
            else:
                speaker_type = "特殊对话" if is_special_dialogue else "旁白"
                dialogues.append({"speaker": speaker_type, "text": full_text})
        return dialogues

    def _parse_non_interactive_dialogue(self, paragraph_box: bs4.Tag) -> List[Dict[str, Any]]:
        """Parses non-interactive dialogue from paragraph box, maintaining same format as interactive dialogue."""
        dialogues = []

        for p_tag in paragraph_box.find_all('p'):
            full_text = p_tag.get_text(strip=True)
            if not full_text:
                continue

            # Handle scene titles in <strong> tags
            strong_tag = p_tag.find('strong')
            if strong_tag and strong_tag.get_text(strip=True) == full_text:
                dialogues.append({"speaker": "场景标题", "text": full_text})
                continue

            # Handle traveler choices in <u> tags
            u_tag = p_tag.find('u')
            if u_tag:
                choices_text = u_tag.get_text(strip=True)
                if '/' in choices_text:
                    choices = [choice.strip() for choice in choices_text.split('/')]
                    dialogues.append({
                        "type": "options",
                        "choices": choices,
                        "reply": []
                    })
                    continue

            # Handle special dialogue in <em> tags
            em_tag = p_tag.find('em')
            if em_tag and em_tag.get_text(strip=True) == full_text:
                # Extract speaker and text from em content
                if '：' in full_text or ':' in full_text:
                    colon = '：' if '：' in full_text else ':'
                    parts = full_text.split(colon, 1)
                    if len(parts) == 2:
                        speaker = parts[0].strip()
                        text = parts[1].strip()
                        dialogues.append({"speaker": speaker, "text": text})
                        continue

                dialogues.append({"speaker": "特殊对话", "text": full_text})
                continue

            # Handle regular dialogue with speaker format
            if '：' in full_text or ':' in full_text:
                colon = '：' if '：' in full_text else ':'
                parts = full_text.split(colon, 1)
                if len(parts) == 2:
                    potential_speaker = parts[0].strip()
                    dialogue_text = parts[1].strip()

                    # Validate speaker name (similar logic to existing method)
                    # Allow special speakers like "？？？", "???", etc.
                    is_special_speaker = potential_speaker in ['？？？', '???', '？', '?']
                    has_forbidden_punct = any(punct in potential_speaker for punct in ['。', '！', '，', '…', '.', '!', ','])

                    if (len(potential_speaker) <= 10 and
                        (is_special_speaker or not has_forbidden_punct) and
                        dialogue_text):
                        dialogues.append({"speaker": potential_speaker, "text": dialogue_text})
                        continue

            # Default to narrator
            dialogues.append({"speaker": "旁白", "text": full_text})

        return dialogues

    def get_template(self) -> Dict[str, Any]:
        """
        返回任务解析器的JSON模板

        Returns:
            Dict[str, Any]: 任务数据模板
        """
        return {
            "任务标题": "请填写任务标题",
            "任务列表": [
                {
                    "名称": "请填写任务名称",
                    "任务概述": {
                        "前置任务": [
                            {"名称": "请填写前置任务名称"}
                        ],
                        "起始NPC": {"名称": "请填写起始NPC名称"},
                        "结束NPC": {"名称": "请填写结束NPC名称"},
                        "后续任务": [
                            {"名称": "请填写后续任务名称"}
                        ]
                    },
                    "触发条件": "请填写触发条件",
                    "等级限制": "请填写等级限制",
                    "特殊限制": "请填写特殊限制",
                    "任务过程": [
                        "请填写任务过程步骤"
                    ],
                    "剧情对话": [
                        {
                            "speaker": "请填写说话者",
                            "text": "请填写对话内容"
                        }
                    ]
                }
            ],
            "任务数量": 1
        }