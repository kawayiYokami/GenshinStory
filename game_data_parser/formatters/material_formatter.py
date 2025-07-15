from typing import Dict, Optional

from ..models import Material

def format_material(material: Material, book_suits: Dict[int, str]) -> str:
    """
    将单个 Material 对象格式化为 Markdown 字符串，用于前端展示。

    Args:
        material: 要格式化的 Material 对象。
        book_suits: 一个从 set_id 到系列名称的映射字典，用于查找书籍所属的系列。

    Returns:
        格式化后的 Markdown 字符串。
    """
    
    parts = []
    
    # 1. 标题 (物品名称)
    parts.append(f"# {material.name}")
    parts.append("---")


    # 3. 核心描述与故事
    # 描述和故事都应放在同一个引述块中
    content_to_format = ""
    if material.description:
        content_to_format += material.description.strip()

    if material.story:
        if content_to_format:
            content_to_format += "\\n\\n"
        content_to_format += material.story.strip()

    if content_to_format:
        formatted_content = content_to_format.replace('\\n', '\n> ')
        parts.append(f"> {formatted_content}")
        parts.append("")

    # 4. 书籍的特殊处理
    if material.is_book and material.set_id:
        series_name = book_suits.get(material.set_id)
        if series_name:
            parts.append("## 所属系列")
            parts.append(f"《{series_name}》")
            parts.append("")

    return "\n".join(parts)