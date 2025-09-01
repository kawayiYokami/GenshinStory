from typing import Dict, List, Optional
from ..models.item import Item
from ..dataloader import ZZZDataLoader


class ItemInterpreter:
    """
    Interpreter for parsing item data from the game's configuration and text maps.
    """

    def __init__(self):
        """
        Initializes the interpreter by loading the text map and item config data.
        """
        self.data_loader = ZZZDataLoader(gender='M', player_name='哲')
        self.text_map = self.data_loader.get_text_map()

    def parse(self) -> List[Item]:
        """
        Parses all items from the item configuration file.

        Returns:
            A list of Item objects.
        """
        item_config = self.data_loader.get_item_config()
        if not item_config:
            return []

        items = []
        for item_id, config in item_config.items():
            # Get name from text map
            name = self.text_map.get(config['name_key'], '')

            # Get description from text map if key exists and is not empty
            description = ""
            if config.get('description_key'):
                description = self.text_map.get(config['description_key'], '')

            # Get story from text map if key exists and is not empty
            story = ""
            if config.get('story_key'):
                story = self.text_map.get(config['story_key'], '')

            item = Item(
                id=item_id,
                name=name,
                description=description,
                story=story
            )
            items.append(item)

        return items