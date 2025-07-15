from typing import Any, Dict, List, Optional

from ..dataloader import DataLoader
from ..interpreters.avatar_interpreter import AvatarInterpreter
from ..formatters.avatar_formatter import AvatarFormatter
from ..models import Avatar
from .base_service import BaseService


class AvatarService(BaseService):
    """
    提供所有与“角色(Avatar)”领域相关的查询和操作。
    """
    def __init__(self, loader: DataLoader):
        self.interpreter = AvatarInterpreter(loader)
        self.formatter = AvatarFormatter()
        super().__init__({}, {})

    def list(self, nation: Optional[str] = None, vision: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取所有角色的简明列表，支持按国家和神之眼筛选。
        """
        all_items = []
        all_avatar_ids = self.interpreter.get_all_avatar_ids()
        
        for avatar_id in all_avatar_ids:
            avatar = self.interpreter.interpret(avatar_id)
            if not avatar:
                continue

            # --- Filtering Logic ---
            if nation is not None and avatar.nation != nation:
                continue
            if vision is not None and avatar.vision != vision:
                continue
            
            all_items.append({
                "id": avatar.id,
                "name": avatar.name
            })
            
        return all_items

    def get(self, item_id: int) -> Optional[Avatar]:
        """获取单个角色的完整信息。"""
        return self.interpreter.interpret(item_id)

    def get_raw(self, item_id: int) -> Optional[Dict[str, Any]]:
        """获取角色的原始 JSON 数据。"""
        return self.interpreter.get_raw_data(item_id)

    def as_markdown(self, item_id: int) -> Optional[str]:
        """获取单个角色的格式化Markdown文档。"""
        avatar = self.get(item_id)
        if not avatar:
            return None
        return self.formatter.format_avatar(avatar)
