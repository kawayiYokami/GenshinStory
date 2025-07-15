import os
import threading
from game_data_parser.api import GameDataAPI

# Determine the root path of the project to find the data directory
# This file is at /web/backend/app/services/game_data.py
# The project root is 4 levels up.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
data_path = os.path.join(project_root, "AnimeGameData")
cache_file_path = os.path.join(project_root, "game_data.cache")

# Use thread-local storage to create separate GameDataAPI instances for each thread
# This solves the SQLite thread safety issue where SQLite objects created in one thread
# cannot be used in another thread.
_thread_local = threading.local()

def get_game_data_service() -> GameDataAPI:
    """
    Dependency injection provider for the GameDataAPI service.
    Creates a separate GameDataAPI instance for each thread to avoid SQLite thread safety issues.
    """
    if not hasattr(_thread_local, 'game_data_service'):
        thread_id = threading.current_thread().ident
        print(f"Creating new GameDataAPI instance for thread {thread_id}")
        print(f"Using data root path: {data_path}")
        print(f"Using cache file: {cache_file_path}")
        _thread_local.game_data_service = GameDataAPI(data_root_path=data_path, cache_path=cache_file_path)
        print(f"GameDataAPI instance created for thread {thread_id}")
    
    return _thread_local.game_data_service
