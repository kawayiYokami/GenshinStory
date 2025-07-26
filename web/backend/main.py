import os
import sys

# This is the crucial part to make the backend find the 'game_data_parser' module
# Add the project root to the Python path. This file is at /web/backend/main.py
# The project root is 2 levels up.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

# Also, add the backend directory itself to the path for module resolution (e.g., 'app')
backend_root = os.path.dirname(os.path.abspath(__file__))
if backend_root not in sys.path:
    sys.path.append(backend_root)

import logging
from collections import defaultdict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from game_data_parser.api import GameDataAPI

# Configure logging
logging.basicConfig(level=logging.INFO)

# .env for environment variables
load_dotenv()

app = FastAPI(
    title="Game Data Parser API",
    description="API for accessing parsed game data.",
    version="0.1.0",
)

# Create a single, shared instance of the GameDataAPI
# This will load the data from the cache file upon startup.
# The project_root is calculated at the top of the file.
api = GameDataAPI(data_root_path=project_root)

# Diagnostic logging after initialization
logging.info("--- API Initialization Status ---")
logging.info(f"Search index size: {len(api.search_index)}")
if hasattr(api.loader, '_cache'):
    logging.info(f"File cache size: {len(api.loader._cache)}")
else:
    logging.info("File cache (_cache) not found in loader.")
logging.info("---------------------------------")


# CORS (Cross-Origin Resource Sharing)
# For debugging, allow all origins.
# In production, this should be a specific list of allowed domains.
origins = ["*"] # os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """A simple endpoint to test if the API is running."""
    return {"message": "Welcome to the Game Data Parser API!"}

@app.get("/api/search/list")
def get_search_list():
    """
    Returns an empty list, as the search results are populated dynamically
    based on user input, not on initial page load.
    """
    return []

@app.get("/api/search")
def search_all(keyword: str):
    """
    Performs a global search across all data types and returns the
    results grouped by category, matching the format expected by ListPane.
    """
    logging.info(f"Received search request with keyword: '{keyword}'")
    if not keyword:
        return []

    search_results = api.search(keyword)
    logging.info(f"Found {len(search_results)} results from api.search")
    
    # Group results by type
    grouped_results = defaultdict(list)
    for result in search_results:
        # The item for the list should contain all necessary info for a click
        item = {
            "id": str(result.id), # Ensure ID is a string for consistency
            "name": result.name,
            "type": result.type # This is crucial for the detail view request
        }
        grouped_results[result.type].append(item)

    # --- 汉化和格式化 ---
    CATEGORY_MAP = {
        "Readable": "世界文本",
        "Material": "材料",
        "Chapter": "章节",
        "RelicSet": "圣遗物",
        "Quest": "任务",
        "Weapon": "武器",
        "Book": "书籍",
        "Character": "角色",
    }

    formatted_list = []
    for category, items in grouped_results.items():
        formatted_list.append({
            "groupName": CATEGORY_MAP.get(category, category), # 使用映射，如果找不到则用回原名
            "children": items,
            "collapsed": True  # 默认折叠
        })
        
    return formatted_list

# Import and include the chapters router
from app.api import chapter as chapters_router

app.include_router(chapters_router.router, prefix="/api", tags=["Chapters"])

# Import and include the new quests router
from app.api import quest as quests_router

app.include_router(quests_router.router, prefix="/api", tags=["Quests"])

# Import and include the new weapons router
from app.api import weapon as weapons_router

app.include_router(weapons_router.router, prefix="/api", tags=["Weapons"])

# Import and include the new characters router
from app.api import character as characters_router

app.include_router(characters_router.router, prefix="/api", tags=["Characters"])

# Import and include the new books router
from app.api import book as books_router

app.include_router(books_router.router, prefix="/api", tags=["Books"])

# Import and include the new materials router
from app.api import material as materials_router
app.include_router(materials_router.router, prefix="/api", tags=["Materials"])

# Import and include the new relics router
from app.api import relic as relics_router
app.include_router(relics_router.router, prefix="/api", tags=["Relics"])

# Import and include the new readables router
from app.api import readable as readables_router
app.include_router(readables_router.router, prefix="/api", tags=["Readables"])
