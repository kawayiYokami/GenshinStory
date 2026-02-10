"""
原神Wiki动物数据格式化器

将动物数据转换为Markdown格式，专注于展示背景故事和世界观内容。
"""

from typing import List, Dict
from ..models.animal_49 import AnimalModel, AnimalCollection


class AnimalFormatter:
    """动物数据格式化器"""
    
    def format_single_animal(self, animal: AnimalModel, include_metadata: bool = True) -> str:
        """格式化单个动物"""
        lines = []
        
        # 标题
        lines.append(f"# {animal.name}")
        lines.append("")
        
        # 基本信息
        if include_metadata:
            lines.append("## 基本信息")
            lines.append("")
            
            animal_type = animal.get_animal_type()
            lines.append(f"**类型**: {animal_type}")
            
            if animal.is_magical_creature():
                lines.append(f"**特性**: 魔法生物")
            
            if animal.drop_items:
                drop_names = [item.name for item in animal.drop_items]
                lines.append(f"**掉落物品**: {', '.join(drop_names)}")
            
            lines.append("")
        
        # 背景故事
        if animal.background_story:
            lines.append("## 背景故事")
            lines.append("")
            
            # 分段处理长故事
            story_paragraphs = animal.background_story.split('\n')
            for paragraph in story_paragraphs:
                paragraph = paragraph.strip()
                if paragraph:
                    lines.append(paragraph)
                    lines.append("")
        
        # 世界观关键词
        if animal.has_story_content():
            keywords = animal.extract_lore_keywords()
            if keywords:
                lines.append("## 世界观要素")
                lines.append("")
                
                # 按类别分组关键词
                keyword_groups = {}
                for keyword in keywords:
                    if ':' in keyword:
                        category, term = keyword.split(':', 1)
                        if category not in keyword_groups:
                            keyword_groups[category] = []
                        keyword_groups[category].append(term)
                
                for category, terms in keyword_groups.items():
                    lines.append(f"**{category}**: {', '.join(terms)}")
                
                lines.append("")
        
        # 攻略方法
        if animal.attack_method and animal.attack_method.strip():
            lines.append("## 攻略方法")
            lines.append("")
            lines.append(animal.attack_method)
            lines.append("")
        
        # 备注
        if animal.notes and animal.notes.strip():
            lines.append("## 备注")
            lines.append("")
            lines.append(animal.notes)
            lines.append("")
        
        return '\n'.join(lines).strip()
    
    def format_collection(self, collection: AnimalCollection, 
                         story_only: bool = True) -> str:
        """格式化动物集合"""
        lines = []
        
        # 标题
        lines.append("# 原神动物图鉴")
        lines.append("")
        
        # 统计信息
        total_animals = len(collection.animals)
        story_animals = collection.get_story_animals()
        magical_creatures = collection.get_magical_creatures()
        
        lines.append("## 数据概览")
        lines.append("")
        lines.append(f"- 总动物数量: {total_animals}")
        lines.append(f"- 包含故事内容: {len(story_animals)}")
        lines.append(f"- 魔法生物: {len(magical_creatures)}")
        lines.append("")
        
        # 选择要展示的动物
        animals_to_show = story_animals if story_only else collection.animals
        
        if story_only and story_animals:
            lines.append("## 故事动物")
            lines.append("")
            lines.append("以下动物包含丰富的背景故事和世界观设定：")
            lines.append("")
        
        # 按类型分组展示
        if animals_to_show:
            type_groups = {}
            for animal in animals_to_show:
                animal_type = animal.get_animal_type()
                if animal_type not in type_groups:
                    type_groups[animal_type] = []
                type_groups[animal_type].append(animal)
            
            for type_name, type_animals in type_groups.items():
                if not type_animals:
                    continue
                
                lines.append(f"### {type_name}")
                lines.append("")
                
                # 按故事长度排序
                type_animals.sort(key=lambda x: x.get_story_length(), reverse=True)
                
                for animal in type_animals:
                    lines.append(f"#### {animal.name}")
                    lines.append("")
                    
                    if animal.is_magical_creature():
                        lines.append("*魔法生物*")
                        lines.append("")
                    
                    # 背景故事预览
                    if animal.background_story:
                        # 显示前200字符作为预览
                        preview = animal.background_story[:200]
                        if len(animal.background_story) > 200:
                            preview += "..."
                        
                        lines.append(preview)
                        lines.append("")
                        
                        if len(animal.background_story) > 200:
                            lines.append(f"*（完整故事共{len(animal.background_story)}字符）*")
                            lines.append("")
                    
                    # 掉落物品
                    if animal.drop_items:
                        drop_names = [item.name for item in animal.drop_items]
                        lines.append(f"**掉落**: {', '.join(drop_names)}")
                        lines.append("")
                    
                    lines.append("---")
                    lines.append("")
        
        return '\n'.join(lines).strip()
    
    def format_story_animals_only(self, collection: AnimalCollection) -> str:
        """仅格式化包含故事内容的动物"""
        story_animals = collection.get_story_animals()
        
        if not story_animals:
            return "# 原神动物故事\n\n暂无包含故事内容的动物。"
        
        lines = []
        lines.append("# 原神动物故事")
        lines.append("")
        lines.append(f"共收录 {len(story_animals)} 个包含故事内容的动物。")
        lines.append("")
        
        # 按故事丰富程度排序
        story_animals.sort(key=lambda x: x.get_story_length(), reverse=True)
        
        for animal in story_animals:
            lines.append(f"## {animal.name}")
            lines.append("")
            
            # 基本信息
            animal_type = animal.get_animal_type()
            lines.append(f"**类型**: {animal_type}")
            
            if animal.is_magical_creature():
                lines.append(f"**特性**: 魔法生物")
            
            lines.append("")
            
            # 完整背景故事
            if animal.background_story:
                story_paragraphs = animal.background_story.split('\n')
                for paragraph in story_paragraphs:
                    paragraph = paragraph.strip()
                    if paragraph:
                        lines.append(paragraph)
                        lines.append("")
            
            # 世界观关键词
            keywords = animal.extract_lore_keywords()
            if keywords:
                lines.append("**世界观要素**:")
                keyword_groups = {}
                for keyword in keywords:
                    if ':' in keyword:
                        category, term = keyword.split(':', 1)
                        if category not in keyword_groups:
                            keyword_groups[category] = []
                        keyword_groups[category].append(term)
                
                for category, terms in keyword_groups.items():
                    lines.append(f"- {category}: {', '.join(terms)}")
                
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return '\n'.join(lines).strip()
    
    def format_magical_creatures(self, collection: AnimalCollection) -> str:
        """格式化魔法生物"""
        magical_creatures = collection.get_magical_creatures()
        
        if not magical_creatures:
            return "# 原神魔法生物\n\n暂无魔法生物。"
        
        lines = []
        lines.append("# 原神魔法生物")
        lines.append("")
        lines.append(f"共收录 {len(magical_creatures)} 个魔法生物。")
        lines.append("")
        
        # 按故事长度排序
        magical_creatures.sort(key=lambda x: x.get_story_length(), reverse=True)
        
        for creature in magical_creatures:
            lines.append(f"## {creature.name}")
            lines.append("")
            
            if creature.background_story:
                story_paragraphs = creature.background_story.split('\n')
                for paragraph in story_paragraphs:
                    paragraph = paragraph.strip()
                    if paragraph:
                        lines.append(paragraph)
                        lines.append("")
            
            # 特殊能力和特征
            keywords = creature.extract_lore_keywords()
            ability_keywords = [kw for kw in keywords if '能力:' in kw]
            if ability_keywords:
                lines.append("**特殊能力**:")
                for keyword in ability_keywords:
                    ability = keyword.split(':', 1)[1]
                    lines.append(f"- {ability}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return '\n'.join(lines).strip()
    
    def format_animal_index(self, collection: AnimalCollection) -> str:
        """生成动物索引"""
        lines = []
        lines.append("# 原神动物索引")
        lines.append("")
        
        # 按类型分组
        type_groups = collection.group_by_type()
        
        lines.append("## 按类型分类")
        lines.append("")
        
        for type_name, type_animals in sorted(type_groups.items()):
            lines.append(f"### {type_name}")
            lines.append("")
            
            # 分为有故事和无故事
            story_animals = [a for a in type_animals if a.has_story_content()]
            other_animals = [a for a in type_animals if not a.has_story_content()]
            
            if story_animals:
                lines.append("**有背景故事**:")
                for animal in sorted(story_animals, key=lambda x: x.name):
                    story_length = animal.get_story_length()
                    magical_mark = " 🔮" if animal.is_magical_creature() else ""
                    lines.append(f"- [{animal.name}](#{animal.name.replace(' ', '-').lower()}) ({story_length}字){magical_mark}")
                lines.append("")
            
            if other_animals:
                lines.append("**其他**:")
                for animal in sorted(other_animals, key=lambda x: x.name):
                    lines.append(f"- {animal.name}")
                lines.append("")
        
        return '\n'.join(lines).strip()
    
    def format_lore_analysis(self, collection: AnimalCollection) -> str:
        """格式化世界观分析"""
        analysis = collection.analyze_lore_content()
        
        lines = []
        lines.append("# 原神动物世界观分析")
        lines.append("")
        
        lines.append("## 统计概览")
        lines.append("")
        lines.append(f"- 包含故事的动物: {analysis['total_story_animals']}")
        lines.append(f"- 魔法生物: {analysis['magical_creatures']}")
        lines.append(f"- 世界观丰富的动物: {analysis['lore_rich_animals']}")
        lines.append("")
        
        lines.append("## 关键词频率")
        lines.append("")
        for keyword, count in list(analysis['keyword_frequency'].items())[:15]:
            lines.append(f"- {keyword}: {count}次")
        lines.append("")
        
        lines.append("## 故事最丰富的动物")
        lines.append("")
        for animal in analysis['top_story_animals'][:10]:
            story_length = animal.get_story_length()
            magical_mark = " (魔法生物)" if animal.is_magical_creature() else ""
            lines.append(f"- **{animal.name}**: {story_length}字{magical_mark}")
        lines.append("")
        
        return '\n'.join(lines).strip()
    
    def format(self, animal: AnimalModel) -> str:
        """标准格式化方法，用于与主解析器兼容"""
        return self.format_single_animal(animal)