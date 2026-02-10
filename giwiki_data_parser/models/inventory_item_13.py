"""
原神Wiki物品数据模型

处理背包物品相关的数据结构，专注于提取物品的故事背景和世界观内容。
"""

from typing import List, Optional, Union, Dict, Any
from pydantic import Field
from ._core import BaseWikiModel, WikiMetadata


class InventoryItemModel(BaseWikiModel):
    """物品数据模型"""
    
    title: str = Field(..., description="物品名称")
    description: str = Field(..., description="物品描述，可能包含故事内容")
    obtain_method: List[str] = Field(default_factory=list, description="获取方法")
    exchange_requirements: Union[List[str], List[Dict[str, Any]]] = Field(default_factory=list, description="兑换需求")
    usage: str = Field(default="", description="用途说明")
    
    def has_story_content(self) -> bool:
        """判断是否包含故事内容"""
        # 检查描述是否包含对话、引用或深度背景故事
        story_indicators = [
            "「", "」",  # 对话标记
            "愿", "听说",  # 故事性语言
            "公主", "异邦人", "神", "国度",  # 世界观关键词
            "老身", "女儿", "峰顶",  # 人物关系
            "白树", "冰雪", "黑龙"  # 世界元素
        ]
        
        return any(indicator in self.description for indicator in story_indicators)
    
    def extract_story_quotes(self) -> List[str]:
        """提取描述中的对话内容"""
        quotes = []
        lines = self.description.split('\n')
        
        for line in lines:
            line = line.strip()
            if '「' in line and '」' in line:
                quotes.append(line)
        
        return quotes
    
    def get_lore_content(self) -> str:
        """获取世界观相关内容"""
        if not self.has_story_content():
            return ""
        
        # 移除纯功能性描述，保留故事内容
        lines = self.description.split('\n')
        lore_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 跳过纯功能性描述
            if any(skip_word in line for skip_word in [
                "经验值", "升级", "活动内玩法", "道具", "捕捉"
            ]):
                continue
                
            lore_lines.append(line)
        
        return '\n'.join(lore_lines)


class InventoryItemCollection(BaseWikiModel):
    """物品集合模型"""
    
    items: List[InventoryItemModel] = Field(default_factory=list, description="物品列表")
    metadata: WikiMetadata = Field(default_factory=WikiMetadata, description="元数据")
    
    def get_story_items(self) -> List[InventoryItemModel]:
        """获取包含故事内容的物品"""
        return [item for item in self.items if item.has_story_content()]
    
    def get_lore_items(self) -> List[InventoryItemModel]:
        """获取世界观相关物品"""
        lore_keywords = [
            "匣", "宝盒", "手册", "日记", "信件", "卷轴",
            "神", "公主", "异邦人", "国度", "世界"
        ]
        
        return [
            item for item in self.items 
            if any(keyword in item.title or keyword in item.description 
                   for keyword in lore_keywords)
        ]
    
    def group_by_type(self) -> dict:
        """按物品类型分组"""
        groups = {
            "story_items": [],      # 故事物品
            "lore_items": [],       # 世界观物品  
            "quest_items": [],      # 任务物品
            "consumables": [],      # 消耗品
            "materials": [],        # 材料
            "other": []            # 其他
        }
        
        for item in self.items:
            if item.has_story_content():
                if any(keyword in item.title for keyword in ["匣", "手册", "日记"]):
                    groups["lore_items"].append(item)
                else:
                    groups["story_items"].append(item)
            elif "经验" in item.description or "升级" in item.description:
                groups["consumables"].append(item)
            elif "材料" in item.description or "素材" in item.description:
                groups["materials"].append(item)
            elif "任务" in item.usage or "活动" in item.usage:
                groups["quest_items"].append(item)
            else:
                groups["other"].append(item)
        
        return groups