from .base_parser import BaseParser
from bs4 import BeautifulSoup, Tag
import json

class RogueEventParser(BaseParser):
    """
    用于解析“模拟宇宙·事件图鉴”类型页面的解析器。
    """

    def parse(self, html: str) -> dict:
        """
        解析给定的URL，提取事件相关信息。
        """

        soup = self._create_soup(html)

        title = soup.select_one('h1.detail__title').get_text(strip=True) if soup.select_one('h1.detail__title') else "标题未找到"

        # 从URL中提取ID
        import re
        id_match = re.search(r'/(\d+)/detail', url)
        event_id = int(id_match.group(1)) if id_match else -1  # 使用-1作为默认值或错误标识

        # 提取事件发生地
        location = ""
        location_element = soup.select_one('div.detail__content td:nth-of-type(2) p')
        if location_element:
            location_text = location_element.get_text(strip=True)
            if "事件发生地：" in location_text:
                location = location_text.replace("事件发生地：", "").strip()

        outcomes_section = soup.select_one('div.obc-tmpl-relic__story')
        possible_outcomes = []
        if outcomes_section:
            for p in outcomes_section.select('p'):
                outcome_text = p.get_text(strip=True)
                if outcome_text:
                    possible_outcomes.append(outcome_text)

        # 使用新的对话树解析方法
        dialogue_tree = self._parse_dialogue_tree(soup)

        return {
            "id": event_id,
            "title": title,
            "location": location,
            "possible_outcomes": possible_outcomes,
            "dialogue_tree": dialogue_tree
        }

    @staticmethod
    def _parse_initial_dialogue(soup: BeautifulSoup) -> list:
        """提取初始对话内容"""
        initial_content = []
        # 定位初始对话容器
        initial_container = soup.select_one('div.int-dialog-flow--no-parent .int-dialog-flow__content')
        if initial_container:
            dialogue_node = initial_container.select_one('.obc-tmpl-mission__int-dialog__node-dialogue')
            if dialogue_node:
                # 复用已有的对话解析逻辑
                initial_content = RogueEventParser._parse_dialogue_node(dialogue_node)
        return initial_content

    @staticmethod
    def _parse_dialogue_node(dialogue_node: Tag):
        if not dialogue_node: return []

        dialogue_lines = []
        content_elements = dialogue_node.select('p')

        for element in content_elements:
            text = element.get_text(strip=True)
            if not text: continue

            # Special handling for dialogue lines marked by speakers in colorful tags
            speaker_tag = element.select_one('span.colorful-tag')
            if speaker_tag:
                speaker = speaker_tag.get_text(strip=True)
                # Extract text after the <br> tag
                br_tag = element.find('br')
                if br_tag and br_tag.next_sibling:
                    line = str(br_tag.next_sibling).strip()
                else: # Fallback
                    line = text.replace(speaker, '').strip()

                # The actual player choice text is often in a separate span
                choice_span = element.select_one('span[style*="background-color"]')
                if choice_span:
                    line = choice_span.get_text(strip=True)

                dialogue_lines.append({"type": "dialogue", "speaker": speaker, "line": line})
            elif '：' in text:
                speaker, line = text.split('：', 1)
                dialogue_lines.append({"type": "dialogue", "speaker": speaker.strip(), "line": line.strip()})
            else:
                dialogue_lines.append({"type": "narrator", "line": text})

        return dialogue_lines

    @staticmethod
    def _parse_dialogue_tree(soup: BeautifulSoup) -> dict:
        """解析完整的对话树结构，包含初始对话"""
        # 1. 提取初始对话内容
        initial_dialogue = RogueEventParser._parse_initial_dialogue(soup)

        # 2. 提取所有节点数据
        nodes_dict = {}
        all_target_ids = set()

        nodes_container = soup.select_one('ul.obc-tmpl-mission__int-dialog__nodes')
        if not nodes_container:
            # 如果没有节点容器，至少返回包含初始对话的根节点
            return {
                'id': 'root',
                'option_text': '',
                'dialogue': initial_dialogue,
                'options': []
            }

        for node in nodes_container.select('li.obc-tmpl-mission__int-dialog__node'):
            data_id = node.get('data-dialog-id', '')
            if not data_id:
                continue

            # 解析 data-dialog-id 格式: source_id:target_id1,target_id2,...
            if ':' in data_id:
                source_id, targets_part = data_id.split(':', 1)
                target_ids = [tid for tid in targets_part.split(',') if tid] if targets_part else []
            else:
                source_id = data_id
                target_ids = []

            # 收集所有目标ID，用于后续查找根节点
            all_target_ids.update(target_ids)

            # 提取选项文本
            option_node = node.select_one('.obc-tmpl-mission__int-dialog__node-option')
            option_text = option_node.get_text(strip=True) if option_node else ""

            # 提取对话内容
            dialogue_node = node.select_one('.obc-tmpl-mission__int-dialog__node-dialogue')
            dialogue_content = RogueEventParser._parse_dialogue_node(dialogue_node) if dialogue_node else []

            # 存储节点信息
            nodes_dict[source_id] = {
                'id': source_id,
                'option_text': option_text,
                'dialogue': dialogue_content,
                'children_ids': target_ids
            }

        # 3. 查找根节点 (没有作为目标ID出现的源ID)
        root_ids = set(nodes_dict.keys()) - all_target_ids
        if not root_ids:
            # 如果找不到根节点（理论上不应该发生），创建一个包含初始对话的虚拟根节点
            return {
                'id': 'root',
                'option_text': '',
                'dialogue': initial_dialogue,
                'options': []
            }

        root_id = root_ids.pop()  # 假设只有一个根节点

        # 4. 递归构建对话树
        def build_tree(node_id):
            if node_id not in nodes_dict:
                return None

            node_info = nodes_dict[node_id].copy()
            children = []

            for child_id in node_info['children_ids']:
                child_tree = build_tree(child_id)
                if child_tree:
                    children.append(child_tree)

            # 移除 children_ids，因为已经用 options 表示了
            del node_info['children_ids']
            node_info['options'] = children

            return node_info

        # 5. 构建完整的对话树并添加初始对话
        dialogue_tree = build_tree(root_id) or {}
        if initial_dialogue:
            # 将初始对话添加到根节点
            dialogue_tree['dialogue'] = initial_dialogue

        return dialogue_tree

    @staticmethod
    def _parse_dialogue_flow(soup: BeautifulSoup) -> list:
        """封装对话解析的完整流程"""
        branches_map = RogueEventParser._parse_branches(soup)
        dialogue_content = RogueEventParser._parse_main_flow_and_merge(soup, branches_map)
        return dialogue_content

    def get_template(self) -> dict:
        """
        返回模拟宇宙·事件图鉴解析器的JSON模板

        Returns:
            dict: 模拟宇宙·事件图鉴数据模板
        """
        return {
            "id": -1,
            "title": "请填写事件标题",
            "location": "请填写事件发生地",
            "possible_outcomes": [
                "请填写可能结果1",
                "请填写可能结果2"
            ],
            "dialogue_tree": {
                'id': 'root',
                'option_text': '',
                'dialogue': [
                    {
                        "type": "dialogue",
                        "speaker": "请填写说话者",
                        "line": "请填写对话内容"
                    }
                ],
                "options": [
                    {
                        "id": "请填写节点ID",
                        "option_text": "请填写选项文本",
                        "dialogue": [
                            {
                                "type": "dialogue",
                                "speaker": "请填写说话者",
                                "line": "请填写对话内容"
                            }
                        ],
                        "options": []
                    }
                ]
            }
        }
