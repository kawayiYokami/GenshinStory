from typing import Any, Dict, List, Optional
from dataclasses import asdict

from ..dataloader import DataLoader
from ..interpreters.reliquary_interpreter import ReliquaryInterpreter
from ..formatters.relic_formatter import RelicFormatter
from ..models import Reliquary, ReliquarySet


class RelicService:
    """
    提供所有与“圣遗物(Reliquary)”领域相关的查询和操作, 包括单个圣遗物和套装。
    """
    def __init__(self, loader: DataLoader):
        self.interpreter = ReliquaryInterpreter(loader)
        self.formatter = RelicFormatter()

    def list_relics(self) -> List[Dict[str, Any]]:
        """获取所有圣遗物部件的简明列表。"""
        return self.search_relics()

    def search_relics(self, part: Optional[str] = None, rarity: Optional[int] = None) -> List[Dict[str, Any]]:
        """根据部件和稀有度筛选圣遗物部件。"""
        all_relics = []
        all_relic_ids = self.interpreter.get_all_relic_ids()
        for relic_id in all_relic_ids:
            relic = self.interpreter.interpret_single(relic_id)
            if not relic:
                continue

            # Placeholder for future rarity filtering improvement
            if rarity is not None:
                pass

            if part is not None and relic.pos_name != part:
                continue
            
            all_relics.append({
                "id": relic.id,
                "name": relic.name
            })
        return all_relics

    def get_relic_by_id(self, item_id: int, index_context: Optional[Any] = None) -> Optional[Reliquary]:
        """获取单个圣遗物部件的完整信息。"""
        return self.interpreter.interpret_single(item_id, index_context=index_context)

    def get_relic_as_json(self, item_id: int, index_context: Optional[Any] = None) -> Optional[Dict]:
        """获取单个圣遗物部件的JSON兼容字典。"""
        relic = self.get_relic_by_id(item_id, index_context=index_context)
        return asdict(relic) if relic else None

    def get_relic_as_markdown(self, item_id: int) -> Optional[str]:
        """获取单个圣遗物部件的格式化Markdown文档。"""
        relic = self.get_relic_by_id(item_id)
        if not relic:
            return None
        return self.formatter.format_relic(relic)
        
    def list_relic_sets(self) -> List[Dict[str, Any]]:
        """获取所有圣遗物套装的简明列表。"""
        all_sets = []
        all_set_ids = self.interpreter.get_all_set_ids()
        for set_id in all_set_ids:
            relic_set = self.interpreter.interpret(set_id)
            if relic_set:
                all_sets.append({
                    "id": relic_set.id,
                    "name": relic_set.name
                })
        return all_sets

    def get_relic_set_by_id(self, set_id: int, index_context: Optional[Any] = None) -> Optional[ReliquarySet]:
        """获取一个完整的圣遗物套装，包含所有部件。"""
        return self.interpreter.interpret(set_id, index_context=index_context)

    def get_relic_set_as_json(self, set_id: int, index_context: Optional[Any] = None) -> Optional[Dict]:
        """获取一个完整的圣遗物套装的JSON兼容字典。"""
        relic_set = self.get_relic_set_by_id(set_id, index_context=index_context)
        return asdict(relic_set) if relic_set else None

    def get_relic_set_as_markdown(self, set_id: int) -> Optional[str]:
        """获取圣遗物套装的格式化Markdown文档。"""
        relic_set = self.get_relic_set_by_id(set_id)
        if not relic_set:
            return None
        return self.formatter.format_relic_set(relic_set)

    def get_tree(self) -> List[Dict[str, Any]]:
        """
        为API层获取一个简化的、扁平的圣遗物套装列表，
        每个元素包含'id'和'title'，用于构建前端树状菜单。
        """
        all_sets_raw = self.list_relic_sets() # This returns a list of {"id": ..., "name": ...}
        
        # 统一键名为 'title' 以匹配API层的期望
        return [{"id": s["id"], "title": s["name"]} for s in all_sets_raw]
