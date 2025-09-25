"""
原神Wiki动物数据模型

处理动物相关的数据结构，专注于提取背景故事和世界观内容。
"""

from typing import List, Optional, Dict, Any
from pydantic import Field
from ._core import BaseWikiModel, WikiMetadata


class DropItem(BaseWikiModel):
    """掉落物品模型"""
    name: str = Field(..., description="物品名称")
    link: str = Field(default="", description="物品链接")


class AnimalModel(BaseWikiModel):
    """动物数据模型"""
    
    name: str = Field(..., description="动物名称")
    attack_method: str = Field(default="", description="攻略方法")
    drop_items: List[DropItem] = Field(default_factory=list, description="掉落物品")
    background_story: str = Field(default="", description="背景故事")
    notes: str = Field(default="", description="备注")
    images: List[str] = Field(default_factory=list, description="图片链接")
    
    def has_story_content(self) -> bool:
        """判断是否包含故事内容"""
        if not self.background_story:
            return False
        
        # 检查背景故事是否包含世界观内容
        story_indicators = [
            "传说", "据说", "古老", "神秘", "法术", "能力",
            "妖", "狸", "狐", "封印", "战争", "纠葛",
            "提瓦特", "大陆", "各地", "水域", "森林",
            "幕府", "组织", "首领", "石像"
        ]
        
        return any(indicator in self.background_story for indicator in story_indicators)
    
    def get_story_length(self) -> int:
        """获取故事内容长度"""
        return len(self.background_story) if self.background_story else 0
    
    def extract_lore_keywords(self) -> List[str]:
        """提取世界观关键词"""
        if not self.background_story:
            return []
        
        lore_keywords = []
        keyword_patterns = {
            "地理": ["提瓦特", "大陆", "水域", "森林", "镇守之森"],
            "组织": ["幕府", "组织", "神秘组织"],
            "生物": ["妖狸", "妖狐", "盗宝鼬", "鲈鱼"],
            "事件": ["狸合战", "封印", "纠葛", "战争"],
            "人物": ["五百藏", "首领", "渔夫", "旅客"],
            "能力": ["法术", "变化", "神出鬼没", "盗窃"]
        }
        
        for category, keywords in keyword_patterns.items():
            for keyword in keywords:
                if keyword in self.background_story:
                    lore_keywords.append(f"{category}:{keyword}")
        
        return lore_keywords
    
    def get_animal_type(self) -> str:
        """获取动物类型"""
        name_lower = self.name.lower()
        
        if any(fish_word in name_lower for fish_word in ["鱼", "鲈", "鳗", "鲑"]):
            return "鱼类"
        elif any(mammal_word in name_lower for mammal_word in ["鼬", "狸", "狐", "猫", "狗"]):
            return "哺乳动物"
        elif any(bird_word in name_lower for bird_word in ["鸟", "鸽", "鸦", "鹰"]):
            return "鸟类"
        elif any(insect_word in name_lower for insect_word in ["蝶", "萤", "蜂"]):
            return "昆虫"
        elif any(magical_word in name_lower for magical_word in ["妖", "灵", "仙"]):
            return "魔法生物"
        else:
            return "其他"
    
    def is_magical_creature(self) -> bool:
        """判断是否为魔法生物"""
        magical_indicators = [
            "妖", "灵", "仙", "神", "法术", "变化", "封印",
            "神出鬼没", "异想天开", "神秘"
        ]
        
        text_to_check = f"{self.name} {self.background_story}"
        return any(indicator in text_to_check for indicator in magical_indicators)


class AnimalCollection(BaseWikiModel):
    """动物集合模型"""
    
    animals: List[AnimalModel] = Field(default_factory=list, description="动物列表")
    metadata: WikiMetadata = Field(default_factory=WikiMetadata, description="元数据")
    
    def get_story_animals(self) -> List[AnimalModel]:
        """获取包含故事内容的动物"""
        return [animal for animal in self.animals if animal.has_story_content()]
    
    def get_magical_creatures(self) -> List[AnimalModel]:
        """获取魔法生物"""
        return [animal for animal in self.animals if animal.is_magical_creature()]
    
    def group_by_type(self) -> Dict[str, List[AnimalModel]]:
        """按动物类型分组"""
        type_groups = {}
        
        for animal in self.animals:
            animal_type = animal.get_animal_type()
            if animal_type not in type_groups:
                type_groups[animal_type] = []
            type_groups[animal_type].append(animal)
        
        return type_groups
    
    def get_lore_rich_animals(self) -> List[AnimalModel]:
        """获取世界观丰富的动物（故事长度>100字符）"""
        return [
            animal for animal in self.animals 
            if animal.get_story_length() > 100
        ]
    
    def search_by_keyword(self, keyword: str) -> List[AnimalModel]:
        """按关键词搜索动物"""
        results = []
        
        for animal in self.animals:
            search_text = f"{animal.name} {animal.background_story} {animal.notes}"
            if keyword.lower() in search_text.lower():
                results.append(animal)
        
        return results
    
    def get_animals_with_drops(self) -> List[AnimalModel]:
        """获取有掉落物品的动物"""
        return [animal for animal in self.animals if animal.drop_items]
    
    def analyze_lore_content(self) -> Dict[str, Any]:
        """分析世界观内容"""
        all_keywords = []
        story_animals = self.get_story_animals()
        
        for animal in story_animals:
            all_keywords.extend(animal.extract_lore_keywords())
        
        # 统计关键词频率
        keyword_count = {}
        for keyword in all_keywords:
            keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
        
        return {
            "total_story_animals": len(story_animals),
            "magical_creatures": len(self.get_magical_creatures()),
            "lore_rich_animals": len(self.get_lore_rich_animals()),
            "keyword_frequency": dict(sorted(keyword_count.items(), 
                                           key=lambda x: x[1], reverse=True)[:20]),
            "top_story_animals": sorted(story_animals, 
                                      key=lambda x: x.get_story_length(), 
                                      reverse=True)[:10]
        }