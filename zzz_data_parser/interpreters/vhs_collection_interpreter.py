from typing import Dict, List, Optional
from ..models.vhs_collection import VHSCollection
from ..dataloader import ZZZDataLoader


class VHSCollectionInterpreter:
    """
    Interpreter for parsing VHS Collection data from the game's configuration and text maps.
    """

    def __init__(self):
        """
        Initializes the interpreter by loading the text map and VHS collection config data.
        """
        self.data_loader = ZZZDataLoader()
        self.text_map = self.data_loader.get_text_map()

    def parse(self) -> List[VHSCollection]:
        """
        Parses all VHS Collection items from the configuration file.

        Returns:
            A list of VHSCollection objects.
        """
        vhs_config = self.data_loader.get_vhs_collection_config()
        if not vhs_config:
            return []

        vhs_collections = []
        for vhs_id, config in vhs_config.items():
            # Get name from text map using the name_key
            name = ""
            if config.get('name_key'):
                name = self.text_map.get(config['name_key'], '')

            # Get description from text map using the description_key
            description = ""
            if config.get('description_key'):
                description = self.text_map.get(config['description_key'], '')

            vhs_collection = VHSCollection(
                id=vhs_id,
                name=name,
                description=description
            )
            vhs_collections.append(vhs_collection)

        return vhs_collections