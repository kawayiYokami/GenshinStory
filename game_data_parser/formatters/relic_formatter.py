from typing import Optional
from ..models import Reliquary, ReliquarySet

class RelicFormatter:
    """
    负责将圣遗物相关的模型格式化为用户友好的字符串，如Markdown。
    """
    def format_relic(self, relic: Reliquary) -> str:
        """
        将单个圣遗物部件对象格式化为 Markdown。
        """
        md = []
        md.append(f"# {relic.name}")
        md.append("\n---")
        
        md.append(f"\n**描述**\n\n{relic.description}")
        
        if relic.story:
            md.append(f"\n\n**故事**\n\n{relic.story}")

        return "\n".join(md)

    def format_relic_set(self, relic_set: ReliquarySet) -> str:
        """
        将一个完整的圣遗物套装对象格式化为 Markdown。
        """
        md = []
        md.append(f"# {relic_set.name}")

        if relic_set.effect_2_piece:
            md.append(f"\n\n**2件套**: {relic_set.effect_2_piece}")
        if relic_set.effect_4_piece:
            md.append(f"**4件套**: {relic_set.effect_4_piece}")

        md.append("\n\n---")

        # Interpreter 已经通过 pos_index 对圣遗物列表进行了排序。
        # 我们只需要直接遍历并格式化即可。
        for relic in relic_set.reliquaries:
            md.append(f"\n\n## {relic.name} ({relic.pos_name})")
            
            # 描述和故事都应放在同一个引述块中
            content_to_format = ""
            if relic.description:
                content_to_format += relic.description.strip()

            if relic.story:
                if content_to_format:
                    content_to_format += "\\n\\n"
                content_to_format += relic.story.strip()
            
            if content_to_format:
                formatted_content = content_to_format.replace('\\n', '\n> ')
                md.append(f"\n\n> {formatted_content}")
            
        return "\n".join(md)
