import pickle
import gzip
import re
from typing import Any, Dict, List

class CacheService:
    """
    负责存储、索引和缓存所有解析后的崩坏：星铁数据。
    """
    def __init__(self):
        # 按类型存储所有数据对象
        self.books: List[Any] = []
        self.characters: List[Any] = []
        self.lightcones: List[Any] = []
        self.materials: List[Any] = []
        self.messages: List[Any] = []
        self.miracles: List[Any] = []
        self.missions: List[Any] = []
        self.relics: List[Any] = []
        self.rogue_events: List[Any] = []
        
        # 搜索索引
        self._search_index: Dict[str, List[Dict[str, Any]]] = {}

    def _clean_markdown_for_search(self, markdown_text: str) -> str:
        """移除Markdown格式，保留纯文本内容。"""
        if not markdown_text: return ""
        text = re.sub(r'#+\s?', '', markdown_text)
        text = re.sub(r'(\*\*|__)(.*?)(\*\*|__)', r'\2', text)
        text = re.sub(r'(\*|_)(.*?)(\*|_)', r'\2', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        text = re.sub(r'^\s*>\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'---', '', text)
        return text.strip()

    def index_item(self, item_id: Any, item_name: str, item_type: str, markdown_content: str):
        """
        为给定的项目创建索引。
        """
        if not item_name or not markdown_content:
            return
            
        full_text = f"{item_name}\n{self._clean_markdown_for_search(markdown_content)}"
        
        # 使用简单的分词（非中文优化）
        tokens = set(re.findall(r'\b\w+\b', full_text.lower()))
        
        context = {'id': item_id, 'name': item_name, 'type': item_type}

        for token in tokens:
            if token not in self._search_index:
                self._search_index[token] = []
            # 避免重复添加完全相同的上下文
            if context not in self._search_index[token]:
                self._search_index[token].append(context)

    def save(self, file_path: str):
        """
        使用 gzip 压缩将整个 CacheService 对象序列化到文件。
        """
        with gzip.open(file_path, 'wb') as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def load(file_path: str) -> 'CacheService':
        """
        从文件反序列化 CacheService 对象。
        """
        with gzip.open(file_path, 'rb') as f:
            return pickle.load(f)
