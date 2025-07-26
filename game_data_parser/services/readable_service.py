from typing import Any, Dict, List, Optional

from ..dataloader import DataLoader
from ..interpreters.readable_interpreter import ReadableInterpreter
from ..models import Readable
from ..formatters.readable_formatter import ReadableFormatter

class ReadableService:
    def __init__(self, loader: DataLoader):
        self.interpreter = ReadableInterpreter(loader)
        self.formatter = ReadableFormatter()

    def list_readables(self) -> List[Dict[str, str]]:
        all_readables = self.interpreter.get_all_readables()
        return [{"id": r.id, "title": r.title} for r in sorted(all_readables, key=lambda x: x.id)]

    def list_world_texts(self) -> List[Dict[str, str]]:
        """
        仅列出被识别为“世界文本”的读物。
        """
        world_text_paths = self.interpreter.loader.get_world_text_paths()
        
        world_texts = []
        for path in world_text_paths:
            readable = self.interpreter.interpret_from_path(path)
            if readable:
                world_texts.append({"id": readable.id, "title": readable.title})
        
        return sorted(world_texts, key=lambda x: x['id'])

    def get_readable_by_id(self, readable_id: int) -> Optional[Readable]:
        return self.interpreter.interpret(readable_id)

    def get_readable_as_markdown(self, readable_id: int) -> Optional[str]:
        """获取单个读物的完整Markdown文档。"""
        readable = self.get_readable_by_id(readable_id)
        if not readable:
            return None
        
        return self.formatter.format_readable(readable)
