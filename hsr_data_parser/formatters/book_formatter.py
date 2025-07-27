from hsr_data_parser.models import Book

class BookFormatter:
    """
    负责将 Book 对象格式化为 Markdown 文本。
    """
    def format(self, book: Book) -> str:
        """
        将 Book 对象转换为格式化的 Markdown 字符串。
        """
        if not book:
            return ""

        lines = [f"# {book.name} (ID: {book.id})"]
        
        if book.content:
            lines.append("\n---")
            content = book.content.replace('\\n', '  \n')
            lines.append(f"\n{content}")

        return "\n".join(lines)