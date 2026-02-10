from giwiki_data_parser.models.character_story_261 import (
    CharacterStory, DialogueSection, DialogueBranch,
    DialogueContent, GiftDialogue
)

class CharacterStoryFormatter:
    """角色逸闻格式化器"""
    
    def format(self, item: CharacterStory) -> str:
        """将角色逸闻对象格式化为Markdown字符串"""
        if not isinstance(item, CharacterStory):
            return ""
        
        md = []
        
        # 标题
        md.append(f"# {item.character_name}【逸闻】")
        md.append("")
        
        # 基本信息
        if item.birthday:
            md.append(f"**生日**: {item.birthday}")
        
        if item.affiliation:
            md.append(f"**所属**: {item.affiliation}")
        
        if item.character_intro:
            md.append(f"**角色介绍**: {item.character_intro}")
        
        if item.birthday or item.affiliation or item.character_intro:
            md.append("")
        
        # 角色洞天对话
        if item.teapot_dialogues:
            md.append("## 角色洞天对话")
            md.append("")
            
            for section in item.teapot_dialogues:
                md.extend(self._format_dialogue_section(section))
        
        # 角色赠礼对话
        if item.gift_dialogues:
            md.append("## 角色赠礼对话")
            md.append("")
            
            for gift in item.gift_dialogues:
                md.extend(self._format_gift_dialogue(gift))
        
        # 逸闻纪事
        if item.anecdotes:
            md.append("## 逸闻纪事")
            md.append("")
            for anecdote in item.anecdotes:
                md.append(f"- {anecdote}")
            md.append("")
        
        # 剧情彩蛋
        if item.easter_eggs:
            md.append("## 剧情彩蛋")
            md.append("")
            for easter_egg in item.easter_eggs:
                md.append(f"- {easter_egg}")
            md.append("")
        
        return '\n'.join(md)
    
    def _format_dialogue_section(self, section: DialogueSection) -> list:
        """格式化对话章节"""
        md = []
        
        if section.title:
            md.append(f"### {section.title}")
            md.append("")
        
        if section.summary:
            md.append(f"**简介：** {section.summary}")
            md.append("")
        
        for dialogue in section.dialogues:
            md.extend(self._format_dialogue_branch(dialogue, level=4))
        
        return md
    
    def _format_dialogue_branch(self, branch: DialogueBranch, level: int = 4) -> list:
        """格式化对话分支"""
        md = []
        
        # 选项标题
        if branch.option:
            header = "#" * level
            md.append(f"{header} {branch.option}")
            md.append("")
        
        # 对话内容
        if branch.dialogue_content:
            for content in branch.dialogue_content:
                md.append(f"**{content.character}：** {content.content}")
                md.append("")
        
        # 子分支
        if branch.sub_branches:
            for sub_branch in branch.sub_branches:
                md.extend(self._format_dialogue_branch(sub_branch, level + 1))
        
        return md
    
    def _format_gift_dialogue(self, gift: GiftDialogue) -> list:
        """格式化赠礼对话"""
        md = []
        
        if gift.title:
            md.append(f"### {gift.title}")
            md.append("")
        
        if gift.summary:
            md.append(f"**简介：** {gift.summary}")
            md.append("")
        
        if gift.dialogue_content:
            for content in gift.dialogue_content:
                # 处理多行内容
                content_lines = content.content.split('\n')
                if len(content_lines) > 1:
                    md.append(f"**{content.character}：**")
                    md.append("")
                    for line in content_lines:
                        if line.strip():
                            md.append(f"> {line.strip()}")
                    md.append("")
                else:
                    md.append(f"**{content.character}：** {content.content}")
                    md.append("")
        
        return md