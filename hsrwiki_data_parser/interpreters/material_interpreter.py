import logging
from typing import List
from pydantic import ValidationError

from hsrwiki_data_parser.models.material import Material
from hsrwiki_data_parser.services.dataloader import DataLoader
from hsrwiki_data_parser.models._core import GlobalTagManager

class MaterialInterpreter:
    def __init__(self, loader: DataLoader):
        self.loader = loader

    def interpret_all(self) -> List[Material]:
        """Loads, validates, and interprets all material data from multiple sources."""
        materials = []
        # The get_materials method in DataLoader already iterates through all material dirs
        raw_data_iterator = self.loader.get_materials()

        for data in raw_data_iterator:
            try:
                # Pop fields that are not in the model to avoid errors
                data.pop('source_url', None)

                material = Material(**data)
                # 手动加载标签
                if material.id:
                    material.tags = GlobalTagManager.get_tags(str(material.id))
                materials.append(material)
            except ValidationError as e:
                logging.error(f"Validation error for material with id {data.get('id', 'N/A')}: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for material id {data.get('id', 'N/A')}: {e}")

        logging.info(f"Successfully interpreted {len(materials)} materials.")
        return materials
