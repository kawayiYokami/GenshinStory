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
        self.quests: List[Any] = []
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

    def index_item(self, item_id: Any, item_name: str, item_type: str, text_content: str, tags: Dict[str, str] = None):
        """
        为给定的项目创建索引 (使用二元组分词)。

        Args:
            item_id: 项目ID
            item_name: 项目名称
            item_type: 项目类型
            text_content: 文本内容
            tags: 标签字典，键为标签名，值为标签内容
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

        # 索引标签内容（只索引标签值，不索引标签键）
        if tags:
            for tag_key, tag_value in tags.items():
                if tag_value:
                    cleaned_tag_value = self._clean_text_for_search(tag_value)
                    if cleaned_tag_value:
                        # 为标签值生成n-gram索引
                        for token in self._generate_ngrams(cleaned_tag_value):
                            self._add_to_index(token, item_id, item_name, item_type)
                        # 短标签值也作为整体索引
                        if len(cleaned_tag_value) <= 5:
                            self._add_to_index(cleaned_tag_value, item_id, item_name, item_type)

    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """搜索功能"""
        if not query:
            return []

        cleaned_query = self._clean_text_for_search(query)
        if not cleaned_query:
            return []

        # 收集所有匹配的结果
        results = set()

        # 直接匹配
        if cleaned_query in self._search_index:
            for item in self._search_index[cleaned_query]:
                results.add((item['id'], item['name'], item['type']))

        # N-gram匹配
        query_ngrams = self._generate_ngrams(cleaned_query)
        for ngram in query_ngrams:
            if ngram in self._search_index:
                for item in self._search_index[ngram]:
                    results.add((item['id'], item['name'], item['type']))

        # 转换为列表并限制数量
        result_list = []
        for item_id, item_name, item_type in list(results)[:limit]:
            result_list.append({
                'id': item_id,
                'name': item_name,
                'type': item_type
            })

        return result_list

    def add_item(self, item: Any, item_type: str):
        """添加数据项到对应的存储列表中"""
        # 标准化类型名称，将中文类型名转换为英文属性名
        type_mapping = {
            '18_角色': 'characters',
            '19_光锥': 'lightcones',
            '25_任务': 'quests',
            '30_遗器': 'relics',
            '31_阅读物': 'books',
            '20_养成材料': 'materials',
            '53_任务道具': 'materials',
            '54_贵重物': 'valuables',
            '55_其他材料': 'materials',
            '157_装扮': 'outfits',
            '103_模拟宇宙·事件图鉴': 'rogue_events',
        }

        # 获取标准化的属性名
        attr_name = type_mapping.get(item_type, item_type.lower().replace('_', '_').replace('&', '_'))

        # 确保属性存在
        if not hasattr(self, attr_name):
            setattr(self, attr_name, [])

        # 添加项目到对应列表
        getattr(self, attr_name).append(item)

    def get_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {}

        # 统计各类型数据数量
        for attr_name in dir(self):
            if not attr_name.startswith('_') and isinstance(getattr(self, attr_name), list):
                attr_value = getattr(self, attr_name)
                if attr_value:  # 只统计非空列表
                    stats[attr_name] = len(attr_value)

        # 索引统计
        stats['search_index_tokens'] = len(self._search_index)
        stats['search_index_entries'] = sum(len(entries) for entries in self._search_index.values())

        return stats

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
