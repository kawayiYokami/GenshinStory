import logging
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.quest_43 import Quest, SubQuest, DialogueEntry, DialogueChoice, QuestNPC
from giwiki_data_parser.services.dataloader import DataLoader

class QuestInterpreter:
    """任务解释器"""
    
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)
    
    def interpret(self, data: Dict[str, Any]) -> Optional[Quest]:
        """解析单个任务数据 - 公共接口"""
        return self._interpret_single(data)
    
    def interpret_all(self) -> List[Quest]:
        """解析所有任务数据"""
        quests = []
        raw_data_iterator = self.loader.get_quests()
        
        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                quest = self._interpret_single(data, file_path)
                if quest:
                    quests.append(quest)
            except Exception as e:
                self.logger.error(f"解析任务数据时出错: {e}")
        
        self.logger.info(f"成功解析 {len(quests)} 个任务")
        return quests
    
    def _interpret_single(self, quest_file_data: Dict[str, Any], file_path: str = "") -> Optional[Quest]:
        """解析单个任务文件（完整JSON文件结构）"""
        try:
            # 提取任务标题和任务列表
            quest_title = quest_file_data.get("任务标题", "")
            sub_quest_list = quest_file_data.get("任务列表", [])

            if not sub_quest_list:
                self.logger.warning("任务列表为空")
                return None

            # 解析所有子任务
            sub_quests = []
            for sub_quest_data in sub_quest_list:
                sub_quest = self._parse_sub_quest(sub_quest_data)
                if sub_quest:
                    sub_quests.append(sub_quest)

            if not sub_quests:
                self.logger.warning("没有成功解析任何子任务")
                return None

            # 整合子任务为完整任务
            final_quest = self._merge_sub_quests_to_quest(quest_title, sub_quests, file_path)

            return final_quest

        except Exception as e:
            self.logger.error(f"解析任务文件时出错: {e}")
            return None

    def _parse_sub_quest(self, sub_quest_data: Dict[str, Any]) -> Optional[SubQuest]:
        """解析单个子任务数据"""
        try:
            # 解析起始和结束NPC
            start_npc = None
            start_npc_data = sub_quest_data.get("任务概述", {}).get("起始NPC", {})
            if isinstance(start_npc_data, dict) and start_npc_data.get("名称"):
                start_npc = QuestNPC(
                    name=start_npc_data["名称"],
                    link=start_npc_data.get("链接")
                )

            end_npc = None
            end_npc_data = sub_quest_data.get("任务概述", {}).get("结束NPC", {})
            if isinstance(end_npc_data, dict) and end_npc_data.get("名称"):
                end_npc = QuestNPC(
                    name=end_npc_data["名称"],
                    link=end_npc_data.get("链接")
                )

            # 解析任务过程
            quest_steps = sub_quest_data.get("任务过程", [])
            if not isinstance(quest_steps, list):
                quest_steps = []

            # 解析剧情对话
            dialogue_content = []
            dialogue_data = sub_quest_data.get("剧情对话", [])

            # 扁平化对话树结构
            flattened_dialogues = self._flatten_dialogue_tree(dialogue_data)

            for dialogue_item in flattened_dialogues:
                if isinstance(dialogue_item, dict):
                    # 创建对话条目，直接使用原始数据
                    dialogue_entry = DialogueEntry(**dialogue_item)
                    dialogue_content.append(dialogue_entry)

            # 创建子任务对象
            sub_quest = SubQuest(
                name=sub_quest_data.get("名称", ""),
                special_requirements=sub_quest_data.get("特殊限制"),
                quest_steps=quest_steps,
                start_npc=start_npc,
                end_npc=end_npc,
                dialogue_content=dialogue_content
            )

            return sub_quest

        except Exception as e:
            self.logger.error(f"解析子任务数据时出错: {e}")
            return None

    def _merge_sub_quests_to_quest(self, quest_title: str, sub_quests: List[SubQuest], file_path: str = "") -> Quest:
        """将多个子任务整合成完整的任务对象"""
        try:
            # 创建完整任务对象（只包含任务标题和子任务列表）
            quest = Quest(
                name=quest_title,
                sub_quests=sub_quests
            )

            # 从文件路径设置ID
            if file_path:
                quest.set_id_from_filename(file_path)

            return quest

        except Exception as e:
            self.logger.error(f"整合子任务时出错: {e}")
            raise

    def _flatten_dialogue_tree(self, dialogue_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将树状对话结构扁平化为线性对话列表"""
        flattened = []

        for item in dialogue_data:
            if not isinstance(item, dict):
                continue

            # 处理普通对话
            if item.get("speaker") and item.get("text"):
                # 添加特殊类型标记
                dialogue_item = item.copy()
                if item.get("type") == "special":
                    dialogue_item["special_type"] = "special"
                flattened.append(dialogue_item)

            # 处理选择项
            elif item.get("type") == "options" and item.get("choices"):
                # 添加每个选择项（不添加系统提示和数字编号）
                for choice in item["choices"]:
                    flattened.append({
                        "speaker": "选项",
                        "text": choice,
                        "dialogue_type": "choice"
                    })

                # 递归处理回复内容（默认选择第一项的后续内容）
                if item.get("reply"):
                    reply_dialogues = self._flatten_dialogue_tree(item["reply"])
                    if reply_dialogues:
                        # 直接添加回复内容，不添加分隔符
                        flattened.extend(reply_dialogues)

            # 处理场景标题
            elif item.get("speaker") == "场景标题":
                flattened.append({
                    "speaker": "场景",
                    "text": f"=== {item.get('text', '')} ===",
                    "dialogue_type": "scene"
                })

        return flattened