from typing import List
from hsrwiki_data_parser.models.rogue_miracle import RogueMiracle


class RogueMiracleFormatter:
    """
    Formats RogueMiracle objects into Markdown strings.
    """

    def format(self, item: RogueMiracle) -> str:
        """
        Formats a single RogueMiracle object into a Markdown string.
        """
        if not isinstance(item, RogueMiracle):
            return ""

        md_lines = []
        md_lines.append(f"### {item.name}")
        md_lines.append("")
        md_lines.append(f"**ID:** {item.id}")
        md_lines.append("")
        md_lines.append("**背景描述:**")
        md_lines.append("")
        md_lines.append(item.description)
        md_lines.append("")
        md_lines.append("---")  # Add a separator
        return "\n".join(md_lines)

    def format_all(self, items: List[RogueMiracle]) -> str:
        """
        Formats a list of RogueMiracle objects into a single Markdown string.
        """
        if not items:
            return "# 奇物列表\n\n暂无奇物数据。"

        md_parts = ["# 奇物列表\n"]
        for item in items:
            md_parts.append(self.format(item))

        return "\n".join(md_parts)