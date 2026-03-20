"""
原神Wiki数据解析器工具模块

包含调试工具和数据生成工具
"""

from .debug_tool import GIWikiDebugTool
from .generate_markdown import main as generate_markdown

__all__ = [
    'GIWikiDebugTool',
    'generate_markdown'
]