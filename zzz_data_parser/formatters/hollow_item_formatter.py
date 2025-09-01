from typing import Dict
from ..models.hollow_item import HollowItem


class HollowItemFormatter:
    """
    Formatter for converting HollowItem objects into various output formats.
    """

    @staticmethod
    def to_markdown(item: HollowItem) -> str:
        """
        Formats a HollowItem object into a Markdown string.

        Args:
            item: The HollowItem object to format.

        Returns:
            A Markdown formatted string representing the hollow item.
        """
        lines = []
        lines.append(f"# 空洞道具: {item.name} (ID: {item.id})")
        lines.append("")

        if item.description:
            lines.append("## 描述")
            lines.append(item.description)
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_dict(item: HollowItem) -> Dict[str, any]:
        """
        Converts a HollowItem object into a dictionary.

        Args:
            item: The HollowItem object to convert.

        Returns:
            A dictionary representation of the hollow item.
        """
        return {
            "id": item.id,
            "name": item.name,
            "description": item.description
        }