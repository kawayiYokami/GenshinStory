from hsrwiki_data_parser.models.character import Character

class CharacterFormatter:
    def format(self, item: Character) -> str:
        """Formats a Character object into a Markdown string."""
        if not isinstance(item, Character):
            return ""

        md = []
        md.append(f"# {item.name}")
        md.append("\n---\n")

        if item.metadata and item.metadata.city_state:
            md.append(f"**阵营:** {item.metadata.city_state}\n")

        if item.summary:
            md.append(f"## 简介")
            md.append(f"{item.summary}\n")

        if item.story:
            md.append(f"## 角色故事")
            for i, story_part in enumerate(item.story):
                md.append(f"### 故事 {i+1}")
                md.append(f"{story_part}\n")

        if item.voices:
            for lang, voice_lines in item.voices.items():
                if not voice_lines:
                    continue
                lang_name = lang.replace('_', ' ').title()
                md.append(f"## 语音 ({lang_name})")
                for line in voice_lines:
                    md.append(f"- **{line.title}:** {line.text}")
                md.append("")

        return '\n'.join(md)
