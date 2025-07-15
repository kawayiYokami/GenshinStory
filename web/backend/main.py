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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# .env for environment variables
load_dotenv()

app = FastAPI(
    title="Game Data Parser API",
    description="API for accessing parsed game data.",
    version="0.1.0",
)

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
