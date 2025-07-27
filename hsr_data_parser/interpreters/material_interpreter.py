from typing import List

from ..models.material import Material
from ..services import DataLoader, TextMapService

class MaterialInterpreter:
    """
    Interprets material/item data from ItemConfig.json.
    """
    def __init__(self, loader: DataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map_service = text_map_service

    def interpret_all(self) -> List[Material]:
        """
        Parses the item config file and returns a list of Material objects.
        """
        materials = []
        item_config_data = self.loader.get_json("ItemConfig.json")
        if not item_config_data:
            return materials

        for item_info in item_config_data:
            item_id = item_info.get("ID")
            name_hash = item_info.get("ItemName", {}).get("Hash")
            desc_hash = item_info.get("ItemDesc", {}).get("Hash")
            bg_desc_hash = item_info.get("ItemBGDesc", {}).get("Hash")
            
            main_type = item_info.get("ItemMainType")
            sub_type = item_info.get("ItemSubType")
            rarity = item_info.get("Rarity")

            # We only care about items that have a name and some form of description.
            if not all([item_id, name_hash, main_type, sub_type, rarity]):
                continue

            name = self.text_map_service.get(str(name_hash))
            # Descriptions can be optional, so we get them safely.
            description = self.text_map_service.get(str(desc_hash)) or ""
            bg_description = self.text_map_service.get(str(bg_desc_hash)) or ""

            if name:
                materials.append(Material(
                    id=item_id,
                    name=name,
                    description=description,
                    background_description=bg_description,
                    main_type=main_type,
                    sub_type=sub_type,
                    rarity=rarity
                ))
        
        return materials