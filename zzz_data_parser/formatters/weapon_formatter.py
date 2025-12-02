from typing import Dict, Any
from ..models.weapon import Weapon


class WeaponFormatter:
    """
    武器对象格式化器，用于转换为各种输出格式。
    """

    @staticmethod
    def to_markdown(weapon: Weapon) -> str:
        """
        将武器对象格式化为 Markdown 字符串。

        参数:
            weapon: 要格式化的武器对象。

        返回:
            表示武器的 Markdown 格式字符串。
        """
        lines = []
        lines.append(f"# {weapon.name}")
        lines.append("")

        if weapon.description:
            lines.append("## 描述")
            lines.append(weapon.description)
            lines.append("")

        if weapon.story:
            lines.append("## 故事")
            lines.append(weapon.story)
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_dict(weapon: Weapon) -> Dict[str, Any]:
        """
        将武器对象转换为字典。

        参数:
            weapon: 要转换的武器对象。

        返回:
            武器的字典表示。
        """
        return {
            "id": weapon.id,
            "name": weapon.name,
            "description": weapon.description,
            "story": weapon.story,
            "model_id": weapon.model_id
        }