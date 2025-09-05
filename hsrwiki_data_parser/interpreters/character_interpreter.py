import logging
from typing import List
from pydantic import ValidationError

from hsrwiki_data_parser.models.character import Character
from hsrwiki_data_parser.services.dataloader import DataLoader

class CharacterInterpreter:
    def __init__(self, loader: DataLoader):
        self.loader = loader

    def interpret_all(self) -> List[Character]:
        """Loads, validates, and interprets all character data."""
        characters = []
        raw_data_iterator = self.loader.get_characters()

        for data in raw_data_iterator:
            try:
                character = Character(**data)
                characters.append(character)
            except ValidationError as e:
                logging.error(f"Validation error for character with id {data.get('id', 'N/A')}: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for character id {data.get('id', 'N/A')}: {e}")
        
        logging.info(f"Successfully interpreted {len(characters)} characters.")
        return characters
