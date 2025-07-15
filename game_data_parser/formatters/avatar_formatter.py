from ..models import Avatar

class AvatarFormatter:
    """
    负责将角色相关的模型格式化为用户友好的字符串，如Markdown。
    """
    def format_avatar(self, avatar: Avatar) -> str:
        """
        将单个 Avatar 对象格式化为 Markdown。
        """
        md = []
        md.append(f"# {avatar.name}")
        md.append(f"> *ID: {avatar.id} | 称号: {avatar.title}*")
        
        details = []
        if avatar.nation: details.append(f"**国家**: {avatar.nation}")
        if avatar.vision: details.append(f"**神之眼**: {avatar.vision}")
        if avatar.constellation: details.append(f"**命之座**: {avatar.constellation}")
        if avatar.birthday: details.append(f"**生日**: {avatar.birthday}")
        md.append(" | ".join(details))
        
        md.append("\n" + "="*20)
        
        md.append(f"\n**描述**\n\n{avatar.description}")
        
        if avatar.cvs:
            md.append("\n**声优**")
            if avatar.cvs.chinese: md.append(f"- **中**: {avatar.cvs.chinese}")
            if avatar.cvs.japanese: md.append(f"- **日**: {avatar.cvs.japanese}")
            if avatar.cvs.english: md.append(f"- **英**: {avatar.cvs.english}")
            if avatar.cvs.korean: md.append(f"- **韩**: {avatar.cvs.korean}")

        if avatar.stories:
            md.append("\n\n**故事**\n")
            for story in avatar.stories:
                md.append(f"### {story.title}\n{story.text}\n")

        if avatar.voice_lines:
            md.append("\n\n**语音**\n")
            for line in avatar.voice_lines:
                md.append(f"- **{line.title}**: {line.text}")

        return "\n".join(md)