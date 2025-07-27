from hsr_data_parser.models import Relic

class RelicFormatter:
    """
    负责将 Relic 对象格式化为 Markdown 文本。
    """
    def format(self, relic: Relic) -> str:
        """
        将 Relic 对象（单个遗器套装）转换为格式化的 Markdown 字符串。
        """
        if not relic:
            return ""

        lines = [f"# {relic.name} (ID: {relic.id})"]
        
        if relic.parts:
            for part in relic.parts:
                lines.append(f"\n## {part.name}")
                story_content = part.story.replace('\\n', '  \n')
                lines.append(f"\n{story_content}")
                
        return "\n".join(lines)