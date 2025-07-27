from hsr_data_parser.models import Character

class CharacterFormatter:
    """
    负责将 Character 对象格式化为 Markdown 文本。
    """
    def format(self, character: Character) -> str:
        """
        将 Character 对象转换为格式化的 Markdown 字符串。
        """
        if not character:
            return ""

        lines = [f"# {character.name} (ID: {character.id})"]
        
        if character.stories:
            lines.append("\n## 角色故事")
            for i, story in enumerate(character.stories):
                lines.append(f"\n### 故事 {i+1}")
                md_story = story.text.replace('\\n', '  \n')
                lines.append(md_story)

        if character.voice_lines:
            lines.append("\n## 语音")
            for voice in character.voice_lines:
                lines.append(f"\n### {voice.title}")
                md_voice = voice.text.replace('\\n', '  \n')
                lines.append(md_voice)
        
        return "\n".join(lines)
