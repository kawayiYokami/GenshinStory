import os
import re
from typing import List, Optional

from typing import Any, Dict, List, Optional

from ..models import MainMission, SubMissionScript, QuestStep
from ..services import DataLoader, TextMapService
from .act_interpreter import ActInterpreter
from .story_interpreter import FlowchartInterpreter
from .talk_sentence_interpreter import TalkSentenceInterpreter


class MissionInterpreter:
    def __init__(self, loader: DataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map_service = text_map_service
        
        # 初始化所有专门的子解析器
        talk_sentence_interpreter = TalkSentenceInterpreter(loader, text_map_service)
        self.act_interpreter = ActInterpreter(loader, talk_sentence_interpreter)
        self.flowchart_interpreter = FlowchartInterpreter(loader, talk_sentence_interpreter)
        
        # 任务数据的内部缓存
        self._sub_missions: Dict[int, Any] = {}
        self._main_missions: Dict[int, MainMission] = {}
        self._mission_summaries: Dict[int, str] = {} # 来自 PerformanceSkipOverride 的任务摘要缓存

    def _scan_and_discover_sub_missions(self, mission_id: int) -> List[Dict[str, Any]]:
        """
        扫描三个指定目录以发现给定任务 ID 的所有子任务文件。
        返回一个包含 'id'、'type' 和 'path' 的字典列表。
        'path' 是相对于 'turnbasedgamedata' 目录的，以便与 DataLoader 兼容。
        """
        sub_mission_info_list = []
        discovered_ids = set() # 避免来自不同目录的重复项

        # 定义三个基础目录路径（相对于 turnbasedgamedata）及其对应的类型
        scan_paths = [
            (f"Story/Mission/{mission_id}", "Story"),
            (f"Story/Discussion/Mission/{mission_id}", "DS"),
            (f"Config/Level/Mission/{mission_id}/Act", "Act")
        ]

        for rel_base_path, file_type_prefix in scan_paths:
            # 构建用于扫描的完整绝对路径
            full_base_path = os.path.join("turnbasedgamedata", rel_base_path)
            if not os.path.exists(full_base_path):
                continue # 跳过不存在的目录

            try:
                for filename in os.listdir(full_base_path):
                    # 匹配类似 Story1234567.json, DS1234567.json, Act1234567.json 的文件
                    match = re.match(rf"^{file_type_prefix}(\d+)\.json$", filename)
                    if match:
                        sub_mission_id = int(match.group(1))
                        if sub_mission_id not in discovered_ids:
                            # 存储相对于 'turnbasedgamedata' 的路径
                            relative_file_path = os.path.join(rel_base_path, filename)
                            sub_mission_info_list.append({
                                'id': sub_mission_id,
                                'type': file_type_prefix,
                                'path': relative_file_path
                            })
                            discovered_ids.add(sub_mission_id)
            except OSError as e:
                print(f"Warning: Could not scan directory {full_base_path}. Error: {e}")

        return sub_mission_info_list

    def _prepare_data(self):
        """从 ExcelOutput 预加载并缓存所有必要的数据文件。"""
        if not self._sub_missions:
            sub_mission_data = self.loader.get_json("SubMission.json")
            if sub_mission_data:
                key_name = "SubMissionID" if "SubMissionID" in sub_mission_data[0] else "ID"
                self._sub_missions = {item[key_name]: item for item in sub_mission_data if key_name in item}
        
        if not self._main_missions:
            main_mission_data = self.loader.get_json("MainMission.json")
            if main_mission_data:
                for item in main_mission_data:
                    mission_id = item.get("MainMissionID")
                    if not mission_id:
                        continue
                    name_hash = item.get("Name", {}).get("Hash")
                    desc_hash = item.get("Desc", {}).get("Hash")
                    
                    mission_name = self.text_map_service.get(str(name_hash))
                    if not mission_name:
                        mission_name = "偶遇"

                    self._main_missions[mission_id] = MainMission(
                        id=mission_id,
                        name=mission_name,
                        description=self.text_map_service.get(str(desc_hash))
                    )

        if not self._mission_summaries:
            summary_data = self.loader.get_json("PerformanceSkipOverride.json")
            if summary_data:
                for item in summary_data:
                    if item.get("PerformanceType") == "C":
                        perf_id = item.get("PerformanceID")
                        desc_hash = item.get("Desc", {}).get("Hash")
                        if perf_id and desc_hash:
                            summary_text = self.text_map_service.get(str(desc_hash))
                            if summary_text:
                                self._mission_summaries[perf_id] = summary_text

    def interpret_all(self) -> List[MainMission]:
        """解析所有主线任务。"""
        self._prepare_data()
        all_missions = []
        
        for mission_id in self._main_missions.keys():
            mission_data = self.interpret_mission_script(mission_id)
            if mission_data:
                all_missions.append(mission_data)

        return all_missions

    def interpret_mission_script(self, mission_id: int) -> Optional[MainMission]:
        """通过扫描并解析其所有子任务文件来解析一个完整的任务。"""
        self._prepare_data()

        main_mission_info = self._main_missions.get(mission_id)
        if not main_mission_info:
            return None

        sub_mission_info_list = self._scan_and_discover_sub_missions(mission_id)
        sub_mission_scripts = []

        for sub_info in sub_mission_info_list:
            sub_mission_id = sub_info['id']
            sub_mission_type = sub_info['type']
            sub_mission_path = sub_info['path']

            script = None
            if sub_mission_type in ("DS", "Story"):
                script = self.flowchart_interpreter.interpret_file(sub_mission_path)
            elif sub_mission_type == "Act":
                script = self.act_interpreter.interpret_file(sub_mission_path)
            
            ui_data = self._sub_missions.get(sub_mission_id)
            quest_step = None
            if ui_data:
                target_hash = ui_data.get("TargetText", {}).get("Hash")
                desc_hash = ui_data.get("DescrptionText", {}).get("Hash")
                quest_step = QuestStep(
                    step_id=sub_mission_id,
                    target_text=self.text_map_service.get(str(target_hash)),
                    description_text=self.text_map_service.get(str(desc_hash))
                )
            
            mission_summary = self._mission_summaries.get(sub_mission_id)

            sub_mission_scripts.append(
                SubMissionScript(
                    id=sub_mission_id,
                    script=script,
                    ui_info=quest_step,
                    summary=mission_summary
                )
            )
        
        final_mission = MainMission(
            id=main_mission_info.id,
            name=main_mission_info.name,
            description=main_mission_info.description,
            scripts=sub_mission_scripts
        )
        
        has_dialogue = any(s.script and s.script.dialogue_blocks for s in final_mission.scripts)
        if not has_dialogue:
            return None

        return final_mission