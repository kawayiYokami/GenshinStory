# -*- coding: utf-8 -*-
from typing import Optional

from ..utils.text_transformer import transform_text

class OrphanTextFormatter:
    """
    负责将单个零散文本条目格式化为可读的Markdown文档。
    """
    def format_as_markdown(self, text_id: int, original_text: str) -> Optional[str]:
        """
        将给定的原始文本进行深度清洗，并格式化为Markdown。

        :param text_id: 文本的唯一ID。
        :param original_text: 从TextMap中获取的原始字符串。
        :return: 格式化后的Markdown字符串。
        """
        if not original_text:
            return None

        # 使用全局的文本转换器进行深度清洗
        # 这里的 gender 和 player_name 使用默认值，因为零散文本通常不包含这些占位符
        cleaned_text, _ = transform_text(original_text)

        # 构建Markdown内容
        markdown_content = f"# 零散文本 (ID: {text_id})\n\n"
        markdown_content += "## 内容\n\n"
        markdown_content += f"{cleaned_text}\n"
        
        return markdown_content