from typing import Dict, Any
from ..models.vhs_collection import VHSCollection


class VHSCollectionFormatter:
    """
    Formatter for converting VHSCollection objects into various output formats.
    """

    @staticmethod
    def to_markdown(vhs_collection: VHSCollection) -> str:
        """
        Formats a VHSCollection object into a Markdown string.

        Args:
            vhs_collection: The VHSCollection object to format.

        Returns:
            A Markdown formatted string representing the VHS collection item.
        """
        lines = []
        lines.append(f"# 录像带: {vhs_collection.name} (ID: {vhs_collection.id})")
        lines.append("")

        if vhs_collection.description:
            lines.append("## 描述")
            lines.append(vhs_collection.description)
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_dict(vhs_collection: VHSCollection) -> Dict[str, Any]:
        """
        Converts a VHSCollection object into a dictionary.

        Args:
            vhs_collection: The VHSCollection object to convert.

        Returns:
            A dictionary representation of the VHS collection item.
        """
        return {
            "id": vhs_collection.id,
            "name": vhs_collection.name,
            "description": vhs_collection.description
        }