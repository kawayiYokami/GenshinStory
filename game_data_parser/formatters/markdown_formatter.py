from game_data_parser.models import Quest

class MarkdownFormatter:
    """
    负责将Quest对象格式化为Markdown文本。
    """
    def format(self, quest: Quest, include_series_header: bool = True) -> str:
        """
        将Quest对象转换为格式化的Markdown字符串。

        :param quest: 要格式化的Quest对象。
        :param include_series_header: 是否包含系列的H1大标题。
        """
        if not quest:
            return "Error: Invalid Quest object provided."

        lines = []
        
        if include_series_header:
            header_parts = []
            if quest.chapter_num:
                header_parts.append(quest.chapter_num)
            header_parts.append(quest.chapter_title)
            
            meta_parts = []
            if quest.quest_type:
                meta_parts.append(quest.quest_type)
            meta_parts.append(f"Chapter ID: {quest.chapter_id}")
            
            lines.append(f"# {' '.join(header_parts)} ({', '.join(meta_parts)})")
        
        lines.append(f"## {quest.quest_title} (Quest ID: {quest.quest_id})")
        if quest.quest_description:
            lines.append(f"_{quest.quest_description}_")
        lines.append("\n---")

        if not quest.steps:
            lines.append("\n_This quest has no detailed steps or dialogue information._")
        else:
            for step in quest.steps:
                step_desc = step.step_description or ""
                lines.append(f"\n### {step_desc} (Step: {step.step_id})")

                if step.dialogue:
                    lines.append("```")
                    for dialog in step.dialogue:
                        lines.append(f"{dialog.speaker}: {dialog.content}")
                    lines.append("```")

        return "\n".join(lines)