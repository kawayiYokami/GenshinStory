from ..interpreters.models.unified_dialogue import DialogueChapter, DialogueAct, DialogueLine


class DialogueFormatter:
    """
    将统一的对话数据模型格式化为不同输出格式的工具类。
    """

    def __init__(self, chapter: DialogueChapter):
        self.chapter = chapter

    def to_markdown(self) -> str:
        """
        将 DialogueChapter 转换为 Markdown 格式的字符串。
        """
        md_lines = []

        # 章节标题
        title = f"# {self.chapter.id}"
        if self.chapter.category or self.chapter.sub_category:
            categories = [self.chapter.category, self.chapter.sub_category]
            title += f" ({' / '.join(filter(None, categories))})"
        md_lines.append(title)
        md_lines.append("")  # 空行

        # 遍历每个 Act
        for act_id, act in self.chapter.acts.items():
            md_lines.append(f"## Act: {act_id}")

            # 打印角色映射
            if act.speakers:
                md_lines.append("**角色映射:**")
                for speaker_key, speaker_name in act.speakers.items():
                    md_lines.append(f"  - {speaker_key}: {speaker_name}")
                md_lines.append("")  # 空行

            # 打印对话行
            md_lines.append("**对话内容:**")
            for line_num, line in act.lines.items():
                # 构建行文本
                line_text = ""
                if line.speaker:
                    line_text += f"{line.speaker}: "

                # 优先显示女性文本，如果没有则显示男性文本
                dialog_content = line.female_text or line.male_text or ""
                line_text += dialog_content

                md_lines.append(f"- [{line_num}] {line_text}")

                # 如果有选项，也打印出来
                if line.options:
                    for option_id, option_text in line.options.items():
                        md_lines.append(f"  - *选项 {option_id}*: {option_text}")

            md_lines.append("")  # Act之间的空行

        return "\n".join(md_lines)

    def to_dict(self) -> dict:
        """
        将 DialogueChapter 转换为字典格式，便于序列化为 JSON。
        """
        def _line_to_dict(line: DialogueLine) -> dict:
            return {
                "male_text": line.male_text,
                "female_text": line.female_text,
                "speaker": line.speaker,
                "options": line.options
            }

        def _act_to_dict(act: DialogueAct) -> dict:
            return {
                "id": act.id,
                "lines": {num: _line_to_dict(line) for num, line in act.lines.items()},
                "speakers": act.speakers
            }

        return {
            "id": self.chapter.id,
            "category": self.chapter.category,
            "sub_category": self.chapter.sub_category,
            "acts": {act_id: _act_to_dict(act) for act_id, act in self.chapter.acts.items()}
        }