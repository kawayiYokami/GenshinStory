from giwiki_data_parser.models.character_25 import CharacterModel

class CharacterFormatter:
    """角色格式化器"""

    def format(self, item: CharacterModel) -> str:
        """将角色对象格式化为Markdown字符串"""
        if not isinstance(item, CharacterModel):
            return ""

        md_lines = []

        # 1. 标题
        md_lines.append(f"# {item.name}")
        md_lines.append("")

        # 2. 基本信息
        md_lines.append("## 基本信息")
        md_lines.append("")
        md_lines.append(f"- **星级**: {item.rarity}星")

        # 显示基础信息
        for key, value in item.basic_info.items():
            md_lines.append(f"- **{key}**: {value}")
        md_lines.append("")

        # 3. 命之座
        if item.constellations:
            md_lines.append("## 命之座")
            md_lines.append("")
            for i, constellation in enumerate(item.constellations, 1):
                md_lines.append(f"### {i}. {constellation.name}")
                md_lines.append("")
                md_lines.append(constellation.description)
                md_lines.append("")

        # 4. 角色故事
        if item.character_stories:
            md_lines.append("## 角色故事")
            md_lines.append("")
            for story in item.character_stories:
                md_lines.append(f"### {story.title}")
                md_lines.append("")
                md_lines.append(story.content)
                md_lines.append("")

        # 5. 特殊料理
        if item.special_dish:
            md_lines.append("## 特殊料理")
            md_lines.append("")
            md_lines.append(item.special_dish)
            md_lines.append("")

        # 6. 生日邮件
        if item.birthday_mails:
            md_lines.append("## 生日邮件")
            md_lines.append("")
            for i, mail in enumerate(item.birthday_mails, 1):
                if len(item.birthday_mails) > 1:
                    md_lines.append(f"### 生日邮件 {i}")
                    md_lines.append("")
                md_lines.append(mail)
                md_lines.append("")

        # 7. 配音演员
        if any([item.voice_actors.chinese, item.voice_actors.japanese,
                item.voice_actors.korean, item.voice_actors.english]):
            md_lines.append("## 配音演员")
            md_lines.append("")
            if item.voice_actors.chinese:
                md_lines.append(f"- **汉语**: {', '.join(item.voice_actors.chinese)}")
            if item.voice_actors.japanese:
                md_lines.append(f"- **日语**: {', '.join(item.voice_actors.japanese)}")
            if item.voice_actors.korean:
                md_lines.append(f"- **韩语**: {', '.join(item.voice_actors.korean)}")
            if item.voice_actors.english:
                md_lines.append(f"- **英语**: {', '.join(item.voice_actors.english)}")
            md_lines.append("")

        # 8. 角色语音
        if item.character_voices:
            md_lines.append("## 角色语音")
            md_lines.append("")
            for voice in item.character_voices:
                md_lines.append(f"### {voice.scene}")
                md_lines.append("")
                md_lines.append(f"> {voice.content}")
                md_lines.append("")

        # 9. 角色关联语音
        if item.associated_voices:
            md_lines.append("## 角色关联语音")
            md_lines.append("")
            for voice in item.associated_voices:
                md_lines.append(f"### 来自 {voice.character} 的评价")
                md_lines.append("")
                md_lines.append(f"> {voice.content}")
                md_lines.append("")

        return '\n'.join(md_lines)