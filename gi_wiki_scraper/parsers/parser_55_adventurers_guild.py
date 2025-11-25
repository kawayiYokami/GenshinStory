"""
Parser for Genshin Impact wiki pages under the 'Adventurers' Guild' (冒险家协会) category.
ID: 55_adventurers_guild

Enhanced with complete dialogue tree parsing and multi-task support from parser_43_quest.py
"""
from typing import Dict, Any, List
from .base_parser import BaseParser
from bs4 import Tag, BeautifulSoup
import bs4


class Parser55AdventurersGuild(BaseParser):
    """
    Enhanced parser for 'Adventurers' Guild' wiki pages with complete dialogue tree support.
    Supports module-group structures and complex recursive dialogue parsing.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of an Adventurers' Guild page with enhanced module-group support.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data with multiple tasks support.
        """
        soup = self._create_soup(html)

        # Find all module groups (multi-task support)
        module_groups = soup.select('div[id^="module-group-"]')

        if not module_groups:
            # Fallback to single task mode if no module groups found
            task_data = self._parse_single_task(soup)
            return {
                "任务标题": self._extract_main_title(soup),
                "任务列表": [task_data] if task_data and task_data.get("名称") else [],
                "任务数量": 1 if task_data and task_data.get("名称") else 0
            }

        # Parse each module group as a separate task
        tasks = []
        for group in module_groups:
            task_data = self._parse_module_group(group)
            if task_data and task_data.get("名称"):  # Only add if task has a name
                tasks.append(task_data)

        # Return structure with multiple tasks
        return {
            "任务标题": self._extract_main_title(soup),
            "任务列表": tasks,
            "任务数量": len(tasks)
        }

    def _extract_main_title(self, soup) -> str:
        """Extract main page title"""
        title_tag = soup.select_one('h1.detail__title')
        return title_tag.get_text(strip=True) if title_tag else ""

    def _parse_module_group(self, module_group) -> Dict[str, Any]:
        """Parse a single module group as a task"""
        task_data = {
            "名称": "",
            "触发条件": "",
            "剧情对话": {"对话树": []},
            "任务过程": []
        }

        # Parse all modules within this group
        modules = module_group.select('div[id^="module-"]')
        for module in modules:
            module_type = self._identify_module_type(module)
            self._parse_module_by_type(module, module_type, task_data)

        return task_data

    def _identify_module_type(self, module) -> str:
        """Identify module type based on content"""
        # Base info module
        if module.select_one('.obc-tmpl-baseInfo'):
            return 'base_info'

        # Interactive dialogue module
        if module.select_one('.obc-tmpl-interactiveDialogue'):
            return 'interactive_dialogue'

        # Collapse panel modules (need to check title)
        if module.select_one('.obc-tmpl-collapsePanel'):
            title_elem = module.select_one('.obc-tmpl-fold__title span')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                if '过程' in title_text:
                    return 'quest_process'
                elif '奖励' in title_text:
                    return 'quest_rewards'

        # Map description module
        if module.select_one('.obc-tmpl-mapDesc'):
            return 'map_description'

        return 'unknown'

    def _parse_module_by_type(self, module, module_type: str, task_data: Dict[str, Any]) -> None:
        """Parse module based on its type"""
        if module_type == 'base_info':
            self._parse_base_info_module(module, task_data)
        elif module_type == 'interactive_dialogue':
            self._parse_interactive_dialogue_module(module, task_data)
        elif module_type == 'quest_process':
            self._parse_quest_process_module(module, task_data)
        elif module_type == 'map_description':
            self._parse_map_description_module(module, task_data)
        elif module_type == 'quest_rewards':
            self._parse_quest_rewards_module(module, task_data)

    def _parse_base_info_module(self, module, task_data: Dict[str, Any]) -> None:
        """Parse base info module"""
        # Extract quest name from h2
        name_tag = module.select_one('h2.wiki-h2')
        if name_tag:
            task_data["名称"] = name_tag.get_text(strip=True)

        # Extract trigger conditions
        trigger_tags = module.select('table tbody tr')
        for tag in trigger_tags:
            cells = tag.find_all('td')
            if len(cells) >= 2:
                if "触发条件" in cells[0].get_text(strip=True):
                    task_data["触发条件"] = cells[1].get_text(strip=True)
                    break

    def _parse_interactive_dialogue_module(self, module, task_data: Dict[str, Any]) -> None:
        """Parse interactive dialogue module with complete recursive support"""
        tree_container = module.select_one('.tree-wrapper')
        if not tree_container:
            return

        nodes = self._get_dialogue_nodes_enhanced(tree_container)
        if nodes:
            dialogues = self._parse_linear_flow_enhanced(nodes)
            task_data["剧情对话"]["对话树"] = dialogues

    def _parse_quest_process_module(self, module, task_data: Dict[str, Any]) -> None:
        """Parse quest process module"""
        process_tags = module.select('.obc-tmpl__paragraph-box p')
        for tag in process_tags:
            text = tag.get_text(strip=True)
            if text:
                task_data["任务过程"].append(text)

    def _parse_map_description_module(self, module, task_data: Dict[str, Any]) -> None:
        """Parse map description module - 仅解析但不输出"""
        # 解析地图信息但不存储到结果中
        img_tags = module.select('picture source')
        for img_tag in img_tags:
            if img_tag.get('srcset'):
                # 解析完成但不添加到task_data
                pass

    def _parse_quest_rewards_module(self, module, task_data: Dict[str, Any]) -> None:
        """Parse quest rewards module - 仅解析但不输出"""
        # 解析奖励信息但不存储到结果中
        reward_rows = module.select('.table-wrapper table tbody tr')[1:]  # Skip header
        for row in reward_rows:
            cells = row.find_all('td')
            if len(cells) >= 6:
                # 解析完成但不添加到task_data
                pass

    def _parse_single_task(self, soup) -> Dict[str, Any]:
        """Fallback method for single task parsing"""
        result = {
            "名称": "",
            "触发条件": "",
            "剧情对话": {"对话树": []},
            "任务过程": []
        }

        # Extract name
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["名称"] = name_tag.get_text(strip=True)

        # Extract basic info
        self._extract_basic_info_legacy(soup, result)

        # Extract map descriptions
        self._extract_map_descriptions(soup, result)

        # Extract dialogue tree
        self._extract_dialogue_tree_enhanced(soup, result)

        # Extract quest process
        self._extract_quest_process(soup, result)

        # Extract quest rewards
        self._extract_quest_rewards(soup, result)

        return result

    def _extract_basic_info_legacy(self, soup, result: Dict[str, Any]) -> None:
        """Legacy basic info extraction for fallback mode"""
        trigger_tags = soup.select('.obc-tmpl-baseInfo table tbody tr')
        for tag in trigger_tags:
            cells = tag.find_all('td')
            if len(cells) >= 2:
                if "触发条件" in cells[0].get_text(strip=True):
                    result["触发条件"] = cells[1].get_text(strip=True)
                    break


    # === Enhanced Dialogue Parsing Methods (Transplanted from parser_43_quest.py) ===

    def _get_dialogue_nodes_enhanced(self, tree_container) -> List[Tag]:
        """Enhanced node retrieval for dialogue parsing"""
        # Try primary container first
        nodes = tree_container.find_all(['div'], class_=['content-box', 'tree-node'], recursive=False)
        if nodes:
            return nodes

        # Fallback to nested container
        nested_container = tree_container.find('div', class_='tree-node', recursive=False)
        if nested_container:
            return nested_container.find_all(['div'], class_=['content-box', 'tree-node'], recursive=False)

        return []

    def _parse_linear_flow_enhanced(self, nodes: List[Tag]) -> List[Dict[str, Any]]:
        """Enhanced linear flow parsing with full recursive support"""
        flow = []
        for node in nodes:
            if 'content-box' in node.get('class', []):
                flow.extend(self._parse_dialogue_block_enhanced(node))
                continue

            if 'tree-node' in node.get('class', []):
                nested_flow = self._process_tree_node_recursively(node)
                flow.extend(nested_flow)

        return flow

    def _process_tree_node_recursively(self, tree_node: Tag) -> List[Dict[str, Any]]:
        """Recursively process tree nodes with full complexity support"""
        result = []

        # Handle option items
        option_items = tree_node.find_all('div', class_='option-item', recursive=False)
        if option_items:
            options_group = {
                "type": "options",
                "choices": [item.get_text(strip=True) for item in option_items],
                "reply": []
            }

            # Handle direct reply content
            reply_node = tree_node.find('div', class_='content-box', recursive=False)
            if reply_node:
                options_group["reply"] = self._parse_dialogue_block_enhanced(reply_node)

            # Handle nested nodes (both content-box and tree-node)
            nested_nodes = tree_node.find_all(['div'], class_=['content-box', 'tree-node'], recursive=False)
            for nested_node in nested_nodes:
                if 'content-box' in nested_node.get('class', []):
                    # Skip already processed reply node
                    if nested_node != reply_node:
                        options_group["reply"].extend(self._parse_dialogue_block_enhanced(nested_node))
                elif 'tree-node' in nested_node.get('class', []):
                    # Recursively process nested tree nodes
                    nested_result = self._parse_linear_flow_enhanced([nested_node])
                    options_group["reply"].extend(nested_result)

            result.append(options_group)

        # Handle nested nodes without options
        nested_nodes = tree_node.find_all(['div'], class_=['content-box', 'tree-node'], recursive=False)
        if nested_nodes and not option_items:
            result.extend(self._parse_linear_flow_enhanced(nested_nodes))

        return result

    def _parse_dialogue_block_enhanced(self, content_box: Tag) -> List[Dict[str, Any]]:
        """Enhanced dialogue block parsing with full text analysis"""
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
            # Case 2: Handle dialogue with colon separator
            elif '：' in full_text or ':' in full_text:
                colon = '：' if '：' in full_text else ':'
                parts = full_text.split(colon, 1)
                if len(parts) == 2:
                    potential_speaker = parts[0].strip()
                    dialogue_text = parts[1].strip()

                    # Validate speaker name
                    is_special_speaker = potential_speaker in ['？？？', '???', '？', '?']
                    has_forbidden_punct = any(punct in potential_speaker for punct in ['。', '！', '，', '…', '.', '!', ','])

                    if (len(potential_speaker) <= 10 and
                        (is_special_speaker or not has_forbidden_punct) and
                        dialogue_text):

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

    def _parse_non_interactive_dialogue(self, paragraph_box: Tag) -> List[Dict[str, Any]]:
        """Parse non-interactive dialogue with full format support"""
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

                    # Validate speaker name
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

    def _extract_dialogue_tree_enhanced(self, soup, result: Dict[str, Any]) -> None:
        """Enhanced dialogue tree extraction with both interactive and non-interactive support"""
        all_dialogues = []

        # 1. Extract interactive dialogues
        interactive_modules = soup.select('.obc-tmpl-interactiveDialogue')
        for module in interactive_modules:
            tree_container = module.select_one('.tree-wrapper')
            if not tree_container:
                continue

            nodes = self._get_dialogue_nodes_enhanced(tree_container)
            if nodes:
                all_dialogues.extend(self._parse_linear_flow_enhanced(nodes))

        # 2. Extract non-interactive dialogues from collapse panels
        collapse_modules = soup.select('.obc-tmpl-collapsePanel')
        for module in collapse_modules:
            title_elem = module.select_one('.obc-tmpl-fold__title')
            if title_elem and '剧情对话' in title_elem.get_text(strip=True):
                paragraph_box = module.select_one('.obc-tmpl__paragraph-box')
                if paragraph_box:
                    all_dialogues.extend(self._parse_non_interactive_dialogue(paragraph_box))

        if all_dialogues:
            result["剧情对话"]["对话树"] = all_dialogues

    def get_template(self) -> Dict[str, Any]:
        """
        返回冒险家协会解析器的JSON模板

        Returns:
            Dict[str, Any]: 冒险家协会数据模板
        """
        return {
            "任务标题": "请填写任务标题",
            "任务列表": [
                {
                    "名称": "请填写任务名称",
                    "触发条件": "请填写触发条件",
                    "剧情对话": {
                        "对话树": [
                            {
                                "speaker": "请填写说话者",
                                "text": "请填写对话内容"
                            }
                        ]
                    },
                    "任务过程": [
                        "请填写任务过程步骤"
                    ]
                }
            ],
            "任务数量": 1
        }