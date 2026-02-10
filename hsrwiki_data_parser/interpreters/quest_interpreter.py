import logging
from typing import List
from pydantic import ValidationError

from hsrwiki_data_parser.models.quest import Quest
from hsrwiki_data_parser.services.dataloader import DataLoader
from hsrwiki_data_parser.models._core import GlobalTagManager

class QuestInterpreter:
    def __init__(self, loader: DataLoader):
        self.loader = loader

    def interpret_all(self) -> List[Quest]:
        """Loads, validates, and interprets all quest data."""
        quests = []
        # First, we need to add a get_quests method to the DataLoader
        # For now, let's assume it exists and is named get_quests
        try:
            raw_data_iterator = self.loader.get_quests()
        except AttributeError:
            logging.error("DataLoader does not have a 'get_quests' method. Please add it.")
            return []

        for data in raw_data_iterator:
            try:
                data.pop('source_url', None)
                quest = Quest(**data)
                # 手动加载标签
                if quest.id:
                    quest.tags = GlobalTagManager.get_tags(str(quest.id))
                quests.append(quest)
            except ValidationError as e:
                logging.error(f"Validation error for quest with id {data.get('id', 'N/A')}: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for quest id {data.get('id', 'N/A')}: {e}")

        logging.info(f"Successfully interpreted {len(quests)} quests.")
        return quests
