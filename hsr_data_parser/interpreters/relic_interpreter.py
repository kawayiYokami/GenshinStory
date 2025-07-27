import json
from typing import Dict, List, Optional

from hsr_data_parser.models import Relic, RelicPartStory
from hsr_data_parser.services.loader_service import DataLoader
from hsr_data_parser.services.text_map_service import TextMapService

class RelicInterpreter:
    """
    一个解释器，用于融合游戏内数据和抓取的故事，创建最终的圣遗物数据模型。
    """

    def __init__(self, data_loader: DataLoader, text_map_service: TextMapService):
        self.data_loader = data_loader
        self.text_map_service = text_map_service
        
        # 加载所有需要的数据源
        self.item_config = data_loader.get_json("ItemConfig.json")
        self.scraped_relics = self._load_scraped_relics()

    def _load_scraped_relics(self) -> Dict[str, List[Dict]]:
        """加载爬取的故事数据，并按套装名称构建一个快速查找字典。"""
        try:
            # 使用新的路径和文件名，并提供正确的base_path
            scraped_data = self.data_loader.get_json(
                "relics.json",
                base_path_override="hsr_data_parser/data"
            )
            # a dictionary comprehension for quick lookups by set_name
            return {item['set_name']: item['parts'] for item in scraped_data}
        except FileNotFoundError:
            print("警告: 未找到 data/relics.json 文件，将无法加载圣遗物故事。")
            return {}

    def interpret_all(self) -> List[Relic]:
        """
        执行解释和数据融合过程。

        Returns:
            一个包含完整圣遗物信息的Relic对象列表。
        """
        all_relics = []
        
        for item_data in self.item_config:
            # 我们只关心代表整个套装的那个条目
            if item_data.get("ItemSubType") != "RelicSetShowOnly":
                continue

            item_name_hash = item_data.get("ItemName", {}).get("Hash")
            if not item_name_hash:
                continue

            set_name = self.text_map_service.get(item_name_hash)
            if not set_name:
                continue

            # 从爬取的数据中查找对应的故事
            scraped_parts_data = self.scraped_relics.get(set_name)
            if not scraped_parts_data:
                print(f"警告: 在 relics.json 中未找到套装 '{set_name}' 的故事。")
                continue

            # 构建 RelicPartStory 对象列表
            parts = [
                RelicPartStory(name=part['name'], story=part['story'])
                for part in scraped_parts_data
            ]

            # 创建最终的 Relic 对象
            relic = Relic(
                id=item_data["ID"],
                name=set_name,
                parts=parts
            )
            all_relics.append(relic)
            
        return all_relics
