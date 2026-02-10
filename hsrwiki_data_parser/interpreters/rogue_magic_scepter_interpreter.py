import logging
from typing import List
from hsrwiki_data_parser.models.rogue_magic_scepter import RogueMagicScepter
from hsrwiki_data_parser.services.game_data_loader import GameDataLoader
from hsrwiki_data_parser.services.text_map_service import TextMapService
from hsrwiki_data_parser.utils.text_transformer import TextTransformer


class RogueMagicScepterInterpreter:
    """
    Interprets raw Rogue Magic Scepter data from GameDataLoader into structured RogueMagicScepter objects.
    """

    def __init__(self, loader: GameDataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map = text_map_service
        self.text_transformer = TextTransformer()
        logging.info("Initializing RogueMagicScepterInterpreter...")

    def interpret_all(self) -> List[RogueMagicScepter]:
        """
        Parses all Rogue Magic Scepter data and returns a list of RogueMagicScepter objects.
        """
        raw_scepters_data = self.loader.get_rogue_magic_scepters()
        scepters: List[RogueMagicScepter] = []

        if not raw_scepters_data:
            logging.warning("No Rogue Magic Scepter data found.")
            return scepters

        logging.info(f"Processing {len(raw_scepters_data)} Rogue Magic Scepters...")

        for data in raw_scepters_data:
            try:
                scepter_id = data.get("ScepterID")
                if scepter_id is None:
                    logging.warning("Found Scepter entry without ID, skipping.")
                    continue

                name_hash = data.get("ScepterName", {}).get("Hash")
                desc_hash = data.get("ScepterBGDesc", {}).get("Hash")
                trigger_hash = data.get("ScepterTriggerDesc", {}).get("Hash")

                name = self.text_map.get_text(name_hash, f"未知奇物_{scepter_id}")
                raw_description = self.text_map.get_text(desc_hash, "无描述")
                raw_trigger_desc = self.text_map.get_text(trigger_hash, "无触发描述")

                # 使用 TextTransformer 清洗和转换文本
                description = self.text_transformer.transform(raw_description)
                trigger_desc = self.text_transformer.transform(raw_trigger_desc)

                scepter = RogueMagicScepter(
                    id=scepter_id,
                    name=name,
                    description=description,
                    trigger_desc=trigger_desc
                )
                scepters.append(scepter)

            except Exception as e:
                logging.error(f"Error processing Scepter ID {data.get('ScepterID', 'Unknown')}: {e}")

        logging.info(f"Successfully parsed {len(scepters)} Rogue Magic Scepters.")
        return scepters