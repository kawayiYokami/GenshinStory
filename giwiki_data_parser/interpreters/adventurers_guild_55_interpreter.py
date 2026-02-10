import logging
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.adventurers_guild_55 import AdventurerGuild, AdventurerGuildSubTask, DialogueEntry, DialogueChoice
from giwiki_data_parser.services.dataloader import DataLoader

class AdventurerGuildInterpreter:
    """冒险家协会解释器"""

    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)

    def interpret(self, data: Dict[str, Any]) -> Optional[AdventurerGuild]:
        """解析单个冒险家协会数据 - 公共接口"""
        return self._interpret_single(data)

    def interpret_all(self) -> List[AdventurerGuild]:
        """解析所有冒险家协会数据"""
        guilds = []
        raw_data_iterator = self.loader.get_adventurer_guild()

        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                guild = self._interpret_single(data, file_path)
                if guild:
                    guilds.append(guild)
            except Exception as e:
                self.logger.error(f"解析冒险家协会数据时出错: {e}")

        self.logger.info(f"成功解析 {len(guilds)} 个冒险家协会任务")
        return guilds

    def _interpret_single(self, guild_file_data: Dict[str, Any], file_path: str = "") -> Optional[AdventurerGuild]:
        """解析单个冒险家协会文件（完整JSON文件结构）"""
        try:
            # 提取任务标题和任务列表
            guild_title = guild_file_data.get("任务标题", "")
            sub_task_list = guild_file_data.get("任务列表", [])

            if not sub_task_list:
                self.logger.warning("任务列表为空")
                return None

            # 解析所有子任务
            sub_tasks = []
            for sub_task_data in sub_task_list:
                sub_task = self._parse_sub_task(sub_task_data)
                if sub_task:
                    sub_tasks.append(sub_task)

            if not sub_tasks:
                self.logger.warning("没有成功解析任何子任务")
                return None

            # 整合子任务为完整冒险家协会任务
            final_guild = self._merge_sub_tasks_to_guild(guild_title, sub_tasks, file_path)

            return final_guild

        except Exception as e:
            self.logger.error(f"解析冒险家协会文件时出错: {e}")
            return None

    def _parse_sub_task(self, sub_task_data: Dict[str, Any]) -> Optional[AdventurerGuildSubTask]:
        """解析单个子任务数据"""
        try:
            # 解析任务过程
            quest_steps = sub_task_data.get("任务过程", [])
            if not isinstance(quest_steps, list):
                quest_steps = []

            # 解析剧情对话
            dialogue_content = []
            dialogue_tree_data = sub_task_data.get("剧情对话", {}).get("对话树", [])

            # 扁平化对话树结构
            flattened_dialogues = self._flatten_dialogue_tree(dialogue_tree_data)

            for dialogue_item in flattened_dialogues:
                if isinstance(dialogue_item, dict):
                    # 创建对话条目，直接使用原始数据
                    dialogue_entry = DialogueEntry(**dialogue_item)
                    dialogue_content.append(dialogue_entry)

            # 创建子任务对象
            sub_task = AdventurerGuildSubTask(
                name=sub_task_data.get("名称", ""),
                trigger_condition=sub_task_data.get("触发条件"),
                quest_steps=quest_steps,
                dialogue_content=dialogue_content
            )

            return sub_task

        except Exception as e:
            self.logger.error(f"解析子任务数据时出错: {e}")
            return None

    def _merge_sub_tasks_to_guild(self, guild_title: str, sub_tasks: List[AdventurerGuildSubTask], file_path: str = "") -> AdventurerGuild:
        """将多个子任务整合成完整的冒险家协会对象"""
        try:
            # 创建完整冒险家协会对象
            guild = AdventurerGuild(
                name=guild_title,
                sub_tasks=sub_tasks
            )

            # 从文件路径设置ID
            if file_path:
                guild.set_id_from_filename(file_path)

            return guild

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
                # 直接添加，不修改原始数据
                flattened.append(item.copy())

            # 处理选择项
            elif item.get("type") == "options" and item.get("choices"):
                # 先添加选择项
                for choice in item["choices"]:
                    flattened.append({
                        "speaker": "选项",
                        "text": choice,
                        "dialogue_type": "choice"
                    })

                # 递归处理回复内容
                if item.get("reply"):
                    reply_dialogues = self._flatten_dialogue_tree(item["reply"])
                    flattened.extend(reply_dialogues)

        return flattened