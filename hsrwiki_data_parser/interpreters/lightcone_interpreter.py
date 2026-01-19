import logging
from typing import List
from pydantic import ValidationError

from hsrwiki_data_parser.models.lightcone import Lightcone
from hsrwiki_data_parser.services.dataloader import DataLoader
from hsrwiki_data_parser.models._core import GlobalTagManager

class LightconeInterpreter:
    def __init__(self, loader: DataLoader):
        self.loader = loader

    def interpret_all(self) -> List[Lightcone]:
        """Loads, validates, and interprets all lightcone data."""
        lightcones = []
        raw_data_iterator = self.loader.get_lightcones()

        for data in raw_data_iterator:
            try:
                # 不要移除source_url字段，因为它是模型的一部分
                lightcone = Lightcone(**data)
                # 手动加载标签
                if lightcone.id:
                    lightcone.tags = GlobalTagManager.get_tags(str(lightcone.id))
                lightcones.append(lightcone)
            except ValidationError as e:
                logging.error(f"Validation error for lightcone with id {data.get('id', 'N/A')}: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for lightcone id {data.get('id', 'N/A')}: {e}")

        logging.info(f"Successfully interpreted {len(lightcones)} lightcones.")
        return lightcones