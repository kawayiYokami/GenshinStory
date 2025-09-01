from typing import Dict, List, Optional
from ..models.weapon import Weapon
from ..dataloader import ZZZDataLoader


class WeaponInterpreter:
    """
    Interpreter for parsing weapon data from the game's configuration and text maps.
    """

    def __init__(self):
        """
        Initializes the interpreter by loading the text map and weapon config data.
        """
        self.data_loader = ZZZDataLoader(gender='M', player_name='哲')
        self.text_map = self.data_loader.get_text_map()

    def parse(self) -> List[Weapon]:
        """
        Parses all weapons from the weapon configuration file.

        Returns:
            A list of Weapon objects.
        """
        weapon_config = self.data_loader.get_weapon_config()
        if not weapon_config:
            return []

        weapons = []
        for weapon_id, config in weapon_config.items():
            # Get name from text map using the derived name_key
            name = self.text_map.get(config.get('name_key', ''), '')

            # Get description from text map if key exists and is not empty
            description = ""
            if config.get('description_key'):
                description = self.text_map.get(config['description_key'], '')

            # Get story from text map if key exists and is not empty
            story = ""
            if config.get('story_key'):
                story = self.text_map.get(config['story_key'], '')

            # Get model_id
            model_id = config.get('model_id', '')

            weapon = Weapon(
                id=weapon_id,
                name=name,
                description=description,
                story=story,
                model_id=model_id
            )
            weapons.append(weapon)

        return weapons