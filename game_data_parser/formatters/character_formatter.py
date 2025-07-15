from ..models import Avatar

class CharacterFormatter:
    """
    负责将Avatar对象格式化为美观的Markdown文本。
    """
    def format(self, avatar: Avatar) -> str:
        """
        将一个Avatar对象转换为格式化的Markdown字符串。
        """
        if not avatar:
            return "Error: Invalid Avatar object provided."

        lines = []

        # --- Header ---
        lines.append(f"# {avatar.name}")
        if avatar.description:
            lines.append(f"\n> _{avatar.description}_")
        lines.append("\n")

        # --- Profile ---
        lines.append("## 角色资料")
        if avatar.title: lines.append(f"- **称号**: {avatar.title}")
        if avatar.nation: lines.append(f"- **所属**: {avatar.nation}")
        if avatar.vision: lines.append(f"- **神之眼**: {avatar.vision}")
        if avatar.constellation: lines.append(f"- **命之座**: {avatar.constellation}")
        if avatar.birthday: lines.append(f"- **生日**: {avatar.birthday}")
        if avatar.cvs and (avatar.cvs.chinese or avatar.cvs.japanese):
            lines.append("- **声优**:")
            if avatar.cvs.chinese: lines.append(f"  - **中文**: {avatar.cvs.chinese}")
            if avatar.cvs.japanese: lines.append(f"  - **日文**: {avatar.cvs.japanese}")
            if avatar.cvs.english: lines.append(f"  - **英文**: {avatar.cvs.english}")
            if avatar.cvs.korean: lines.append(f"  - **韩文**: {avatar.cvs.korean}")
        lines.append("\n---")

        # --- Stories ---
        if avatar.stories:
            lines.append("\n## 角色故事\n")
            for story in avatar.stories:
                if story.title and story.text:
                    lines.append(f"### {story.title}")
                    # Replace \n with <br> for markdown line breaks
                    formatted_text = story.text.strip().replace('\\n', '<br>')
                    lines.append(f"{formatted_text}\n")
            lines.append("\n---")

        # --- Voice Lines ---
        if avatar.voice_lines:
            lines.append("\n## 语音台词\n")
            for voice in avatar.voice_lines:
                 if voice.title and voice.text:
                    lines.append(f"### {voice.title}")
                    # Replace \n with <br> for markdown line breaks
                    formatted_text = voice.text.strip().replace('\\n', '<br>')
                    lines.append(f"{formatted_text}\n")

        return "\n".join(lines)