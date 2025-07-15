from typing import Optional
from .dataloader import DataLoader
from .services.character_service import CharacterService
from .services.book_service import BookService
from .services.material_service import MaterialService
from .services.quest_service import QuestService
from .services.relic_service import RelicService
from .services.weapon_service import WeaponService
from .services.text_map_service import TextMapService


class GameDataAPI:
    """
    游戏数据解析器的统一对外接口 (API Facade)。
    这个类本身不实现具体业务逻辑，而是将请求委托给相应的领域服务。
    """
    def __init__(self, data_root_path: str, cache_path: Optional[str] = "game_data.cache"):
        """
        初始化API，设置数据根目录并实例化所有领域服务。
        会优先尝试从缓存加载数据。
        """
        # --- Core Components ---
        self.loader = DataLoader(root_path=data_root_path, cache_path=cache_path)
        
        # --- Domain Services ---
        # Centralized services first
        self.text = TextMapService(self.loader)

        # Each service is responsible for its own interpreters and formatters.
        self.character = CharacterService(self.loader)
        self.book = BookService(self.loader)
        self.material = MaterialService(self.loader)
        self.quest = QuestService(self.loader, self.text)
        self.relic = RelicService(self.loader)
        self.weapon = WeaponService(self.loader)