import logging
from typing import List
from pydantic import ValidationError

from hsrwiki_data_parser.models.rogue_event import RogueEvent
from hsrwiki_data_parser.services.dataloader import DataLoader

class RogueEventInterpreter:
    def __init__(self, loader: DataLoader):
        self.loader = loader

    def interpret_all(self) -> List[RogueEvent]:
        """Loads, validates, and interprets all rogue event data."""
        events = []
        raw_data_iterator = self.loader.get_rogue_events()

        for data in raw_data_iterator:
            try:
                # Remove fields that are not part of the model
                data.pop('source_url', None)
                # 'possible_outcomes' is now part of the model, so we don't remove it

                event = RogueEvent(**data)
                events.append(event)
            except ValidationError as e:
                logging.error(f"Validation error for rogue event with id {data.get('id', 'N/A')}: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for rogue event id {data.get('id', 'N/A')}: {e}")

        logging.info(f"Successfully interpreted {len(events)} rogue events.")
        return events
