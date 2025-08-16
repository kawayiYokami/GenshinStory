import json
import os
import re
from typing import Any, Dict, List

class DataLoader:
    """从 ExcelOutput 目录加载数据。"""
    def __init__(self, data_path: str = "turnbasedgamedata/ExcelOutput"):
        self.data_path = data_path

    def get_json(self, filename: str, base_path_override: str = None) -> Any:
        """
        从数据路径读取一个JSON文件。
        可以提供一个可选的 base_path_override 从不同的根目录加载。
        """
        base_path = base_path_override if base_path_override is not None else self.data_path
        full_path = f"{base_path}/{filename}"
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误: 文件未找到于 {full_path}")
            return None
        except json.JSONDecodeError:
            print(f"错误: 无法从 {full_path} 解码 JSON")
            return None

    def discover_rogue_event_ids(self) -> List[int]:
        """
        通过扫描目录发现所有模拟宇宙事件的ID。
        """
        event_ids = []
        base_path = "turnbasedgamedata/Config/Level/Rogue/RogueDialogue"
        
        if not os.path.exists(base_path):
            print(f"警告: 目录不存在: {base_path}")
            return event_ids

        for entry in os.listdir(base_path):
            match = re.match(r'^Event(\d{7})$', entry)
            if match:
                full_path = os.path.join(base_path, entry)
                if os.path.isdir(full_path):
                    event_ids.append(int(match.group(1)))
        
        return event_ids