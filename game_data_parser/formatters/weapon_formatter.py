from typing import Optional
from ..models import Weapon

class WeaponFormatter:
    """
    负责将武器相关的模型格式化为用户友好的字符串，如Markdown。
    """
    def format_weapon(self, weapon: Weapon) -> str:
        """
        将单个 Weapon 对象格式化为 Markdown。
        """
        md = []
        md.append(f"# {weapon.name} ({'★' * weapon.rank_level})")
        md.append("\n---")
        
        # 描述应放入引述块，不带 "描述" 标签
        if weapon.description:
            formatted_description = weapon.description.strip().replace('\\n', '\n> ')
            md.append(f"\n> {formatted_description}")

        # 故事作为正文，不带 "故事" 标签
        if weapon.story:
            formatted_story = weapon.story.strip().replace('\\n', '\n\n')
            md.append(f"\n\n{formatted_story}")

        return "\n".join(md)