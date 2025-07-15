import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..dataloader import DataLoader
from ..models import BookSuit, BookVolume
from ..utils.text_transformer import transform_text

class BookSuitInterpreter:
    """
    负责将原始的书籍系列数据解析成结构化的 BookSuit 对象。
    """
    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
        self._text_map: Dict[str, str] = {}
        
        # Pre-processed data caches
        self._book_suit_configs: Dict[int, Dict[str, Any]] = {}
        self._volumes_by_series_id: Dict[int, List[Dict[str, Any]]] = {}
        
        self._is_prepared = False

    def _get_text(self, text_map_hash: Any, default: str = "") -> str:
        """根据哈希值安全地获取原始文本。"""
        text, _ = transform_text(self._text_map.get(str(text_map_hash), default))
        return text

    def _prepare_data(self):
        """一次性加载所有需要的数据并进行预处理。"""
        if self._is_prepared:
            return
        
        logging.info("加载书籍系列相关数据 (BookSuit)...")
        # Load original game data
        self._text_map = self.loader.get_json("TextMap/TextMapCHS.json")
        self._book_suit_configs = {item['id']: item for item in self.loader.get_json("ExcelBinOutput/BookSuitExcelConfigData.json")}
        
        # Load our enhanced volume data using the DataLoader
        try:
            # The data root is '.../AnimeGameData', so we go up one level to the project root
            # and then down to the database file.
            relative_path = "../game_data_parser/database/books_with_content_id.json"
            enriched_data = self.loader.get_json(relative_path)
            
            if enriched_data:
                for series_data in enriched_data:
                    series_id = series_data.get('series_id')
                    if series_id:
                        self._volumes_by_series_id[series_id] = series_data.get('volumes', [])
            else:
                logging.error(f"无法加载私有的书籍分卷数据: 文件 {relative_path} 未找到或内容为空。")

        except Exception as e:
            logging.error(f"处理私有的书籍分卷数据时发生错误: {e}")


        self._is_prepared = True
        logging.info("书籍系列相关数据加载完成。")

    def get_all_suit_ids(self) -> List[int]:
        """获取所有书籍系列ID列表。"""
        self._prepare_data()
        return list(self._book_suit_configs.keys())

    def interpret(self, suit_id: int) -> Optional[BookSuit]:
        """解析单个书籍系列的完整信息。"""
        self._prepare_data()

        suit_config = self._book_suit_configs.get(suit_id)
        if not suit_config:
            return None

        name = self._get_text(suit_config.get("suitNameTextMapHash"))
        if not name:
            return None

        volumes_data = self._volumes_by_series_id.get(suit_id, [])
        volumes = []
        for vol_data in volumes_data:
            # We must have book_txt_id to create a valid volume
            if 'book_txt_id' in vol_data:
                volume = BookVolume(
                    volume_title=vol_data.get('volume_title', ''),
                    introduction=vol_data.get('introduction', ''),
                    book_txt_id=vol_data['book_txt_id'],
                    _loader=self.loader  # Pass the loader for lazy loading
                )
                volumes.append(volume)

        book_suit = BookSuit(
            id=suit_id,
            name=name,
            volumes=volumes
        )

        return book_suit