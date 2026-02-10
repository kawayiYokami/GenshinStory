import logging
from typing import List
from pydantic import ValidationError

from hsrwiki_data_parser.models.relic import Relic
from hsrwiki_data_parser.services.dataloader import DataLoader
from hsrwiki_data_parser.models._core import GlobalTagManager

class RelicInterpreter:
    def __init__(self, loader: DataLoader):
        self.loader = loader

    def interpret_all(self) -> List[Relic]:
        """Loads, validates, and interprets all relic data."""
        relics = []
        raw_data_iterator = self.loader.get_relics()

        for data in raw_data_iterator:
            try:
                # The 'set_effects' in some JSONs might be a dict instead of a list.
                # We need to handle this inconsistency.
                if isinstance(data.get('set_effects'), dict):
                    # Attempt to convert dict to list of SetEffect, or ignore if not possible
                    effects_dict = data['set_effects']
                    effects_list = []
                    for key, desc in effects_dict.items():
                        try:
                            # Assuming key is like '2' for 2-piece set
                            count = int(key)
                            effects_list.append({'count': count, 'description': desc})
                        except (ValueError, TypeError):
                            continue # Skip if key is not a valid integer
                    data['set_effects'] = effects_list

                relic = Relic(**data)
                # 手动加载标签
                if relic.id:
                    relic.tags = GlobalTagManager.get_tags(str(relic.id))
                relics.append(relic)
            except ValidationError as e:
                logging.error(f"Validation error for relic with id {data.get('id', 'N/A')}: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for relic id {data.get('id', 'N/A')}: {e}")

        logging.info(f"Successfully interpreted {len(relics)} relics.")
        return relics
