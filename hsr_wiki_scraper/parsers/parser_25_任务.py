from .base_parser import BaseParser
from bs4 import BeautifulSoup, Tag
import json


class TaskParser(BaseParser):
    """
    用于解析“任务”类型页面的解析器。
    完全照搬 get_quest_content.py 的逻辑。
    """

    def parse(self, html: str) -> dict:
        """
        解析给定的URL，提取任务相关信息。
        完全照搬 get_quest_content.py 的 scrape_story_content 函数。
        """
        soup = self._create_soup(html)

        title = soup.select_one('h1.detail__title').get_text(strip=True) or "标题未找到"
        metadata = self._parse_metadata(soup)
        dialogue = self._parse_dialogue_flow(soup)

        # 精准提取 'process'：一个 description 后面如果紧跟着一个 quote，才被视为一个任务过程
        process = []
        for i, item in enumerate(dialogue):
            if item.get('type') == 'description':
                # 检查列表中的下一个元素是否存在且类型为 'quote'
                if (i + 1) < len(dialogue) and dialogue[i+1].get('type') == 'quote':
                    process.append(item['text'])

        return {
            "title": title,
            "metadata": metadata,
            "process": process,
            "dialogue": dialogue # 添加源URL以便追溯
        }

    # --- 以下是从 get_quest_content.py 移植过来的核心解析函数 ---
    # 并将它们转换为 TaskParser 的静态方法

    @staticmethod
    def _parse_dialogue_node(dialogue_node: Tag):
        """
        辅助函数V3：精确区分h3, blockquote, p标签，并新增quote类型。
        """
        if not dialogue_node: return []

        dialogue_lines = []
        content_elements = dialogue_node.select('h3, p, blockquote')

        for element in content_elements:
            text = element.get_text(strip=True)
            if not text: continue

            # 精确映射HTML标签到数据类型
            if element.name == 'h3':
                dialogue_lines.append({"type": "description", "text": text})
            elif element.name == 'blockquote':
                dialogue_lines.append({"type": "quote", "text": text})
            elif element.name == 'p':
                if '：' in text:
                    speaker, line = text.split('：', 1)
                    dialogue_lines.append({"type": "dialogue", "speaker": speaker.strip(), "line": line.strip()})
                else:
                    dialogue_lines.append({"type": "narrator", "line": text})

        return dialogue_lines

    @staticmethod
    def _parse_branches(soup: BeautifulSoup):
        """解析隐藏的UL，返回一个'选项->回复列表'的映射字典。"""
        branches_map = {}
        nodes_container = soup.select_one('ul.obc-tmpl-mission__int-dialog__nodes')
        if not nodes_container: return branches_map

        for node in nodes_container.select('li.obc-tmpl-mission__int-dialog__node'):
            option_node = node.select_one('.obc-tmpl-mission__int-dialog__node-option')
            dialogue_node = node.select_one('.obc-tmpl-mission__int-dialog__node-dialogue')

            if option_node and dialogue_node:
                option_text = option_node.get_text(strip=True)
                dialogue_data_list = TaskParser._parse_dialogue_node(dialogue_node)
                if dialogue_data_list:
                    branches_map[option_text] = dialogue_data_list
        return branches_map

    @staticmethod
    def _parse_main_flow_and_merge(soup: BeautifulSoup, branches_map: dict):
        """
        遍历主干流程，并智能地将'主线选项'与紧随其后的对话块关联起来。
        """
        full_content = []
        main_container = soup.select_one('div.obc-tmpl-mission__int-dialog__main')
        if not main_container: return full_content

        flow_blocks = main_container.select('.int-dialog-flow')
        i = 0
        while i < len(flow_blocks):
            block = flow_blocks[i]

            content_node = block.select_one('.int-dialog-flow__content')
            if content_node:
                dialogue_data = TaskParser._parse_dialogue_node(content_node)
                full_content.extend(dialogue_data)

            options_node = block.select_one('.int-dialog-flow__options')
            if options_node:
                choices = [opt.get_text(strip=True) for opt in options_node.select('.int-dialog-flow__option__text')]
                if choices:
                    enriched_choices = []
                    has_main_line_option = False
                    for choice_text in choices:
                        choice_obj = {"option": choice_text}
                        if choice_text in branches_map:
                            choice_obj["reply"] = branches_map[choice_text]
                        else:
                            has_main_line_option = True
                        enriched_choices.append(choice_obj)

                    if has_main_line_option and (i + 1) < len(flow_blocks):
                        next_block_content = flow_blocks[i+1].select_one('.int-dialog-flow__content')
                        if next_block_content:
                            reply_lines = TaskParser._parse_dialogue_node(next_block_content)
                            for choice in enriched_choices:
                                if "reply" not in choice:
                                    choice["reply"] = reply_lines
                            i += 1

                    full_content.append({"type": "options_group", "choices": enriched_choices})
            i += 1

        return full_content

    @staticmethod
    def _parse_metadata(soup: BeautifulSoup) -> dict:
        """解析任务信息表格"""
        metadata = {}
        table = soup.select_one('div.table-wrapper table')
        if not table: return metadata

        for row in table.select('tr'):
            header = row.select_one('th')
            cell = row.select_one('td')
            if header and cell:
                key = header.get_text(strip=True)
                value = cell.get_text(strip=True)
                metadata[key] = value
        return metadata

    @staticmethod
    def _parse_dialogue_flow(soup: BeautifulSoup) -> list:
        """封装对话解析的完整流程"""
        branches_map = TaskParser._parse_branches(soup)
        dialogue_content = TaskParser._parse_main_flow_and_merge(soup, branches_map)
        return dialogue_content

    def get_template(self) -> dict:
        """
        返回任务解析器的JSON模板

        Returns:
            dict: 任务数据模板
        """
        return {
            "title": "请填写任务标题",
            "metadata": {
                "请填写元数据键": "请填写元数据值"
            },
            "process": [
                "请填写任务过程步骤1",
                "请填写任务过程步骤2"
            ],
            "dialogue": [
                {
                    "type": "description",
                    "text": "请填写描述文本"
                },
                {
                    "type": "quote",
                    "text": "请填写引用文本"
                },
                {
                    "type": "dialogue",
                    "speaker": "请填写说话者",
                    "line": "请填写对话内容"
                },
                {
                    "type": "narrator",
                    "line": "请填写旁白内容"
                },
                {
                    "type": "options_group",
                    "choices": [
                        {
                            "option": "请填写选项文本",
                            "reply": [
                                {
                                    "type": "description",
                                    "text": "请填写回复描述"
                                }
                            ]
                        }
                    ]
                }
            ]
        }