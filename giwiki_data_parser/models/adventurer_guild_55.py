"""
原神Wiki冒险家协会数据模型

处理每日委托任务相关的数据结构，专注于提取剧情对话和故事内容。
"""

from typing import List, Optional, Dict, Any
from pydantic import Field
from ._core import BaseWikiModel, WikiMetadata


class DialogueEntry(BaseWikiModel):
    """对话条目模型"""
    speaker: str = Field(default="", description="说话者")
    text: str = Field(default="", description="对话内容")
    type: str = Field(default="", description="对话类型")
    choices: List[str] = Field(default_factory=list, description="选择项")
    reply: List[Dict[str, str]] = Field(default_factory=list, description="回复内容")


class DialogueTree(BaseWikiModel):
    """对话树模型"""
    dialogue_entries: List[DialogueEntry] = Field(default_factory=list, description="对话条目列表")


class RewardEntry(BaseWikiModel):
    """奖励条目模型"""
    adventure_rank: str = Field(default="", description="冒险等阶")
    primogems: str = Field(default="", description="原石")
    adventure_exp: str = Field(default="", description="冒险阅历")
    mora: str = Field(default="", description="摩拉")
    friendship_exp: str = Field(default="", description="好感经验")
    enhancement_ore: str = Field(default="", description="精锻用矿物")


class AdventurerGuildTaskModel(BaseWikiModel):
    """冒险家协会任务数据模型"""
    
    name: str = Field(..., description="任务名称")
    task_type: str = Field(default="", description="任务类型")
    trigger_condition: str = Field(default="", description="触发条件")
    map_images: List[str] = Field(default_factory=list, description="地图图片")
    dialogue_tree: List[DialogueEntry] = Field(default_factory=list, description="剧情对话")
    task_process: List[str] = Field(default_factory=list, description="任务过程")
    task_rewards: List[RewardEntry] = Field(default_factory=list, description="任务奖励")
    
    def has_story_content(self) -> bool:
        """判断是否包含故事内容"""
        # 检查是否有对话内容
        if not self.dialogue_tree:
            return False
        
        # 检查对话是否有实质内容
        meaningful_dialogues = 0
        for dialogue in self.dialogue_tree:
            if dialogue.text and len(dialogue.text.strip()) > 10:
                meaningful_dialogues += 1
        
        return meaningful_dialogues >= 3  # 至少3条有意义的对话
    
    def get_dialogue_count(self) -> int:
        """获取对话数量"""
        return len([d for d in self.dialogue_tree if d.text.strip()])
    
    def get_main_characters(self) -> List[str]:
        """获取主要角色列表"""
        characters = set()
        for dialogue in self.dialogue_tree:
            if dialogue.speaker and dialogue.speaker.strip():
                # 清理说话者名称
                speaker = dialogue.speaker.replace("：", "").replace(":", "").strip()
                if speaker and speaker not in ["旁白", "派蒙"]:
                    characters.add(speaker)
        
        return list(characters)
    
    def extract_story_summary(self) -> str:
        """提取故事摘要"""
        if not self.dialogue_tree:
            return ""
        
        # 从前几条对话中提取故事背景
        summary_parts = []
        for dialogue in self.dialogue_tree[:5]:
            if dialogue.text and len(dialogue.text.strip()) > 20:
                # 去除引号和多余符号
                text = dialogue.text.replace(""", "").replace(""", "").replace("「", "").replace("」", "")
                summary_parts.append(text[:100])  # 限制长度
        
        return "；".join(summary_parts)
    
    def get_task_theme(self) -> str:
        """获取任务主题"""
        name_lower = self.name.lower()
        dialogue_text = " ".join([d.text for d in self.dialogue_tree])
        
        # 根据任务名称和对话内容判断主题
        if any(keyword in name_lower for keyword in ["钓", "鱼"]):
            return "钓鱼"
        elif any(keyword in name_lower for keyword in ["小说", "书", "写"]):
            return "文学创作"
        elif any(keyword in dialogue_text for keyword in ["料理", "做菜", "食物"]):
            return "料理"
        elif any(keyword in dialogue_text for keyword in ["商人", "贸易", "生意"]):
            return "商业"
        elif any(keyword in dialogue_text for keyword in ["怪物", "魔物", "战斗"]):
            return "战斗"
        elif any(keyword in dialogue_text for keyword in ["寻找", "找", "丢失"]):
            return "寻物"
        else:
            return "日常生活"
    
    def is_character_focused(self) -> bool:
        """判断是否以角色为中心的故事"""
        main_chars = self.get_main_characters()
        return len(main_chars) >= 1 and self.get_dialogue_count() >= 5


class AdventurerGuildCollection(BaseWikiModel):
    """冒险家协会任务集合模型"""
    
    tasks: List[AdventurerGuildTaskModel] = Field(default_factory=list, description="任务列表")
    metadata: WikiMetadata = Field(default_factory=WikiMetadata, description="元数据")
    
    def get_story_tasks(self) -> List[AdventurerGuildTaskModel]:
        """获取包含故事内容的任务"""
        return [task for task in self.tasks if task.has_story_content()]
    
    def get_character_focused_tasks(self) -> List[AdventurerGuildTaskModel]:
        """获取以角色为中心的任务"""
        return [task for task in self.tasks if task.is_character_focused()]
    
    def group_by_theme(self) -> Dict[str, List[AdventurerGuildTaskModel]]:
        """按主题分组任务"""
        theme_groups = {}
        
        for task in self.tasks:
            theme = task.get_task_theme()
            if theme not in theme_groups:
                theme_groups[theme] = []
            theme_groups[theme].append(task)
        
        return theme_groups
    
    def group_by_type(self) -> Dict[str, List[AdventurerGuildTaskModel]]:
        """按任务类型分组"""
        type_groups = {}
        
        for task in self.tasks:
            task_type = task.task_type if task.task_type else "未知类型"
            if task_type not in type_groups:
                type_groups[task_type] = []
            type_groups[task_type].append(task)
        
        return type_groups
    
    def get_featured_characters(self) -> Dict[str, int]:
        """获取出现频率最高的角色"""
        character_count = {}
        
        for task in self.tasks:
            for character in task.get_main_characters():
                character_count[character] = character_count.get(character, 0) + 1
        
        # 按出现频率排序
        return dict(sorted(character_count.items(), key=lambda x: x[1], reverse=True))
    
    def search_by_character(self, character_name: str) -> List[AdventurerGuildTaskModel]:
        """按角色名搜索任务"""
        results = []
        
        for task in self.tasks:
            if character_name in task.get_main_characters():
                results.append(task)
        
        return results
    
    def get_dialogue_rich_tasks(self) -> List[AdventurerGuildTaskModel]:
        """获取对话丰富的任务（对话数>10）"""
        return [task for task in self.tasks if task.get_dialogue_count() > 10]
    
    def analyze_story_content(self) -> Dict[str, Any]:
        """分析故事内容"""
        story_tasks = self.get_story_tasks()
        character_tasks = self.get_character_focused_tasks()
        theme_groups = self.group_by_theme()
        featured_chars = self.get_featured_characters()
        
        return {
            "total_tasks": len(self.tasks),
            "story_tasks": len(story_tasks),
            "character_focused_tasks": len(character_tasks),
            "dialogue_rich_tasks": len(self.get_dialogue_rich_tasks()),
            "theme_distribution": {k: len(v) for k, v in theme_groups.items()},
            "featured_characters": dict(list(featured_chars.items())[:10]),
            "top_story_tasks": sorted(story_tasks, 
                                    key=lambda x: x.get_dialogue_count(), 
                                    reverse=True)[:10]
        }