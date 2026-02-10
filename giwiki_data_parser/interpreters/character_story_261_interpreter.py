import logging
import os
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.character_story_261 import (
    CharacterStory, DialogueSection, DialogueBranch,
    DialogueContent, GiftDialogue
)
from giwiki_data_parser.services.dataloader import DataLoader

class CharacterStoryInterpreter:
    """角色逸闻解释器"""
    
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)
    
    def interpret(self, data: Dict[str, Any]) -> Optional[CharacterStory]:
        """解析单个角色逸闻数据 - 公共接口"""
        return self._interpret_single(data)
    
    def interpret_all(self) -> List[CharacterStory]:
        """解析所有角色逸闻数据"""
        character_stories = []
        raw_data_iterator = self.loader.get_character_stories()
        
        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                story = self._interpret_single(data, file_path)
                if story:
                    character_stories.append(story)
            except Exception as e:
                self.logger.error(f"解析角色逸闻数据时出错: {e}")
        
        self.logger.info(f"成功解析 {len(character_stories)} 个角色逸闻")
        return character_stories
    
    def _interpret_single(self, data: Dict[str, Any], file_path: str = "") -> Optional[CharacterStory]:
        """解析单个角色逸闻数据"""
        try:
            # 提取基本信息
            basic_info = data.get("基本信息", {})
            
            # 解析角色洞天对话
            teapot_dialogues = self._parse_teapot_dialogues(data.get("角色洞天", []))
            
            # 解析角色赠礼对话
            gift_dialogues = self._parse_gift_dialogues(data.get("角色赠礼", []))
            
            # 创建角色逸闻对象
            title = data.get("标题", "")  # 提取顶级标题，如"瑶瑶【逸闻】"
            character_story = CharacterStory(
                name=basic_info.get("角色名称", ""),
                title=title,  # 使用顶级标题作为标题
                character_name=basic_info.get("角色名称", ""),
                story_type=data.get("类型"),
                birthday=basic_info.get("生日"),
                affiliation=basic_info.get("所属"),
                character_intro=basic_info.get("角色介绍"),
                teapot_dialogues=teapot_dialogues,
                gift_dialogues=gift_dialogues,
                anecdotes=data.get("逸闻纪事", []),
                easter_eggs=data.get("剧情彩蛋", []),
                birthday_mails=data.get("生日邮件", [])
            )
            
            # 从文件路径设置ID
            if file_path:
                character_story.set_id_from_filename(file_path)
            elif "_file_path" in data:
                character_story.set_id_from_filename(data["_file_path"])
            elif "_file_id" in data:
                file_id = str(data["_file_id"])
                if file_id.isdigit():
                    character_story.id = file_id
                else:
                    self.logger.warning(f"非数字文件ID，跳过: {file_id}")
                    return None
            
            return character_story
            
        except Exception as e:
            self.logger.error(f"解析单个角色逸闻数据时出错: {e}")
            return None
    
    def _parse_teapot_dialogues(self, teapot_data: List[Dict[str, Any]]) -> List[DialogueSection]:
        """解析角色洞天对话"""
        sections = []
        
        for section_data in teapot_data:
            try:
                dialogues = []
                for dialogue_data in section_data.get("对话", []):
                    dialogue_branch = self._parse_dialogue_branch(dialogue_data)
                    if dialogue_branch:
                        dialogues.append(dialogue_branch)
                
                section = DialogueSection(
                    title=section_data.get("标题", ""),
                    summary=section_data.get("简介"),
                    dialogues=dialogues
                )
                sections.append(section)
                
            except Exception as e:
                self.logger.error(f"解析洞天对话章节时出错: {e}")
        
        return sections
    
    def _parse_dialogue_branch(self, branch_data: Dict[str, Any]) -> Optional[DialogueBranch]:
        """解析对话分支"""
        try:
            # 解析对话内容
            dialogue_content = []
            for content_data in branch_data.get("对话内容", []):
                if isinstance(content_data, dict) and "角色" in content_data and "内容" in content_data:
                    dialogue_content.append(DialogueContent(
                        character=content_data["角色"],
                        content=content_data["内容"]
                    ))
            
            # 递归解析子分支
            sub_branches = []
            for sub_branch_data in branch_data.get("子分支", []):
                if isinstance(sub_branch_data, dict) and "选项" in sub_branch_data:
                    sub_branch = self._parse_dialogue_branch(sub_branch_data)
                    if sub_branch:
                        sub_branches.append(sub_branch)
                elif isinstance(sub_branch_data, dict) and "角色" in sub_branch_data:
                    # 处理直接的对话内容
                    dialogue_content.append(DialogueContent(
                        character=sub_branch_data["角色"],
                        content=sub_branch_data["内容"]
                    ))
            
            return DialogueBranch(
                option=branch_data.get("选项", ""),
                dialogue_content=dialogue_content,
                sub_branches=sub_branches
            )
            
        except Exception as e:
            self.logger.error(f"解析对话分支时出错: {e}")
            return None
    
    def _parse_gift_dialogues(self, gift_data: List[Dict[str, Any]]) -> List[GiftDialogue]:
        """解析角色赠礼对话"""
        gift_dialogues = []
        
        for gift_item in gift_data:
            try:
                dialogue_content = []
                for dialogue_item in gift_item.get("对话", []):
                    if isinstance(dialogue_item, dict) and "角色" in dialogue_item and "内容" in dialogue_item:
                        dialogue_content.append(DialogueContent(
                            character=dialogue_item["角色"],
                            content=dialogue_item["内容"]
                        ))
                
                gift_dialogue = GiftDialogue(
                    title=gift_item.get("标题", ""),
                    summary=gift_item.get("简介"),
                    dialogue_content=dialogue_content
                )
                gift_dialogues.append(gift_dialogue)
                
            except Exception as e:
                self.logger.error(f"解析赠礼对话时出错: {e}")
        
        return gift_dialogues