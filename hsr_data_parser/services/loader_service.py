import json
from typing import Any, Dict, List

class DataLoader:
    """Loads data from the ExcelOutput directory."""
    def __init__(self, data_path: str = "turnbasedgamedata/ExcelOutput"):
        self.data_path = data_path

    def get_json(self, filename: str) -> List[Dict[str, Any]]:
        """Reads a JSON file from the data path."""
        try:
            with open(f"{self.data_path}/{filename}", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found at {self.data_path}/{filename}")
            return []
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {self.data_path}/{filename}")
            return []