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
        # 主文档部分
        parts = []
        parts.append(f"# {relic_set.name}")

        # 套装效果
        effect_parts = []
        if relic_set.effect_2_piece:
            effect_parts.append(f"**2件套**: {relic_set.effect_2_piece}")
        if relic_set.effect_4_piece:
            effect_parts.append(f"**4件套**: {relic_set.effect_4_piece}")
        if effect_parts:
            parts.append("\n".join(effect_parts))

        parts.append("---")

        # 各个部件
        for relic in relic_set.reliquaries:
            relic_md_parts = []
            relic_md_parts.append(f"## {relic.name} ({relic.pos_name})")
            
            # 描述（引述块）
            if relic.description:
                cleaned_description = relic.description.replace('\\n', '\n')
                paragraphs = [p.strip() for p in cleaned_description.split('\n') if p.strip()]
                if paragraphs:
                    formatted_content = "> " + "\n> \n> ".join(paragraphs)
                    relic_md_parts.append(formatted_content)

            # 故事（Story）应该完全保留原文格式
            if relic.story:
                # 直接使用原始字符串，仅去除首尾空白
                relic_md_parts.append(relic.story.strip())
            
            # 将单个部件的所有内容合并成一个字符串
            parts.append("\n\n".join(relic_md_parts))
            
        # 用两个换行符连接主文档的各个部分，以确保章节间距
        return "\n\n".join(parts)
