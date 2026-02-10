import logging
from typing import List
from pydantic import ValidationError

from hsrwiki_data_parser.models.outfit import Outfit
from hsrwiki_data_parser.services.dataloader import DataLoader
from hsrwiki_data_parser.models._core import GlobalTagManager

class OutfitInterpreter:
    def __init__(self, loader: DataLoader):
        self.loader = loader

    def interpret_all(self) -> List[Outfit]:
        """Loads, validates, and interprets all outfit data."""
        outfits = []
        try:
            raw_data_iterator = self.loader.get_outfits()
        except AttributeError:
            logging.error("DataLoader does not have a 'get_outfits' method. Please add it.")
            return []

        for data in raw_data_iterator:
            try:
                data.pop('source_url', None)
                outfit = Outfit(**data)
                # 手动加载标签
                if outfit.id:
                    outfit.tags = GlobalTagManager.get_tags(str(outfit.id))
                outfits.append(outfit)
            except ValidationError as e:
                logging.error(f"Validation error for outfit with id {data.get('id', 'N/A')}: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for outfit id {data.get('id', 'N/A')}: {e}")

        logging.info(f"Successfully interpreted {len(outfits)} outfits.")
        return outfits
