from typing import Dict, Any, List, Optional

from ..models import Quest, QuestStep
from ..services import DataLoader, TextMapService


class QuestInterpreter:
    def __init__(self, loader: DataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map_service = text_map_service
        self._quests: Dict[int, Any] = {}
        self._finish_ways: Dict[int, Any] = {}
        self._sub_missions: Dict[int, Any] = {}

    def _prepare_data(self):
        """Pre-loads and caches all necessary data files."""
        # Load QuestData.json
        quest_data = self.loader.get_json("QuestData.json")
        self._quests = {item["QuestID"]: item for item in quest_data}

        # Load FinishWay.json
        finish_way_data = self.loader.get_json("FinishWay.json")
        self._finish_ways = {item["ID"]: item for item in finish_way_data}

        # Load SubMission.json
        sub_mission_data = self.loader.get_json("SubMission.json")
        self._sub_missions = {item["SubMissionID"]: item for item in sub_mission_data}

    def interpret(self, quest_id: int) -> Optional[Quest]:
        """Interprets a single quest by its ID."""
        # Ensure data is loaded
        if not self._quests:
            self._prepare_data()

        quest_info = self._quests.get(quest_id)
        if not quest_info:
            print(f"Quest with ID {quest_id} not found.")
            return None
        
        # Create the base quest object
        quest_title_hash = quest_info.get("QuestTitle", {}).get("Hash")
        quest = Quest(
            quest_id=quest_id,
            quest_title=self.text_map_service.get(quest_title_hash)
        )

        # Find the completion method (FinishWay)
        finish_way_id = quest_info.get("FinishWayID")
        finish_way_info = self._finish_ways.get(finish_way_id)

        if not finish_way_info or finish_way_info.get("FinishType") != "FinishMission":
            return quest # Return quest with no steps if no sub-missions are defined

        # Find and build the steps (SubMissions)
        sub_mission_ids = finish_way_info.get("ParamIntList", [])
        for sub_id in sub_mission_ids:
            sub_mission_info = self._sub_missions.get(sub_id)
            if sub_mission_info:
                title_hash = sub_mission_info.get("TargetText", {}).get("Hash")
                desc_hash = sub_mission_info.get("DescrptionText", {}).get("Hash")
                
                step = QuestStep(
                    step_id=sub_id,
                    title=self.text_map_service.get(title_hash),
                    description=self.text_map_service.get(desc_hash)
                )
                quest.steps.append(step)
        
        return quest