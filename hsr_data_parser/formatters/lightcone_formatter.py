from hsr_data_parser.models import LightCone

class LightconeFormatter:
    """
    负责将 LightCone 对象格式化为 Markdown 文本。
    """
    def format(self, lightcone: LightCone) -> str:
        """
        将 LightCone 对象转换为格式化的 Markdown 字符串。
        """
        if not lightcone:
            return ""

        lines = [f"# {lightcone.name} (ID: {lightcone.id})"]
        
        if lightcone.description:
            desc = lightcone.description.replace('\n', '\n> ')
            lines.append(f"\n> {desc}")
            
        if lightcone.background_description:
            lines.append("\n---")
            bg_desc = lightcone.background_description.replace('\\n', '  \n')
            lines.append(f"\n{bg_desc}")

        return "\n".join(lines)