from typing import Dict, Any
from ..models.vhs_collection import VHSCollection


class VHSCollectionFormatter:
    """
    录像带收藏品对象格式化器，用于转换为各种输出格式。
    """

    @staticmethod
    def to_markdown(vhs_collection: VHSCollection) -> str:
        """
        将录像带收藏品对象格式化为 Markdown 字符串。

        参数:
            vhs_collection: 要格式化的录像带收藏品对象。

        返回:
            表示录像带收藏品的 Markdown 格式字符串。
        """
        lines = []
        lines.append(f"# 录像带: {vhs_collection.name}")
        lines.append("")

        if vhs_collection.description:
            lines.append("## 描述")
            lines.append(vhs_collection.description)
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_dict(vhs_collection: VHSCollection) -> Dict[str, Any]:
        """
        将录像带收藏品对象转换为字典。

        参数:
            vhs_collection: 要转换的录像带收藏品对象。

        返回:
            录像带收藏品的字典表示。
        """
        return {
            "id": vhs_collection.id,
            "name": vhs_collection.name,
            "description": vhs_collection.description
        }