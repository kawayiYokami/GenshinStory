from giwiki_data_parser.models.domain_54 import DomainModel

class DomainFormatter:
    """秘境格式化器"""

    def format(self, item: DomainModel) -> str:
        """将秘境对象格式化为Markdown字符串"""
        if not isinstance(item, DomainModel):
            return ""

        md_lines = []

        # 1. 标题
        md_lines.append(f"# {item.name}")
        md_lines.append("")

        # 2. 简述
        if item.brief:
            md_lines.append("## 简述")
            md_lines.append("")
            for brief_item in item.brief:
                if brief_item.name:
                    md_lines.append(f"### {brief_item.name}")
                    md_lines.append("")
                if brief_item.description:
                    md_lines.append(brief_item.description)
                    md_lines.append("")

        return '\n'.join(md_lines)