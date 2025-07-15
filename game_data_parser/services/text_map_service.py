from functools import lru_cache
from typing import Dict

from ..dataloader import DataLoader


class TextMapService:
    """
    提供文本哈希到具体文本的查询服务。
    数据源现在是 DataLoader，它在内存中缓存了 TextMap 文件。
    通过LRU缓存来优化高频访问的性能。
    """
    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
        # Pre-load the entire text map into memory.
        # The keys in the JSON are strings, so we need to handle that.
        self._text_map: Dict[str, str] = self.loader.get_text_map()

    @lru_cache(maxsize=4096)
    def get(self, text_hash: int, default: str = "") -> str:
        """
        根据文本哈希查找对应的文本。
        如果找不到，返回一个默认值。
        此方法被LRU缓存以提高性能。
        """
        if not text_hash:
            return default

        # JSON keys must be strings, so we must convert the hash for lookup.
        key = str(text_hash)
        return self._text_map.get(key, default)