from hsrwiki_data_parser.models.quest import Quest, AnyDialoguePart

class QuestFormatter:

    def _format_dialogue_part(self, part: AnyDialoguePart, indent_level: int = 0) -> str:
        indent = "    " * indent_level
        if part.type == 'dialogue':
            return f"{indent}**{part.speaker}:** {part.line}"
        elif part.type == 'description':
            return f"{indent}> {part.text}"
        elif part.type == 'quote':
            return f"{indent}> _{part.text}_"
        elif part.type == 'narrator':
            return f"{indent}*({part.line})*"
        elif part.type == 'options_group':
            lines = [f"{indent}- (玩家选项)"]
            for choice in part.choices:
                lines.append(f"{indent}    - **{choice.option}**")
                if choice.reply:
                    for reply_part in choice.reply:
                        lines.append(self._format_dialogue_part(reply_part, indent_level + 2))
            return '\n'.join(lines)
        return ""

    def format(self, item: Quest) -> str:
        if not isinstance(item, Quest):
            return ""

        md = []
        md.append(f"# {item.name}")
        md.append("\n---\n")

        if item.metadata:
            meta = item.metadata
            if meta.task_type: md.append(f"**类型:** {meta.task_type}")
            if meta.task_area: md.append(f"**地区:** {meta.task_area}")
            if meta.open_level: md.append(f"**开放等级:** {meta.open_level}")
            if meta.task_description: md.append(f"\n> {meta.task_description}\n")
            if meta.reward: md.append(f"**奖励:** {meta.reward}")

        if item.process:
            md.append("\n## 任务流程")
            for i, step in enumerate(item.process):
                md.append(f"{i+1}. {step}")
        
        if item.dialogue:
            md.append("\n## 任务对话")
            for part in item.dialogue:
                md.append(self._format_dialogue_part(part))

        return '\n'.join(md)
