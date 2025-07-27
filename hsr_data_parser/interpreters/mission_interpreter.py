from typing import List, Optional

from typing import Any, Dict, List, Optional

from ..models import MainMission, SubMissionScript, QuestStep
from ..services import DataLoader, TextMapService
from .act_interpreter import ActInterpreter
from .talk_sentence_interpreter import TalkSentenceInterpreter


class MissionInterpreter:
    def __init__(self, loader: DataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map_service = text_map_service
        self.talk_sentence_interpreter = TalkSentenceInterpreter(loader, text_map_service)
        self.act_interpreter = ActInterpreter(self.loader, self.talk_sentence_interpreter)
        
        # Internal caches for mission data, moved from QuestInterpreter
        self._sub_missions: Dict[int, Any] = {}
        self._main_missions: Dict[int, MainMission] = {}
    
    def _prepare_data(self):
        """Pre-loads and caches all necessary data files from ExcelOutput."""
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
                    
                    # Store the pre-parsed MainMission object
                    mission_name = self.text_map_service.get(str(name_hash))
                    if not mission_name:
                        # As per user feedback, missions without a name are "Encounter" missions
                        mission_name = "偶遇"

                    self._main_missions[mission_id] = MainMission(
                        id=mission_id,
                        name=mission_name,
                        description=self.text_map_service.get(str(desc_hash))
                    )

    def interpret_all(self) -> List[MainMission]:
        """Parses all main missions."""
        self._prepare_data()
        all_missions = []
        
        for mission_id in self._main_missions.keys():
            mission_data = self.interpret_mission_script(mission_id)
            if mission_data:
                all_missions.append(mission_data)

        return all_missions

    def interpret_mission_script(self, mission_id: int) -> Optional[MainMission]:
        """Interprets a full mission, extracting the dialogue script and associated UI text."""
        self._prepare_data() # Ensure data is loaded
        
        info_file_path = f"Config/Level/Mission/{mission_id}/MissionInfo_{mission_id}.json"

        main_mission_info = self._main_missions.get(mission_id)
        if not main_mission_info:
            return None # Should not happen if called from interpret_all

        mission_info_data = self.loader.get_json(info_file_path, base_path_override="turnbasedgamedata")
        if not mission_info_data:
            # If there's no MissionInfo file, we might still have a valid mission with no sub-steps.
            # Return the base info.
            return main_mission_info

        sub_mission_list = mission_info_data.get("SubMissionList", [])
        sub_mission_scripts = []

        for sub_mission_raw in sub_mission_list:
            sub_mission_id = sub_mission_raw.get("ID")
            if not sub_mission_id:
                continue

            # Get the UI text directly from the internal cache
            ui_data = self._sub_missions.get(sub_mission_id)
            quest_step = None
            if ui_data:
                target_hash = ui_data.get("TargetText", {}).get("Hash")
                desc_hash = ui_data.get("DescrptionText", {}).get("Hash") # Note: Typo is in the game data
                quest_step = QuestStep(
                    step_id=sub_mission_id,
                    target_text=self.text_map_service.get(str(target_hash)),
                    description_text=self.text_map_service.get(str(desc_hash))
                )

            # Get the dialogue script
            act_file_path = f"Config/Level/Mission/{mission_id}/Act/Act{sub_mission_id}.json"
            script = self.act_interpreter.interpret_file(act_file_path)

            sub_mission_scripts.append(
                SubMissionScript(
                    id=sub_mission_id,
                    script=script,
                    ui_info=quest_step
                )
            )
        
        # Create a final mission object with all collected data
        final_mission = MainMission(
            id=main_mission_info.id,
            name=main_mission_info.name,
            description=main_mission_info.description,
            scripts=sub_mission_scripts
        )
        
        # Filter out missions that have no dialogue content
        has_dialogue = any(s.script and s.script.dialogue_blocks for s in final_mission.scripts)
        if not has_dialogue:
            return None

        return final_mission