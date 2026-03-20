from giwiki_data_parser.models.quest_43 import Quest, SubQuest, DialogueEntry, DialogueChoice, QuestNPC

class QuestFormatter:
    """任务格式化器"""

    def format(self, item: Quest, output_format: str = "markdown", quest_title: str = None) -> str:
        """将任务对象格式化为指定格式的字符串

        Args:
            item: 任务对象
            output_format: 输出格式，支持 "markdown" 或 "html"
            quest_title: 总标题（可选）
        """
        if not isinstance(item, Quest):
            return ""

        # 检查是否包含子任务
        if item.sub_quests:
            # 多子任务格式
            if output_format.lower() == "html":
                return self._format_multi_sub_quest_html(item, quest_title)
            else:
                return self._format_multi_sub_quest_markdown(item, quest_title)
        else:
            # 单任务格式（向后兼容）
            if output_format.lower() == "html":
                return self._format_html(item, quest_title)
            else:
                return self._format_markdown(item, quest_title)

    def _format_markdown(self, item: Quest, quest_title: str = None) -> str:
        """格式化为Markdown（向后兼容单任务格式）"""
        md_lines = []

        # 1. 总标题（如果提供）
        if quest_title:
            md_lines.append(f"# {quest_title}")
            md_lines.append("")

        # 2. 任务名称
        md_lines.append(f"## {item.name}")
        md_lines.append("")

        # 3. 提示信息（因为新模型不包含具体任务内容）
        md_lines.append("### 任务信息")
        md_lines.append("")
        md_lines.append("- **注意**: 此任务使用新的数据模型，具体内容请查看子任务")
        md_lines.append("")

        return '\n'.join(md_lines)

    def _format_html(self, item: Quest, quest_title: str = None) -> str:
        """格式化为HTML（向后兼容单任务格式）"""
        html_parts = []

        # 1. 总标题（如果提供）
        if quest_title:
            html_parts.append(f"<h1>{self._escape_html(quest_title)}</h1>")

        # 2. 任务名称
        html_parts.append(f"<h2>{self._escape_html(item.name)}</h2>")

        # 3. 提示信息（因为新模型不包含具体任务内容）
        html_parts.append("<h3>任务信息</h3>")
        html_parts.append("<ul>")
        html_parts.append("<li><strong>注意</strong>: 此任务使用新的数据模型，具体内容请查看子任务</li>")
        html_parts.append("</ul>")

        return '\n'.join(html_parts)

    def _format_dialogue_markdown(self, dialogue: DialogueEntry) -> list:
        """格式化单个对话为Markdown"""
        lines = []

        # 场景标题 - 隐藏发言人，用引述格式
        if dialogue.dialogue_type == "scene":
            lines.append(f"> {dialogue.text}")
            lines.append("")
        # 系统提示 - 跳过【选择以下选项】等系统消息
        elif dialogue.dialogue_type == "system":
            # 跳过系统提示，不输出
            pass
        # 选择项
        elif dialogue.dialogue_type == "choice":
            lines.append(f"{dialogue.text}")
            lines.append("")  # 添加空行
        # 特殊对话 - 隐藏发言人，用斜体
        elif dialogue.special_type == "special":
            lines.append(f"*{dialogue.text}*")
            lines.append("")
        # 普通对话
        elif dialogue.speaker and dialogue.text:
            # 场景标题类的发言人（包含"标题"关键词）- 用引述格式
            if "标题" in dialogue.speaker:
                lines.append(f"> {dialogue.text}")
                lines.append("")
            # 旁白 - 直接显示
            elif dialogue.speaker == "旁白":
                lines.append(dialogue.text)
                lines.append("")
            # 普通对话
            else:
                lines.append(f"{dialogue.speaker}: {dialogue.text}")
                lines.append("")

        return lines

    def _format_dialogue_html(self, dialogue: DialogueEntry) -> list:
        """格式化单个对话为HTML"""
        parts = []

        # 场景标题
        if dialogue.dialogue_type == "scene":
            parts.append(f'<h3 class="scene-title">{self._escape_html(dialogue.text)}</h3>')
        # 系统提示
        elif dialogue.dialogue_type == "system":
            parts.append(f'<div class="system-message"><em>{self._escape_html(dialogue.text)}</em></div>')
        # 选择项
        elif dialogue.dialogue_type == "choice":
            parts.append(f'<div class="choice-option">{self._escape_html(dialogue.text)}</div>')
        # 特殊对话
        elif dialogue.special_type == "special":
            parts.append(f'<div class="special-dialogue"><em><strong>{self._escape_html(dialogue.speaker)}</strong>: {self._escape_html(dialogue.text)}</em></div>')
        # 普通对话
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
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#x27;"))

    def get_filename(self, item: Quest) -> str:
        """生成文件名"""
        if not isinstance(item, Quest):
            return "unknown_quest.md"

        # 使用任务名称作为文件名，清理特殊字符
        filename = item.name or f"quest_{item.id}"
        # 清理文件名中的特殊字符
        filename = filename.replace("/", "_").replace("\\", "_").replace(":", "_")
        filename = filename.replace("*", "_").replace("?", "_").replace('"', "_")
        filename = filename.replace("<", "_").replace(">", "_").replace("|", "_")

        return f"{filename}.md"

    def _format_multi_sub_quest_markdown(self, item: Quest, quest_title: str = None) -> str:
        """格式化包含多个子任务的任务为Markdown"""
        md_lines = []

        # 1. 总标题（如果提供）
        if quest_title:
            md_lines.append(f"# {quest_title}")
            md_lines.append("")

        # 2. 任务标题和基本信息
        md_lines.append(f"**任务标题**: {item.name}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

        # 3. 遍历所有子任务
        for i, sub_quest in enumerate(item.sub_quests):
            # 子任务标题
            md_lines.append(f"## {sub_quest.name}")
            md_lines.append("")

            # 子任务信息
            md_lines.append("### 任务信息")
            md_lines.append("")
            if sub_quest.special_requirements:
                md_lines.append(f"- **触发条件**: {sub_quest.special_requirements}")
            else:
                md_lines.append("- **触发条件**: 无")
            if sub_quest.start_npc and sub_quest.start_npc.name:
                md_lines.append(f"- **起始NPC**: {sub_quest.start_npc.name}")
            if sub_quest.end_npc and sub_quest.end_npc.name:
                md_lines.append(f"- **结束NPC**: {sub_quest.end_npc.name}")
            md_lines.append("")

            # 子任务过程
            if sub_quest.quest_steps:
                md_lines.append("### 任务过程")
                md_lines.append("")
                for j, step in enumerate(sub_quest.quest_steps, 1):
                    clean_step = step.lstrip("•").strip()
                    md_lines.append(f"{j}. {clean_step}")
                md_lines.append("")

            # 子任务剧情对话
            if sub_quest.dialogue_content:
                md_lines.append("### 剧情对话")
                md_lines.append("")

                for dialogue in sub_quest.dialogue_content:
                    md_lines.extend(self._format_dialogue_markdown(dialogue))

            # 如果不是最后一个子任务，添加分隔符
            if i < len(item.sub_quests) - 1:
                md_lines.append("")
                md_lines.append("---")
                md_lines.append("")

        return '\n'.join(md_lines)

    def _format_multi_sub_quest_html(self, item: Quest, quest_title: str = None) -> str:
        """格式化包含多个子任务的任务为HTML"""
        html_parts = []

        # 1. 总标题（如果提供）
        if quest_title:
            html_parts.append(f"<h1>{self._escape_html(quest_title)}</h1>")

        # 2. 任务标题和基本信息
        html_parts.append("<h1>任务数据测试输出</h1>")
        html_parts.append(f"<p><strong>源文件</strong>: {self._escape_html(item.id)}.json</p>" if hasattr(item, 'id') and item.id else "<p><strong>源文件</strong>: 未知</p>")
        html_parts.append(f"<p><strong>任务标题</strong>: {self._escape_html(item.name)}</p>")
        html_parts.append(f"<p><strong>任务数量</strong>: {len(item.sub_quests)}</p>")
        html_parts.append("<hr>")

        # 3. 遍历所有子任务
        for i, sub_quest in enumerate(item.sub_quests):
            # 子任务标题
            html_parts.append(f"<h2>{self._escape_html(sub_quest.name)}</h2>")

            # 子任务信息
            html_parts.append("<h3>任务信息</h3>")
            html_parts.append("<ul>")
            if sub_quest.special_requirements:
                html_parts.append(f"<li><strong>触发条件</strong>: {self._escape_html(sub_quest.special_requirements)}</li>")
            else:
                html_parts.append("<li><strong>触发条件</strong>: 无</li>")
            if sub_quest.start_npc and sub_quest.start_npc.name:
                html_parts.append(f"<li><strong>起始NPC</strong>: {self._escape_html(sub_quest.start_npc.name)}</li>")
            if sub_quest.end_npc and sub_quest.end_npc.name:
                html_parts.append(f"<li><strong>结束NPC</strong>: {self._escape_html(sub_quest.end_npc.name)}</li>")
            html_parts.append("</ul>")

            # 子任务过程
            if sub_quest.quest_steps:
                html_parts.append("<h3>任务过程</h3>")
                html_parts.append("<ol>")
                for step in sub_quest.quest_steps:
                    clean_step = step.lstrip("•").strip()
                    html_parts.append(f"<li>{self._escape_html(clean_step)}</li>")
                html_parts.append("</ol>")

            # 子任务剧情对话
            if sub_quest.dialogue_content:
                html_parts.append("<h3>剧情对话</h3>")
                html_parts.append('<div class="dialogue-content">')

                for dialogue in sub_quest.dialogue_content:
                    html_parts.extend(self._format_dialogue_html(dialogue))

                html_parts.append("</div>")

            # 如果不是最后一个子任务，添加分隔符
            if i < len(item.sub_quests) - 1:
                html_parts.append("<hr>")

        return '\n'.join(html_parts)