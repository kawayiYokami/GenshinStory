from typing import Dict
from ..models.item import Item


class ItemFormatter:
    """
    物品对象格式化器，用于转换为各种输出格式。
    """

    @staticmethod
    def to_markdown(item: Item) -> str:
        """
        将物品对象格式化为 Markdown 字符串。

        参数:
            item: 要格式化的物品对象。

        返回:
            表示物品的 Markdown 格式字符串。
        """
        lines = []
        lines.append(f"# {item.name}")
        lines.append("")
        lines.append(f"**ID**: {item.id}")
        lines.append("")

        if item.description:
            lines.append("## 描述")
            lines.append(item.description)
            lines.append("")

        if item.story:
            lines.append("## 故事")
            lines.append(item.story)
            lines.append("")

        return "\n".join(lines)
    @staticmethod
    def to_dict(item: Item) -> Dict[str, any]:
        """
        将物品对象转换为字典。

        参数:
            item: 要转换的物品对象。

        返回:
            物品的字典表示。
        """
        return {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "story": item.story
        }