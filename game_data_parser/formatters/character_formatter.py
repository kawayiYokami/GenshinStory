from ..models.character import Character

class CharacterFormatter:
    """
    负责将Character对象格式化为美观的Markdown文本。
    """
    def format(self, character: Character) -> str:
        """
        将一个Character对象转换为格式化的Markdown字符串。
        """
        if not character:
            return "Error: Invalid Character object provided."

        lines = []

        # --- Header ---
        lines.append(f"# {character.name}")
        if character.description:
            lines.append(f"\n> _{character.description}_")
        lines.append("\n")

        # --- Profile ---
        lines.append("## 角色资料")
        if character.title: lines.append(f"- **称号**: {character.title}")
        if character.nation: lines.append(f"- **所属**: {character.nation}")
        if character.vision: lines.append(f"- **神之眼**: {character.vision}")
        if character.constellation: lines.append(f"- **命之座**: {character.constellation}")
        if character.birthday: lines.append(f"- **生日**: {character.birthday}")
        if character.cvs and (character.cvs.chinese or character.cvs.japanese):
            lines.append("- **声优**:")
            if character.cvs.chinese: lines.append(f"  - **中文**: {character.cvs.chinese}")
            if character.cvs.japanese: lines.append(f"  - **日文**: {character.cvs.japanese}")
            if character.cvs.english: lines.append(f"  - **英文**: {character.cvs.english}")
            if character.cvs.korean: lines.append(f"  - **韩文**: {character.cvs.korean}")
        lines.append("\n---")

        # --- Stories ---
        if character.stories:
            lines.append("\n## 角色故事\n")
            for story in character.stories:
                if story.title and story.text:
                    lines.append(f"### {story.title}")
                    # Replace \n with <br> for markdown line breaks
                    formatted_text = story.text.strip().replace('\\n', '<br>')
                    lines.append(f"{formatted_text}\n")
            lines.append("\n---")

        # --- Voice Lines ---
        if character.voice_lines:
            lines.append("\n## 语音台词\n")
            for voice in character.voice_lines:
                 if voice.title and voice.text:
                    lines.append(f"### {voice.title}")
                    # Replace \n with <br> for markdown line breaks
                    formatted_text = voice.text.strip().replace('\\n', '<br>')
                    lines.append(f"{formatted_text}\n")

        return "\n".join(lines)