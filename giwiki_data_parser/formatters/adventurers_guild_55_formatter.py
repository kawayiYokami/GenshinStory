from giwiki_data_parser.models.adventurers_guild_55 import AdventurerGuild, AdventurerGuildSubTask, DialogueEntry

class AdventurerGuildFormatter:
    """冒险家协会格式化器"""

    def format(self, item: AdventurerGuild, output_format: str = "markdown", guild_title: str = None) -> str:
        """将冒险家协会对象格式化为指定格式的字符串"""
        if not isinstance(item, AdventurerGuild):
            return ""

        if item.sub_tasks:
            if output_format.lower() == "html":
                return self._format_multi_sub_task_html(item, guild_title)
            else:
                return self._format_multi_sub_task_markdown(item, guild_title)
        else:
            if output_format.lower() == "html":
                return self._format_html(item, guild_title)
            else:
                return self._format_markdown(item, guild_title)

    def _format_markdown(self, item: AdventurerGuild, guild_title: str = None) -> str:
        """格式化为Markdown"""
        md_lines = []
        if guild_title:
            md_lines.append(f"# {guild_title}")
            md_lines.append("")
        md_lines.append(f"## {item.name}")
        md_lines.append("")
        md_lines.append("### 任务信息")
        md_lines.append("- 使用新的数据模型，具体内容请查看子任务")
        return '\n'.join(md_lines)

    def _format_html(self, item: AdventurerGuild, guild_title: str = None) -> str:
        """格式化为HTML"""
        html_parts = []
        if guild_title:
            html_parts.append(f"<h1>{self._escape_html(guild_title)}</h1>")
        html_parts.append(f"<h2>{self._escape_html(item.name)}</h2>")
        html_parts.append("<h3>任务信息</h3>")
        html_parts.append("<ul><li>使用新的数据模型，具体内容请查看子任务</li></ul>")
        return '\n'.join(html_parts)

    def _format_dialogue_markdown(self, dialogue: DialogueEntry) -> list:
        """格式化单个对话为Markdown"""
        lines = []
        if dialogue.dialogue_type == "scene":
            lines.append(f"> {dialogue.text}")
        elif dialogue.dialogue_type == "choice":
            lines.append(f"{dialogue.text}")
        elif dialogue.speaker and dialogue.text:
            if "标题" in dialogue.speaker:
                lines.append(f"> {dialogue.text}")
            elif dialogue.speaker == "旁白":
                lines.append(dialogue.text)
            else:
                lines.append(f"{dialogue.speaker}: {dialogue.text}")
        return lines

    def _format_dialogue_html(self, dialogue: DialogueEntry) -> list:
        """格式化单个对话为HTML"""
        parts = []
        if dialogue.dialogue_type == "scene":
            parts.append(f'<h3 class="scene-title">{self._escape_html(dialogue.text)}</h3>')
        elif dialogue.dialogue_type == "choice":
            parts.append(f'<div class="choice-option">{self._escape_html(dialogue.text)}</div>')
        elif dialogue.speaker and dialogue.text:
            if dialogue.speaker == "旁白":
                parts.append(f'<div class="narrator">{self._escape_html(dialogue.text)}</div>')
            else:
                parts.append(f'<div class="dialogue"><strong>{self._escape_html(dialogue.speaker)}</strong>: {self._escape_html(dialogue.text)}</div>')
        return parts

    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        if not text:
            return ""
        return (text.replace("&", "&")
                    .replace("<", "<")
                    .replace(">", ">")
                    .replace('"', """)
                    .replace("'", "&#x27;"))

    def get_filename(self, item: AdventurerGuild) -> str:
        """生成文件名"""
        if not isinstance(item, AdventurerGuild):
            return "unknown_guild.md"
        filename = item.name or f"guild_{item.id}"
        filename = filename.replace("/", "_").replace("\\", "_").replace(":", "_")
        filename = filename.replace("*", "_").replace("?", "_").replace('"', "_")
        filename = filename.replace("<", "_").replace(">", "_").replace("|", "_")
        return f"{filename}.md"

    def _format_multi_sub_task_markdown(self, item: AdventurerGuild, guild_title: str = None) -> str:
        """格式化包含多个子任务的冒险家协会任务为Markdown"""
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

            md_lines.append("### 任务信息")
            md_lines.append("")
            if sub_task.trigger_condition:
                md_lines.append(f"- **触发条件**: {sub_task.trigger_condition}")
            else:
                md_lines.append("- **触发条件**: 无")
            md_lines.append("")

            if sub_task.quest_steps:
                md_lines.append("### 任务过程")
                md_lines.append("")
                for j, step in enumerate(sub_task.quest_steps, 1):
                    clean_step = step.lstrip("•").strip()
                    md_lines.append(f"{j}. {clean_step}")
                md_lines.append("")

            if sub_task.dialogue_content:
                md_lines.append("### 剧情对话")
                md_lines.append("")
                for dialogue in sub_task.dialogue_content:
                    md_lines.extend(self._format_dialogue_markdown(dialogue))
                md_lines.append("")

            if i < len(item.sub_tasks) - 1:
                md_lines.append("---")
                md_lines.append("")

        return '\n'.join(md_lines)

    def _format_multi_sub_task_html(self, item: AdventurerGuild, guild_title: str = None) -> str:
        """格式化包含多个子任务的冒险家协会任务为HTML"""
        html_parts = []

        if guild_title:
            html_parts.append(f"<h1>{self._escape_html(guild_title)}</h1>")

        html_parts.append("<h1>冒险家协会任务数据</h1>")
        html_parts.append(f"<p><strong>任务标题</strong>: {self._escape_html(item.name)}</p>")
        html_parts.append(f"<p><strong>子任务数量</strong>: {len(item.sub_tasks)}</p>")
        html_parts.append("<hr>")

        for i, sub_task in enumerate(item.sub_tasks):
            html_parts.append(f"<h2>{self._escape_html(sub_task.name)}</h2>")

            html_parts.append("<h3>任务信息</h3>")
            html_parts.append("<ul>")
            if sub_task.trigger_condition:
                html_parts.append(f"<li><strong>触发条件</strong>: {self._escape_html(sub_task.trigger_condition)}</li>")
            else:
                html_parts.append("<li><strong>触发条件</strong>: 无</li>")
            html_parts.append("</ul>")

            if sub_task.quest_steps:
                html_parts.append("<h3>任务过程</h3>")
                html_parts.append("<ol>")
                for step in sub_task.quest_steps:
                    clean_step = step.lstrip("•").strip()
                    html_parts.append(f"<li>{self._escape_html(clean_step)}</li>")
                html_parts.append("</ol>")

            if sub_task.dialogue_content:
                html_parts.append("<h3>剧情对话</h3>")
                html_parts.append('<div class="dialogue-content">')
                for dialogue in sub_task.dialogue_content:
                    html_parts.extend(self._format_dialogue_html(dialogue))
                html_parts.append("</div>")

            if i < len(item.sub_tasks) - 1:
                html_parts.append("<hr>")

        return '\n'.join(html_parts)