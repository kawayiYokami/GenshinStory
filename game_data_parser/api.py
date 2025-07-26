from typing import Optional, List, Dict, Any, Counter
from collections import defaultdict
from .dataloader import DataLoader
from .models import SearchResult
from .services.character_service import CharacterService
from .services.book_service import BookService
from .services.material_service import MaterialService
from .services.quest_service import QuestService
from .services.relic_service import RelicService
from .services.weapon_service import WeaponService
from .services.text_map_service import TextMapService
from .services.readable_service import ReadableService


class GameDataAPI:
    """
    游戏数据解析器的统一对外接口 (API Facade)。
    这个类本身不实现具体业务逻辑，而是将请求委托给相应的领域服务。
    """
    def __init__(self, data_root_path: Optional[str] = None, cache_path: Optional[str] = "game_data.cache"):
        """
        初始化API，设置数据根目录并实例化所有领域服务。
        会优先尝试从缓存加载数据。
        """
        # --- Core Components ---
        self.loader = DataLoader(root_path=data_root_path, cache_path=cache_path)
        
        # --- Domain Services ---
        self.text = TextMapService(self.loader)
        self.character = CharacterService(self.loader)
        self.book = BookService(self.loader)
        self.material = MaterialService(self.loader)
        self.quest = QuestService(self.loader, self.text)
        self.relic = RelicService(self.loader)
        self.weapon = WeaponService(self.loader)
        self.readable = ReadableService(self.loader)

        self.search_index = self.loader._search_index

    def search(self, keyword: str, match_ratio_threshold: float = 0.75) -> List[SearchResult]:
        """
        在所有领域服务中快速搜索与关键字匹配的对象。
        采用N-gram和相关性计分算法。
        """
        if not keyword:
            return []
            
        keyword_lower = keyword.lower()
        
        query_tokens = self.loader._generate_ngrams(keyword_lower)
        if not query_tokens:
            query_tokens = {keyword_lower}

        results_scores: Dict[SearchResult, int] = defaultdict(int)
        for token in query_tokens:
            if token in self.search_index:
                for result_item in self.search_index[token]:
                    results_scores[result_item] += 1
        
        min_score = max(1, int(len(query_tokens) * match_ratio_threshold))
        
        filtered_results = [
            (result, score) for result, score in results_scores.items() if score >= min_score
        ]

        sorted_results = sorted(filtered_results, key=lambda item: (item[1], -item[0].id), reverse=True)

        return [result for result, score in sorted_results]
