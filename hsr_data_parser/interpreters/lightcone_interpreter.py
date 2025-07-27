from typing import List

from ..models.lightcone import LightCone
from ..services import DataLoader, TextMapService

class LightConeInterpreter:
    """
    Interprets Light Cone data from ItemConfigEquipment.json.
    """
    def __init__(self, loader: DataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map_service = text_map_service

    def interpret_all(self) -> List[LightCone]:
        """
        Parses the equipment config file and returns a list of LightCone objects.
        """
        light_cones = []
        equipment_data = self.loader.get_json("ItemConfigEquipment.json")
        if not equipment_data:
            return light_cones

        for item_info in equipment_data:
            # We are only interested in Light Cones, which seem to be the main content of this file.
            if item_info.get("ItemSubType") != "Equipment":
                 continue

            item_id = item_info.get("ID")
            name_hash = item_info.get("ItemName", {}).get("Hash")
            desc_hash = item_info.get("ItemDesc", {}).get("Hash")
            bg_desc_hash = item_info.get("ItemBGDesc", {}).get("Hash")
            rarity = item_info.get("Rarity")

            if not all([item_id, name_hash, rarity]):
                continue

            name = self.text_map_service.get(str(name_hash))
            description = self.text_map_service.get(str(desc_hash)) or ""
            bg_description = self.text_map_service.get(str(bg_desc_hash)) or ""

            if name:
                light_cones.append(LightCone(
                    id=item_id,
                    name=name,
                    description=description,
                    background_description=bg_description,
                    rarity=rarity
                ))
        
        return light_cones