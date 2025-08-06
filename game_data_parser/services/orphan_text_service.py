# -*- coding: utf-8 -*-
from typing import List, Optional, Dict

from ..dataloader import DataLoader
from ..formatters.orphan_text_formatter import OrphanTextFormatter
from .text_map_service import TextMapService

class OrphanTextService:
    """
    提供访问和处理“零散文本”数据的服务。
    “零散文本”指在TextMap中存在，但未被任何游戏内数据文件（如任务、书籍等）引用的文本。
    """
    def __init__(self, loader: DataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.formatter = OrphanTextFormatter()
        self.text_map_service = text_map_service

    def list_orphan_text_ids(self) -> List[Dict[str, int]]:
        """
        从DataLoader缓存中获取所有零散文本的ID列表。
        返回一个包含字典的列表，以便与现有接口保持一致。
        """
        ids = self.loader._orphan_text_ids or []
        # 为了与系统中其他 list_* 函数的返回格式保持一致
        return [{"id": id} for id in ids]

    def get_orphan_text_as_markdown(self, text_id: int) -> Optional[str]:
        """
        获取单个零散文本的完整Markdown文档。
        """
        # 从 TextMapService 获取原始文本
        original_text = self.text_map_service.get(text_id)
        if not original_text:
            return None
        
        # 使用 Formatter 进行格式化
        return self.formatter.format_as_markdown(text_id, original_text)