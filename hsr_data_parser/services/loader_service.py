import json
from typing import Any, Dict, List

class DataLoader:
    """Loads data from the ExcelOutput directory."""
    def __init__(self, data_path: str = "turnbasedgamedata/ExcelOutput"):
        self.data_path = data_path

    def get_json(self, filename: str, base_path_override: str = None) -> Any:
        """
        Reads a JSON file from the data path.
        An optional base_path_override can be provided to load from a different root.
        """
        base_path = base_path_override if base_path_override is not None else self.data_path
        full_path = f"{base_path}/{filename}"
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found at {full_path}")
            return None
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {full_path}")
            return None