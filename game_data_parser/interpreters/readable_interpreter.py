import logging
import re
from typing import Dict, List, Optional

from ..dataloader import DataLoader
from ..models import Readable

class ReadableInterpreter:
    """负责将 'Readable/' 目录下的文件解析成结构化的 Readable 对象。"""
    
    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
        self._readables: Dict[str, Readable] = {}
        self._is_prepared = False

    def _generate_title(self, content: str) -> str:
        if not content:
            return "(空内容)"
        clean_content = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', content)
        if not clean_content:
            return "(无有效字符)"
        title_body = clean_content[:5]
        return f"{title_body}…" if len(clean_content) > 5 else title_body

    def _prepare_data(self):
        if self._is_prepared:
            return
        
        logging.info("正在准备所有 Readable 对象的元数据...")
        # 关键修改：加载所有 .txt 文件，而不仅仅是世界文本
        all_readable_paths = self.loader.get_all_file_paths_in_folder("Readable/CHS", name_contains=".txt")
        
        for relative_path in all_readable_paths:
            # 从文件名（如 Book5.txt）中提取数字ID
            match = re.search(r'(\d+)\.txt$', relative_path)
            if not match:
                continue
            
            file_id = int(match.group(1))

            # 关键修复：读取内容以生成标题，但不进行“染色”
            raw_content = self.loader.get_text_file(relative_path, stain=False) or ""

            # 过滤掉测试数据
            if "test" in raw_content.lower():
                continue

            title = self._generate_title(raw_content)
            
            # 创建 Readable 对象，不存储 content，但传入 loader
            self._readables[file_id] = Readable(
                id=file_id,
                title=title,
                path=relative_path,
                _loader=self.loader
            )
        
        self._is_prepared = True
        logging.info(f"Readable 元数据准备完成，共找到 {len(self._readables)} 个。")

    def get_all_readables(self) -> List[Readable]:
        self._prepare_data()
        return list(self._readables.values())

    def interpret(self, readable_id: int) -> Optional[Readable]:
        self._prepare_data()
        return self._readables.get(readable_id)

    def interpret_from_path(self, relative_path: str) -> Optional[Readable]:
        """根据单个文件路径创建一个临时的 Readable 对象。"""
        match = re.search(r'(\d+)\.txt$', relative_path)
        if not match:
            return None
        
        file_id = int(match.group(1))
        
        # 关键修复：读取内容以生成标题，但不进行“染色”
        raw_content = self.loader.get_text_file(relative_path, stain=False) or ""
        title = self._generate_title(raw_content)
        
        return Readable(
            id=file_id,
            title=title,
            path=relative_path,
            _loader=self.loader
        )