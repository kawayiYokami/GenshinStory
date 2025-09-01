from typing import Dict, List, Optional
from ..models.hollow_item import HollowItem
from ..dataloader import ZZZDataLoader


class HollowItemInterpreter:
    """
    Interpreter for parsing hollow item data from the game's configuration and text maps.
    """

    def __init__(self):
        """
        Initializes the interpreter by loading the text map and hollow item config data.
        """
        self.data_loader = ZZZDataLoader(gender='M', player_name='哲')
        self.text_map = self.data_loader.get_text_map()

    def parse(self) -> List[HollowItem]:
        """
        Parses all hollow items from the hollow item configuration file.

        Returns:
            A list of HollowItem objects.
        """
        hollow_item_config = self.data_loader.get_hollow_item_config()
        if not hollow_item_config:
            return []

        items = []
        for item_id, config in hollow_item_config.items():
            # Get name from text map
            name = self.text_map.get(config['name_key'], '')

            # Get description from text map
            description = self.text_map.get(config['description_key'], '')

            item = HollowItem(
                id=item_id,
                name=name,
                description=description
            )
            items.append(item)

        return items