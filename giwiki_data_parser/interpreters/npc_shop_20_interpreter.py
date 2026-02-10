"""
原神Wiki NPC数据解释器

负责将JSON数据转换为NPC数据模型，专注于提取对话和故事内容。
"""

import logging
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.npc_shop_20 import NPCModel, DialogueGroup, DialogueOption
from giwiki_data_parser.services.dataloader import DataLoader


class NPCInterpreter:
    """NPC数据解释器"""

    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)

    def interpret(self, data: Dict[str, Any]) -> Optional[NPCModel]:
        """解析单个NPC数据 - 公共接口"""
        return self._interpret_single(data)

    def interpret_all(self) -> List[NPCModel]:
        """解析所有NPC数据"""
        npcs = []
        raw_data_iterator = self.loader.get_npcs()

        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                npc = self._interpret_single(data, file_path)
                if npc:
                    npcs.append(npc)
            except Exception as e:
                self.logger.error(f"解析NPC数据时出错: {e}")

        self.logger.info(f"成功解析 {len(npcs)} 个NPC")
        return npcs

    def _interpret_single(self, data: Dict[str, Any], file_path: str = "") -> Optional[NPCModel]:
        """解析单个NPC数据"""
        try:
            # 基础信息提取
            name = data.get("名称", "").strip()
            gender = data.get("性别", "").strip()
            location = data.get("位置", "").strip()

            # 解析对话组
            dialogue_groups = []
            dialogue_groups_data = data.get("对话组", [])

            if isinstance(dialogue_groups_data, list):
                for group_data in dialogue_groups_data:
                    if isinstance(group_data, dict):
                        group_title = group_data.get("标题", "")
                        group_dialogues = []

                        dialogues_data = group_data.get("对话", [])
                        if isinstance(dialogues_data, list):
                            for dialogue_data in dialogues_data:
                                if isinstance(dialogue_data, dict):
                                    option = dialogue_data.get("选项", "")
                                    content = dialogue_data.get("内容", [])

                                    if isinstance(content, list):
                                        dialogue_option = DialogueOption(
                                            option=option,
                                            content=content
                                        )
                                        group_dialogues.append(dialogue_option)

                        dialogue_group = DialogueGroup(
                            title=group_title,
                            dialogues=group_dialogues
                        )
                        dialogue_groups.append(dialogue_group)

            # 创建NPC对象
            npc = NPCModel(
                name=name,
                gender=gender,
                location=location,
                dialogue_groups=dialogue_groups
            )

            # 从文件路径设置ID
            if file_path:
                npc.set_id_from_filename(file_path)
            elif "_file_path" in data:
                npc.set_id_from_filename(data["_file_path"])
            elif "_file_id" in data:
                file_id = str(data["_file_id"])
                if file_id.isdigit():
                    npc.id = file_id
                else:
                    self.logger.warning(f"非数字文件ID，跳过: {file_id}")
                    return None

            return npc

        except Exception as e:
            self.logger.error(f"解析NPC数据时出错: {e}")
            return None