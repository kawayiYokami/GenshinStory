"""
Game Data Parser
================

A library to parse and interpret game data into structured objects and formatted text.

Provides a main entry point `GameDataAPI` to access various functionalities.
"""
from .api import GameDataAPI

# Define what gets imported with a 'from game_data_parser import *'
__all__ = ["GameDataAPI"]