from hsr_data_parser.models import Miracle

class MiracleFormatter:
    """
    负责将 Miracle 对象格式化为 Markdown 文本。
    """
    def format(self, miracle: Miracle) -> str:
        """
        将 Miracle 对象转换为格式化的 Markdown 字符串。
        """
        if not miracle:
            return ""

        lines = [f"# {miracle.name} (ID: {miracle.id})"]
        
        if miracle.background_description:
            bg_desc = miracle.background_description.replace('\n', '\n> ')
            lines.append(f"\n> {bg_desc}")

        return "\n".join(lines)