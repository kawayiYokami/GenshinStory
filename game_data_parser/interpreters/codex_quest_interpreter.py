import json
import os
import re
from typing import Dict, Any, List, Optional

from game_data_parser.models import Quest, QuestStep, DialogueNode
from ..services.text_map_service import TextMapService
from ..dataloader import DataLoader

class CodexQuestInterpreter:
    """
    专门用于解析 AnimeGameData/BinOutput/CodexQuest/ 目录下的任务文件。
    
    该解析器采用“文本替换”策略：
    1. 将整个JSON文件作为纯文本读取。
    2. 使用正则表达式查找所有 "textId": <hash> 的实例。
    3. 从TextMapService中查找对应的文本，并替换回原始文本字符串中。
    4. 将被修改过的、包含所有真实文本的字符串，最终解析为JSON对象。
    5. 将解析出的JSON对象映射到内部数据模型。
    """
    def __init__(self, text_map_service: TextMapService, loader: DataLoader):
        self.text_map_service = text_map_service
        self.loader = loader

    def _read_and_replace_text(self, relative_path: str) -> Optional[Dict[str, Any]]:
        """读取文件，替换textId哈希，然后解析为JSON。"""
        content = self.loader.get_text_file(relative_path)
        if not content:
            return None

        def replacer(match):
            hash_id = match.group(1)
            replacement = self.text_map_service.get(int(hash_id), "")
            # 使用 json.dumps 确保替换的文本是有效的JSON字符串（带引号，转义等）
            return f'"textId": {json.dumps(replacement, ensure_ascii=False)}'

        # 正则表达式查找 "textId": <数字> 结构
        # 使用回调函数进行替换
        modified_content = re.sub(r'"textId":\s*(\d+)', replacer, content)

        try:
            return json.loads(modified_content)
        except json.JSONDecodeError:
            # 如果替换后JSON无效，可以添加日志记录
            return None

    def _map_to_model(self, data: Dict[str, Any]) -> Quest:
        """将解析后的JSON字典映射到Quest数据模型。"""
        
        quest_steps = []
        for sub_quest_data in data.get("subQuests", []):
            dialogue_nodes = []
            for item_data in sub_quest_data.get("items", []):
                
                # 处理旁白
                if item_data.get("itemType") == "Narratage" or "texts" in item_data:
                    for text_data in item_data.get("texts", []):
                        dialogue_nodes.append(DialogueNode(
                            id=item_data.get("itemId"),
                            speaker="旁白",
                            content=text_data.get("textId", ""),
                            node_type="narratage"
                        ))
                    continue

                # 处理对话
                speaker = item_data.get("speakerText", {}).get("textId", "未知")
                dialogs_data = item_data.get("dialogs", [])

                if item_data.get("itemType") == "MultiDialog" and len(dialogs_data) > 1:
                    # 玩家选项
                    player_node = DialogueNode(
                        id=item_data.get("itemId"),
                        speaker="旅行者",
                        content="（选择一个选项）",
                        node_type="dialogue"
                    )
                    for dialog_data in dialogs_data:
                        option_content = dialog_data.get("text", {}).get("textId", "")
                        if option_content:
                            player_node.options.append(DialogueNode(
                                id=item_data.get("itemId"),
                                speaker="旅行者",
                                content=option_content,
                                node_type="option"
                            ))
                    
                    if player_node.options:
                        dialogue_nodes.append(player_node)
                else:
                    # 单句对话
                    for dialog_data in dialogs_data:
                        dialogue_nodes.append(DialogueNode(
                            id=item_data.get("itemId"),
                            speaker=speaker,
                            content=dialog_data.get("text", {}).get("textId", ""),
                            node_type="dialogue"
                        ))

            quest_steps.append(QuestStep(
                step_id=sub_quest_data.get("subId", 0),
                title=sub_quest_data.get("subQuestTitle", {}).get("textId"),
                dialogue_nodes=dialogue_nodes
            ))

        quest_title = data.get("mainQuestTitle", {}).get("textId", "")
        chapter_title = data.get("chapterTitle", {}).get("textId", "")

        # 修正：如果主任务标题和章节标题一样，并且存在子任务，则尝试使用第一个子任务的标题
        if quest_title and quest_title == chapter_title:
            first_sub_quest = next(iter(data.get("subQuests", [])), None)
            if first_sub_quest:
                sub_quest_title = first_sub_quest.get("subQuestTitle", {}).get("textId")
                if sub_quest_title:
                    quest_title = sub_quest_title

        return Quest(
            quest_id=data["mainQuestId"],
            quest_title=quest_title,
            quest_description=data.get("mainQuestDesp", {}).get("textId", ""),
            chapter_id=data.get("chapterId", 0),
            chapter_title=chapter_title,
            chapter_num=data.get("chapterNum", {}).get("textId"),
            series_id=data.get("series", 0),
            steps=quest_steps,
            source_json=f"{data['mainQuestId']}.json (Codex)"
        )

    def interpret(self, quest_id: int) -> Optional[Quest]:
        """
        解析指定ID的CodexQuest任务。
        """
        # 构建相对于数据根目录的路径
        relative_path = f"BinOutput/CodexQuest/{quest_id}.json"
        quest_data = self._read_and_replace_text(relative_path)

        if not quest_data:
            return None

        return self._map_to_model(quest_data)
