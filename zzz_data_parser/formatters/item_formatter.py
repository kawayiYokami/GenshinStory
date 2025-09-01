from typing import Dict
from ..models.item import Item


class ItemFormatter:
    """
    Formatter for converting Item objects into various output formats.
    """

    @staticmethod
    def to_markdown(item: Item) -> str:
        """
        Formats an Item object into a Markdown string.

        Args:
            item: The Item object to format.

        Returns:
            A Markdown formatted string representing the item.
        """
        lines = []
        lines.append(f"# 道具: {item.name} (ID: {item.id})")
        lines.append("")

        if item.description:
            lines.append("## 功能描述")
            lines.append(item.description)
            lines.append("")

        if item.story:
            lines.append("## 背景故事")
            lines.append(item.story)
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_dict(item: Item) -> Dict[str, any]:
        """
        Converts an Item object into a dictionary.

        Args:
            item: The Item object to convert.

        Returns:
            A dictionary representation of the item.
        """
        return {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "story": item.story
        }