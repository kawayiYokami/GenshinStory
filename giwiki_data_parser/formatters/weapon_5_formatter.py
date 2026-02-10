from giwiki_data_parser.models.weapon_5 import Weapon

class WeaponFormatter:
    """武器格式化器"""
    
    def format(self, item: Weapon) -> str:
        """将武器对象格式化为Markdown字符串"""
        if not isinstance(item, Weapon):
            return ""

        md_lines = []

        # 1. 标题
        md_lines.append(f"# {item.name}")
        md_lines.append("")

        # 2. 基本信息
        md_lines.append("## 基本信息")
        md_lines.append("")
        if item.rarity:
            stars = "★" * item.rarity
            md_lines.append(f"- **稀有度**: {stars}")
        if item.weapon_type:
            md_lines.append(f"- **武器类型**: {item.weapon_type}")
        if item.description:
            md_lines.append(f"- **描述**: {item.description}")
        md_lines.append("")

        # 3. 武器故事
        if item.story:
            md_lines.append("## 武器故事")
            md_lines.append("")
            # 直接添加故事文本，保留其原始换行
            md_lines.append(item.story)
            md_lines.append("")

        return '\n'.join(md_lines)