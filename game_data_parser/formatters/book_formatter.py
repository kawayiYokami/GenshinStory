from typing import Optional
from ..models import Material, BookSuit, BookVolume

class BookFormatter:
    """
    负责将书籍相关的模型格式化为用户友好的字符串，如Markdown。
    """
    def format_book(self, book: Material, suit: Optional[BookSuit] = None) -> str:
        """
        将单个书籍 Material 对象格式化为 Markdown。
        此函数保持不变，因为它专注于单个物料。
        """
        if not book.is_book:
            return f"错误：物品 {book.name} (ID: {book.id}) 不是一本书籍。"

        md = []
        md.append(f"# {book.name}")
        md.append(f"> *物料 ID: {book.id}*")
        
        if suit:
            md.append(f"\n**系列**: {suit.name} (ID: {suit.id})")
        
        md.append("\n" + "="*20)
        md.append(f"\n**描述**\n\n{book.description}")

        return "\n".join(md)

    def format_book_series(self, suit: BookSuit) -> str:
        """
        将一个完整的 BookSuit 对象格式化为 Markdown。
        此版本通过将半角'~'替换为全角'～'来“中和”其特殊功能，
        从而忠实地再现原文排版，防止渲染错误。
        """
        if not suit.volumes:
            return ""

        volume_chunks = []
        for volume in suit.volumes:
            parts = [f"# {volume.volume_title}"]
            
            if volume.introduction:
                # 替换~，保留原始排版
                safe_intro = volume.introduction.replace('~', '～')
                parts.append(safe_intro)
            
            # 替换~，保留原始排版
            safe_content = volume.get_content().replace('~', '～')
            parts.append(safe_content)
            
            volume_chunks.append("\n".join(parts))

        return "\n\n".join(volume_chunks)