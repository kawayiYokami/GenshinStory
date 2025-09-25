from giwiki_data_parser.models.outfit_211 import OutfitModel

class OutfitFormatter:
    """装扮格式化器"""

    def format(self, item: OutfitModel) -> str:
        """将装扮对象格式化为Markdown字符串"""
        if not isinstance(item, OutfitModel):
            return ""

        md_lines = []

        # 1. 标题
        md_lines.append(f"# {item.name}")
        md_lines.append("")

        # 2. 简介（如果有）
        if item.has_introduction():
            md_lines.append("## 简介")
            md_lines.append("")
            md_lines.append(item.introduction)
            md_lines.append("")

        # 3. 故事（如果有）
        if item.has_story():
            md_lines.append("## 故事")
            md_lines.append("")
            md_lines.append(item.story)
            md_lines.append("")

        return '\n'.join(md_lines)

    def get_filename(self, item: OutfitModel) -> str:
        """生成文件名"""
        if not isinstance(item, OutfitModel):
            return "unknown.md"

        # 清理文件名中的特殊字符
        safe_name = item.name.replace("「", "").replace("」", "").replace("/", "-").replace("\\", "-")
        safe_name = safe_name.replace(":", "-").replace("*", "-").replace("?", "-")
        safe_name = safe_name.replace("<", "-").replace(">", "-").replace("|", "-")

        # 如果有ID，添加到文件名中
        if item.id:
            return f"{safe_name}-{item.id}.md"
        else:
            return f"{safe_name}.md"