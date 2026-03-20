from giwiki_data_parser.models.adventurers_guild_55 import AdventurerGuild

class SimpleAdventurerGuildFormatter:
    """简化版冒险家协会格式化器"""

    def format(self, item: AdventurerGuild, output_format: str = "markdown", guild_title: str = None) -> str:
        """格式化冒险家协会对象"""
        if not isinstance(item, AdventurerGuild):
            return ""

        md_lines = []

        if guild_title:
            md_lines.append(f"# {guild_title}")
            md_lines.append("")

        md_lines.append(f"**任务标题**: {item.name}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

        for i, sub_task in enumerate(item.sub_tasks):
            md_lines.append(f"## {sub_task.name}")
            md_lines.append("")

            if sub_task.trigger_condition:
                md_lines.append(f"- **触发条件**: {sub_task.trigger_condition}")
                md_lines.append("")

            if sub_task.quest_steps:
                md_lines.append("### 任务过程")
                md_lines.append("")
                for j, step in enumerate(sub_task.quest_steps, 1):
                    md_lines.append(f"{j}. {step}")
                md_lines.append("")

            if sub_task.dialogue_content:
                md_lines.append("### 剧情对话")
                md_lines.append("")
                for dialogue in sub_task.dialogue_content:
                    if dialogue.speaker and dialogue.text:
                        md_lines.append(f"{dialogue.speaker}: {dialogue.text}")
                    elif dialogue.text:
                        md_lines.append(dialogue.text)
                md_lines.append("")

            if i < len(item.sub_tasks) - 1:
                md_lines.append("---")
                md_lines.append("")

        return '\n'.join(md_lines)

    def get_filename(self, item: AdventurerGuild) -> str:
        """生成文件名"""
        if not isinstance(item, AdventurerGuild):
            return "unknown_guild.md"
        filename = item.name or f"guild_{item.id}"
        filename = filename.replace("/", "_").replace("\\", "_").replace(":", "_")
        filename = filename.replace("*", "_").replace("?", "_").replace('"', "_")
        filename = filename.replace("<", "_").replace(">", "_").replace("|", "_")
        return f"{filename}.md"