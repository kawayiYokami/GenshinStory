from typing import Optional
from ..models import Readable
from ..utils.text_transformer import transform_text

class ReadableFormatter:
    """
    负责将 Readable 对象格式化为用户友好的字符串，例如 Markdown。
    """
    def format_readable(self, readable: Readable) -> str:
        """
        将一个 Readable 对象格式化为 Markdown。
        格式非常简单：一个一级标题，后跟全文内容。
        """
        if not readable:
            return ""
        
        # 从 Readable 对象按需获取内容并进行清理
        raw_content = readable.get_content()
        content, _ = transform_text(raw_content)
        
        # 返回格式化的 Markdown 字符串
        return f"# {readable.title}\n\n{content}"