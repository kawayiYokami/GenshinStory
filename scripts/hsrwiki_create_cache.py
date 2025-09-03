import os
import logging
import time
import sys

# Setup project root path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Wiki Data Components
from hsrwiki_data_parser.services.dataloader import DataLoader as WikiDataLoader
from hsrwiki_data_parser.interpreters.character_interpreter import CharacterInterpreter
from hsrwiki_data_parser.interpreters.relic_interpreter import RelicInterpreter
from hsrwiki_data_parser.interpreters.book_interpreter import BookInterpreter
from hsrwiki_data_parser.interpreters.material_interpreter import MaterialInterpreter
from hsrwiki_data_parser.interpreters.quest_interpreter import QuestInterpreter
from hsrwiki_data_parser.interpreters.outfit_interpreter import OutfitInterpreter
from hsrwiki_data_parser.formatters.character_formatter import CharacterFormatter
from hsrwiki_data_parser.formatters.relic_formatter import RelicFormatter
from hsrwiki_data_parser.formatters.book_formatter import BookFormatter
from hsrwiki_data_parser.formatters.material_formatter import MaterialFormatter
from hsrwiki_data_parser.formatters.quest_formatter import QuestFormatter
from hsrwiki_data_parser.formatters.outfit_formatter import OutfitFormatter

# Game Data Components (for Messages)
from hsrwiki_data_parser.services.game_data_loader import GameDataLoader
from hsrwiki_data_parser.services.text_map_service import TextMapService
from hsrwiki_data_parser.interpreters.message_interpreter import MessageInterpreter
from hsrwiki_data_parser.formatters.message_formatter import MessageFormatter

# Common
from hsrwiki_data_parser.services.cache_service import CacheService

# --- Config ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
CACHE_DIR = "hsrwiki_data_parser/cache"
CACHE_FILE = os.path.join(CACHE_DIR, "hsrwiki_data.cache.gz")

def main():
    """Main function to create and save the cache from both wiki and game data."""
    start_time = time.time()
    logging.info("Starting to create cache from ALL data sources...")

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    # --- 1. Initialize Services ---
    logging.info("Initializing services...")
    wiki_loader = WikiDataLoader(base_path=os.path.join(project_root, 'structured_data'))
    game_loader = GameDataLoader(base_path=os.path.join(project_root, 'turnbasedgamedata'))
    text_map_service = TextMapService(game_loader)
    cache_service = CacheService()

    # --- 2. Process All Data Types ---
    # Note: Messages are processed first as they are from a different loader
    processing_map = {
        'messages': {'interpreter': MessageInterpreter(game_loader, text_map_service), 'formatter': MessageFormatter(), 'type_name': 'Message'},
        'characters': {'interpreter': CharacterInterpreter(wiki_loader), 'formatter': CharacterFormatter(), 'type_name': 'Character'},
        'relics': {'interpreter': RelicInterpreter(wiki_loader), 'formatter': RelicFormatter(), 'type_name': 'Relic'},
        'books': {'interpreter': BookInterpreter(wiki_loader), 'formatter': BookFormatter(), 'type_name': 'Book'},
        'materials': {'interpreter': MaterialInterpreter(wiki_loader), 'formatter': MaterialFormatter(), 'type_name': 'Material'},
        'quests': {'interpreter': QuestInterpreter(wiki_loader), 'formatter': QuestFormatter(), 'type_name': 'Quest'},
        'outfits': {'interpreter': OutfitInterpreter(wiki_loader), 'formatter': OutfitFormatter(), 'type_name': 'Outfit'},
    }

    for store_key, config in processing_map.items():
        interpreter = config['interpreter']
        formatter = config['formatter']
        type_name = config['type_name']
        
        logging.info(f"--- Processing: {type_name} ---")
        items = interpreter.interpret_all()
        setattr(cache_service, store_key, items)
        logging.info(f"  Interpreted {len(items)} {type_name} items.")

        # Format and Index
        for item in items:
            markdown_content = formatter.format(item)
            cache_service.index_item(item.id, item.name, type_name, text_content=markdown_content)
        logging.info(f"  Indexed {len(items)} {type_name} items.")

    # --- 3. Save Cache ---
    logging.info(f"Saving cache to '{CACHE_FILE}'...")
    cache_service.save(CACHE_FILE)

    end_time = time.time()
    logging.info(f"Cache creation process finished in {end_time - start_time:.2f} seconds.")
    logging.info(f"Cache file with search index saved at: {os.path.abspath(CACHE_FILE)}")

if __name__ == "__main__":
    main()
