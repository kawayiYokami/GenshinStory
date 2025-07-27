from typing import List

from ..models.miracle import Miracle
from ..services import DataLoader, TextMapService

class MiracleInterpreter:
    """
    Interprets miracle (Curio) data from RogueMiracleDisplay.json.
    """
    def __init__(self, loader: DataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map_service = text_map_service

    def interpret_all(self) -> List[Miracle]:
        """
        Parses the miracle display file and returns a list of Miracle objects.
        """
        miracles = []
        miracle_data = self.loader.get_json("RogueMiracleDisplay.json")
        if not miracle_data:
            return miracles

        for miracle_info in miracle_data:
            miracle_id = miracle_info.get("MiracleDisplayID")
            name_hash = miracle_info.get("MiracleName", {}).get("Hash")
            bg_desc_hash = miracle_info.get("MiracleBGDesc", {}).get("Hash")

            if not all([miracle_id, name_hash, bg_desc_hash]):
                continue

            name = self.text_map_service.get(str(name_hash))
            background_description = self.text_map_service.get(str(bg_desc_hash))

            if name and background_description:
                miracles.append(Miracle(
                    id=miracle_id,
                    name=name,
                    background_description=background_description
                ))
        
        return miracles