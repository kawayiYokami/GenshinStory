import logging
from typing import List
from hsrwiki_data_parser.models.rogue_miracle import RogueMiracle
from hsrwiki_data_parser.services.game_data_loader import GameDataLoader
from hsrwiki_data_parser.services.text_map_service import TextMapService
from hsrwiki_data_parser.utils.text_transformer import TextTransformer


class RogueMiracleInterpreter:
    """
    Interprets raw Rogue Miracle data from GameDataLoader into structured RogueMiracle objects.
    """

    def __init__(self, loader: GameDataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map = text_map_service
        self.text_transformer = TextTransformer()
        logging.info("Initializing RogueMiracleInterpreter...")

    def interpret_all(self) -> List[RogueMiracle]:
        """
        Parses all Rogue Miracle data and returns a list of RogueMiracle objects.
        """
        raw_miracles = self.loader.get_rogue_miracles()
        raw_displays = self.loader.get_rogue_miracle_displays()
        displays_dict = {item['MiracleDisplayID']: item for item in raw_displays}
        miracles: List[RogueMiracle] = []

        if not raw_miracles:
            logging.warning("No Rogue Miracle data found.")
            return miracles

        logging.info(f"Processing {len(raw_miracles)} Rogue Miracles...")

        for data in raw_miracles:
            try:
                miracle_id = data.get("MiracleID")
                if miracle_id is None:
                    logging.warning("Found Miracle entry without ID, skipping.")
                    continue

                display_id = data.get("MiracleDisplayID")
                display = displays_dict.get(display_id)
                if not display:
                    logging.warning(f"No display data for MiracleDisplayID {display_id}, skipping.")
                    continue

                name_hash = display.get("MiracleName", {}).get("Hash")
                desc_hash = display.get("MiracleBGDesc", {}).get("Hash")

                name = self.text_map.get_text(name_hash, f"未知奇物_{miracle_id}")
                raw_description = self.text_map.get_text(desc_hash, "无描述")
                description = self.text_transformer.transform(raw_description)

                miracle = RogueMiracle(
                    id=miracle_id,
                    name=name,
                    description=description
                )
                miracles.append(miracle)

            except Exception as e:
                logging.error(f"Error processing Miracle ID {data.get('MiracleID', 'Unknown')}: {e}")

        logging.info(f"Successfully parsed {len(miracles)} Rogue Miracles.")
        return miracles