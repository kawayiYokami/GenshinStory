from typing import Dict, Any
from ..models.weapon import Weapon


class WeaponFormatter:
    """
    Formatter for converting Weapon objects into various output formats.
    """

    @staticmethod
    def to_markdown(weapon: Weapon) -> str:
        """
        Formats a Weapon object into a Markdown string.

        Args:
            weapon: The Weapon object to format.

        Returns:
            A Markdown formatted string representing the weapon.
        """
        lines = []
        lines.append(f"# 武器: {weapon.name} (ID: {weapon.id})")
        lines.append(f"**型号**: {weapon.model_id}")
        lines.append("")

        if weapon.description:
            lines.append("## 功能描述")
            lines.append(weapon.description)
            lines.append("")

        if weapon.story:
            lines.append("## 背景故事")
            lines.append(weapon.story)
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_dict(weapon: Weapon) -> Dict[str, Any]:
        """
        Converts a Weapon object into a dictionary.

        Args:
            weapon: The Weapon object to convert.

        Returns:
            A dictionary representation of the weapon.
        """
        return {
            "id": weapon.id,
            "name": weapon.name,
            "description": weapon.description,
            "story": weapon.story,
            "model_id": weapon.model_id
        }