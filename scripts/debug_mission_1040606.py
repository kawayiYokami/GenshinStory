import sys
import os
import json

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from hsr_data_parser.services.loader_service import DataLoader
from hsr_data_parser.services.text_map_service import TextMapService
from hsr_data_parser.interpreters.mission_interpreter import MissionInterpreter
from hsr_data_parser.formatters.mission_formatter import MissionFormatter

def main():
    """
    Initializes services, runs the interpreter for a specific mission,
    and then uses the formatter to print the final Markdown output.
    """
    print("--- Initializing Services for Mission 1040606 Debug ---")
    
    loader = DataLoader(data_path="turnbasedgamedata/ExcelOutput")
    text_map_service = TextMapService(loader)
    mission_interpreter = MissionInterpreter(loader, text_map_service)
    mission_formatter = MissionFormatter()

    target_mission_id = 1040606
    print(f"\n--- Interpreting and Formatting Mission ID: {target_mission_id} ---")

    mission_data = mission_interpreter.interpret_mission_script(target_mission_id)

    if not mission_data:
        print("\n--- RESULT: Mission data could not be interpreted. ---")
        return

    # Format the mission data into a Markdown string
    markdown_output = mission_formatter.format(mission_data)

    print("\n\n--- FINAL MARKDOWN OUTPUT ---")
    print(markdown_output)
    print("\n--- Debug script finished. ---")

if __name__ == "__main__":
    main()