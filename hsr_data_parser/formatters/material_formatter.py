from hsr_data_parser.models import Material

class MaterialFormatter:
    """
    负责将 Material 对象格式化为 Markdown 文本。
    """
    def format(self, material: Material) -> str:
        """
        将 Material 对象转换为格式化的 Markdown 字符串。
        """
        if not material:
            return ""

        lines = [f"# {material.name} (ID: {material.id})"]
        lines.append(f"_{material.main_type}_")
        
        if material.description:
            desc = material.description.replace('\n', '\n> ')
            lines.append(f"\n> {desc}")

        return "\n".join(lines)