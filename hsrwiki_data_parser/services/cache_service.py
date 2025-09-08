import pickle
import gzip
import re
from typing import Any, Dict, List
from collections import defaultdict

class CacheService:
    """
    负责存储、索引和缓存所有从 structured_data 解析后的数据。
    """
    def __init__(self):
        # 按类型存储所有数据对象
        self.books: List[Any] = []
        self.characters: List[Any] = []
        self.lightcones: List[Any] = [] # May not be used if not in structured_data
        self.materials: List[Any] = []
        self.missions: List[Any] = []
        self.relics: List[Any] = []
        # Add other lists as needed from structured_data
        self.outfits: List[Any] = []
        self.valuables: List[Any] = []
        self.rogue_events: List[Any] = []
        self.rogue_magic_scepters: List[Any] = []

        # 搜索索引
        self._search_index: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def _clean_text_for_search(self, text: str) -> str:
        """清洗文本，移除标点符号、特殊字符，并转换为小写。"""
        if not text: return ""
        # A more aggressive cleaning for user-generated content
        text = re.sub(r'<[^>]+>', '', text) # Remove HTML tags
        text = re.sub(r'#+\s?', '', text) # Remove markdown headers
        text = re.sub(r'(\*\*|__)(.*?)(\*\*|__)', r'\2', text) # Bold
        text = re.sub(r'(\*|_)(.*?)(\*|_)', r'\2', text) # Italic
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text) # Links
        text = re.sub(r'[^\u4e00-\u9fa5\u3040-\u30ff\uac00-\ud7a3a-zA-Z0-9\s]', '', text)
        text = re.sub(r'\s+', '', text)
        return text.lower()

    def _generate_ngrams(self, text: str, n: int = 2):
        """为给定的文本生成二元词条集合。"""
        if len(text) < n:
            return set()
        return {text[i:i+n] for i in range(len(text)-n+1)}

    def _add_to_index(self, token: str, item_id: Any, item_name: str, item_type: str):
        """向索引中添加一条记录，处理重复。"""
        context = {'id': item_id, 'name': item_name, 'type': item_type}
        if context not in self._search_index[token]:
            self._search_index[token].append(context)

    def index_item(self, item_id: Any, item_name: str, item_type: str, text_content: str):
        """
        为给定的项目创建索引 (使用二元组分词)。
        """
        if not item_name:
            return

        # 索引名称
        cleaned_name = self._clean_text_for_search(item_name)
        if cleaned_name:
            for token in self._generate_ngrams(cleaned_name):
                self._add_to_index(token, item_id, item_name, item_type)
            if len(cleaned_name) <= 5: # 短名称也作为整体索引
                 self._add_to_index(cleaned_name, item_id, item_name, item_type)

        # 索引内容
        if text_content:
            cleaned_content = self._clean_text_for_search(text_content)
            if cleaned_content:
                for token in self._generate_ngrams(cleaned_content):
                    self._add_to_index(token, item_id, item_name, item_type)

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
