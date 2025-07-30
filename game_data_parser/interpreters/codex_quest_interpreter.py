from typing import Dict, Any, List, Optional

from game_data_parser.models import Quest, QuestStep, DialogueNode
from ..services.text_map_service import TextMapService
from ..dataloader import DataLoader
from ..utils.text_transformer import transform_text

class CodexQuestInterpreter:
    """
    专门用于解析 AnimeGameData/BinOutput/CodexQuest/ 目录下的任务文件。
    
    该解析器采用标准的“加载-解析-映射”流程：
    1. 使用 DataLoader 加载并解析原始JSON文件。
    2. 遍历解析后的数据结构。
    3. 按需调用 TextMapService 将文本哈希转换为真实文本。
    4. 将数据映射到内部标准数据模型 (Quest, QuestStep, DialogueNode)。
    """
    def __init__(self, text_map_service: TextMapService, loader: DataLoader):
        self.text_map_service = text_map_service
        self.loader = loader

    def _get_text(self, text_id: int) -> str:
        """安全地获取原始文本，并进行清洗和转换。"""
        raw_text = self.text_map_service.get(text_id, "")
        # 调用通用转换工具处理占位符等
        transformed_text, _ = transform_text(raw_text)
        return transformed_text

    def _map_to_model(self, data: Dict[str, Any]) -> Quest:
        """将解析后的JSON字典映射到Quest数据模型。"""
        
        quest_steps = []
        # 使用 enumerate 来为没有 subId 的步骤生成一个唯一的、有序的ID
        for i, sub_quest_data in enumerate(data.get("subQuests", [])):
            dialogue_nodes = []
            for item_data in sub_quest_data.get("items", []):
                
                item_id = item_data.get("itemId")

                # 处理旁白
                if item_data.get("itemType") == "Narratage" or "texts" in item_data:
                    for text_data in item_data.get("texts", []):
                        dialogue_nodes.append(DialogueNode(
                            id=item_id,
                            speaker="旁白",
                            content=self._get_text(text_data.get("textId")),
                            node_type="narratage"
                        ))
                    continue

                # 处理对话
                speaker_hash = item_data.get("speakerText", {}).get("textId")
                speaker = self._get_text(speaker_hash) if speaker_hash else "未知"
                
                # 标准化说话人名称
                if item_data.get("speakerText", {}).get("textType") == "SpeakerPlayer":
                    speaker = "旅行者"

                dialogs_data = item_data.get("dialogs", [])

                if item_data.get("itemType") == "MultiDialog":
                    # 【新】扁平化处理玩家选项，不再创建带占位符的父节点
                    for dialog_data in dialogs_data:
                        option_content = self._get_text(dialog_data.get("text", {}).get("textId"))
                        if option_content:
                            dialogue_nodes.append(DialogueNode(
                                id=item_id,
                                speaker=speaker, # speaker 在外部已被正确设为“旅行者”
                                content=option_content,
                                node_type="option"
                            ))
                else:
                    # 单句对话或旁白
                    for dialog_data in dialogs_data:
                        dialogue_nodes.append(DialogueNode(
                            id=item_id,
                            speaker=speaker,
                            content=self._get_text(dialog_data.get("text", {}).get("textId")),
                            node_type="dialogue"
                        ))

            step_title = self._get_text(sub_quest_data.get("subQuestTitle", {}).get("textId"))
            quest_steps.append(QuestStep(
                # 使用索引 i + 1 作为 step_id，确保其唯一且从1开始
                step_id=i + 1,
                title=step_title,
                # 将标题也作为描述，以兼容旧模型
                step_description=step_title,
                dialogue_nodes=dialogue_nodes
            ))

        quest_title = self._get_text(data.get("mainQuestTitle", {}).get("textId"))
        chapter_title = self._get_text(data.get("chapterTitle", {}).get("textId"))

        return Quest(
            quest_id=data["mainQuestId"],
            quest_title=quest_title,
            quest_description=self._get_text(data.get("mainQuestDesp", {}).get("textId")),
            chapter_id=data.get("chapterId"),
            chapter_title=chapter_title,
            chapter_num=self._get_text(data.get("chapterNum", {}).get("textId")),
            series_id=data.get("series"),
            steps=quest_steps,
            source_json=f"{data['mainQuestId']}.json (Codex)"
        )

    def interpret(self, quest_id: int) -> Optional[Quest]:
        """
        解析指定ID的CodexQuest任务。
        """
        relative_path = f"BinOutput/CodexQuest/{quest_id}.json"
        # 使用标准的 get_json 方法加载数据
        quest_data = self.loader.get_json(relative_path)

        if not quest_data:
            return None

        # 将解析后的原始字典传递给映射函数
        return self._map_to_model(quest_data)
