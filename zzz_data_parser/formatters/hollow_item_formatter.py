from typing import Dict
from ..models.hollow_item import HollowItem


class HollowItemFormatter:
    """
    空洞道具对象格式化器，用于转换为各种输出格式。
    """

    @staticmethod
    def to_markdown(item: HollowItem) -> str:
        """
        将空洞道具对象格式化为 Markdown 字符串。

        参数:
            item: 要格式化的空洞道具对象。

        返回:
            表示空洞道具的 Markdown 格式字符串。
        """
        lines = []
        lines.append(f"# 空洞道具: {item.name}")
        lines.append("")

        if item.description:
            lines.append("## 描述")
            lines.append(item.description)
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_dict(item: HollowItem) -> Dict[str, any]:
        """
        将空洞道具对象转换为字典。

        参数:
            item: 要转换的空洞道具对象。

        返回:
            空洞道具的字典表示。
        """
        return {
            "id": item.id,
            "name": item.name,
            "description": item.description
        }