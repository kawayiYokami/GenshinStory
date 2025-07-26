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
    
    # 1. 标题和元数据
    parts.append(f"# {material.name}")
    parts.append(f"<!-- Material ID: {material.id} -->") # 修正：加入ID注释
    parts.append(f"**类型:** {material.type_name}")
    parts.append("")

    # 2. 核心描述与故事 (恢复原有精细处理逻辑)
    description_parts = []
    if material.description:
        cleaned_description = material.description.replace('\\n', '\n')
        paragraphs = [p.strip() for p in cleaned_description.split('\n') if p.strip()]
        description_parts.extend(paragraphs)

    if material.story:
        story_paragraphs = [p.strip() for p in material.story.replace("\\n", "\n").split('\n') if p.strip()]
        description_parts.extend(story_paragraphs)

    if description_parts:
        parts.append("## 描述")
        parts.append("\n\n".join(description_parts))
        parts.append("")

    # 3. 书籍的特殊处理 (恢复原有逻辑)
    if material.is_book and material.set_id:
        series_name = book_suits.get(material.set_id)
        if series_name:
            parts.append("## 所属系列")
            parts.append(f"《{series_name}》")
            parts.append("")

    return "\n".join(parts)