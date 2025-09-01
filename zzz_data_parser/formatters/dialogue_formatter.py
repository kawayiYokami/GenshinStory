from typing import Dict
from ..models.unified_dialogue import DialogueChapter, DialogueAct, DialogueLine


class DialogueFormatter:
    """
    将统一的对话数据模型格式化为不同输出格式的工具类。
    """

    def __init__(self, chapter: DialogueChapter):
        self.chapter = chapter

    def _format_single_act(self, act: DialogueAct, act_number: int) -> str:
        """
        将单个对话幕格式化为 Markdown 字符串。
        """
        md_lines = []

        # 幕标题
        md_lines.append(f"## 第 {act_number} 幕")
        md_lines.append("")
        # 出场角色
        if act.speakers:
            speaker_names = sorted(list(set(act.speakers.values())))
            md_lines.append(f"**出场角色**: {', '.join(speaker_names)}")
            md_lines.append("")

        # 对话内容
        sorted_lines = sorted(act.lines.items(), key=lambda item: int(item[0]))

        for line_num, line in sorted_lines:
            line_text = ""
            if line.speaker:
                line_text += f"**{line.speaker}**: "

            dialog_content = line.female_text or line.male_text or ""
            line_text += dialog_content.replace('\n', '  \n')

            md_lines.append(f"{line_text}")
            md_lines.append("")

            if line.options:
                md_lines.append("> **选项:**")
                for option_id, option_text in sorted(line.options.items()):
                    md_lines.append(f"> - {option_text}")
                md_lines.append("")

        return "\n".join(md_lines)

    def to_markdown_files(self) -> Dict[str, str]:
        """
        将对话章节转换为一个包含多个 Markdown 文件内容的字典。
        键是建议的文件名，值是文件内容。
        """
        files_dict = {}

        sorted_acts = sorted(self.chapter.acts.items(), key=lambda item: int(item[0]))

        act_number = 1
        for act_id, act in sorted_acts:
            filename = f"{self.chapter.id}-{act_number}.md"
            content = self._format_single_act(act, act_number)
            files_dict[filename] = content
            act_number += 1

        return files_dict

    def to_full_chapter_markdown(self) -> str:
        """
        将整个对话章节格式化为单个 Markdown 字符串。
        """
        all_act_contents = []

        sorted_acts = sorted(self.chapter.acts.items(), key=lambda item: int(item[0]))

        act_number = 1
        for act_id, act in sorted_acts:
            act_content = self._format_single_act(act, act_number)
            all_act_contents.append(act_content)
            act_number += 1

        return "\n\n---\n\n".join(all_act_contents)

    def to_dict(self) -> dict:
        """
        将对话章节转换为字典格式，便于序列化为 JSON。
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