"""
原神Wiki物品数据格式化器

将物品数据转换为Markdown格式，专注于展示故事和世界观内容。
"""

from typing import List
from ..models.inventory_item_13 import InventoryItemModel, InventoryItemCollection


class InventoryItemFormatter:
    """物品数据格式化器"""
    
    def format_single_item(self, item: InventoryItemModel, include_metadata: bool = True) -> str:
        """格式化单个物品"""
        lines = []
        
        # 标题
        lines.append(f"# {item.title}")
        lines.append("")
        
        # 描述内容
        if item.description:
            lines.append("## 物品描述")
            lines.append("")
            
            # 如果包含故事内容，特别处理
            if item.has_story_content():
                lore_content = item.get_lore_content()
                if lore_content:
                    # 分段处理描述
                    paragraphs = lore_content.split('\n')
                    for paragraph in paragraphs:
                        paragraph = paragraph.strip()
                        if not paragraph:
                            continue
                            
                        # 对话内容特殊格式化
                        if '「' in paragraph and '」' in paragraph:
                            lines.append(f"> {paragraph}")
                        else:
                            lines.append(paragraph)
                        lines.append("")
                else:
                    lines.append(item.description)
                    lines.append("")
            else:
                lines.append(item.description)
                lines.append("")
        
        # 故事引用
        quotes = item.extract_story_quotes()
        if quotes:
            lines.append("## 故事内容")
            lines.append("")
            for quote in quotes:
                lines.append(f"> {quote}")
                lines.append("")
        
        # 用途说明
        if item.usage and item.usage.strip():
            lines.append("## 用途")
            lines.append("")
            lines.append(item.usage)
            lines.append("")
        
        # 获取方法
        if item.obtain_method:
            lines.append("## 获取方法")
            lines.append("")
            for method in item.obtain_method:
                if method.strip():
                    lines.append(f"- {method}")
            lines.append("")
        
        # 兑换需求
        if item.exchange_requirements:
            lines.append("## 兑换需求")
            lines.append("")
            for requirement in item.exchange_requirements:
                if isinstance(requirement, dict):
                    # 字典格式: {"name": "物品名", "count": 数量}
                    name = requirement.get("name", "")
                    count = requirement.get("count", 0)
                    if name:
                        if count > 0:
                            lines.append(f"- {name} x{count}")
                        else:
                            lines.append(f"- {name}")
                elif isinstance(requirement, str) and requirement.strip():
                    # 字符串格式
                    lines.append(f"- {requirement}")
            lines.append("")
        
        return '\n'.join(lines).strip()
    
    def format_collection(self, collection: InventoryItemCollection, 
                         story_only: bool = True) -> str:
        """格式化物品集合"""
        lines = []
        
        # 标题
        lines.append("# 原神物品资料")
        lines.append("")
        
        # 统计信息
        total_items = len(collection.items)
        story_items = collection.get_story_items()
        lore_items = collection.get_lore_items()
        
        lines.append("## 数据概览")
        lines.append("")
        lines.append(f"- 总物品数量: {total_items}")
        lines.append(f"- 包含故事内容: {len(story_items)}")
        lines.append(f"- 世界观相关物品: {len(lore_items)}")
        lines.append("")
        
        # 选择要展示的物品
        items_to_show = story_items if story_only else collection.items
        
        if story_only and story_items:
            lines.append("## 故事物品")
            lines.append("")
            lines.append("以下物品包含丰富的故事背景和世界观设定：")
            lines.append("")
        
        # 按类型分组展示
        if items_to_show:
            groups = self._group_story_items(items_to_show)
            
            for group_name, group_items in groups.items():
                if not group_items:
                    continue
                    
                lines.append(f"### {group_name}")
                lines.append("")
                
                for item in group_items:
                    lines.append(f"#### {item.title}")
                    lines.append("")
                    
                    # 简化的描述
                    if item.has_story_content():
                        lore_content = item.get_lore_content()
                        if lore_content:
                            # 只显示前几行
                            preview_lines = lore_content.split('\n')[:3]
                            for line in preview_lines:
                                line = line.strip()
                                if line:
                                    if '「' in line and '」' in line:
                                        lines.append(f"> {line}")
                                    else:
                                        lines.append(line)
                            lines.append("")
                    
                    # 用途
                    if item.usage and item.usage.strip():
                        lines.append(f"**用途**: {item.usage}")
                        lines.append("")
                    
                    lines.append("---")
                    lines.append("")
        
        return '\n'.join(lines).strip()
    
    def format_story_items_only(self, collection: InventoryItemCollection) -> str:
        """仅格式化包含故事内容的物品"""
        story_items = collection.get_story_items()
        
        if not story_items:
            return "# 原神物品故事\n\n暂无包含故事内容的物品。"
        
        lines = []
        lines.append("# 原神物品故事")
        lines.append("")
        lines.append(f"共收录 {len(story_items)} 个包含故事内容的物品。")
        lines.append("")
        
        # 按故事丰富程度排序
        story_items.sort(key=lambda x: len(x.get_lore_content()), reverse=True)
        
        for item in story_items:
            lines.append(f"## {item.title}")
            lines.append("")
            
            lore_content = item.get_lore_content()
            if lore_content:
                paragraphs = lore_content.split('\n')
                for paragraph in paragraphs:
                    paragraph = paragraph.strip()
                    if not paragraph:
                        continue
                        
                    if '「' in paragraph and '」' in paragraph:
                        lines.append(f"> {paragraph}")
                    else:
                        lines.append(paragraph)
                    lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return '\n'.join(lines).strip()
    
    def _group_story_items(self, items: List[InventoryItemModel]) -> dict:
        """将故事物品分组"""
        groups = {
            "神秘宝盒": [],
            "文献资料": [],
            "特殊道具": [],
            "其他故事物品": []
        }
        
        for item in items:
            if "匣" in item.title:
                groups["神秘宝盒"].append(item)
            elif any(keyword in item.title for keyword in ["手册", "日记", "信件", "卷轴"]):
                groups["文献资料"].append(item)
            elif any(keyword in item.description for keyword in ["神", "公主", "异邦人", "国度"]):
                groups["特殊道具"].append(item)
            else:
                groups["其他故事物品"].append(item)
        
        # 移除空组
        return {k: v for k, v in groups.items() if v}
    
    def format_item_index(self, collection: InventoryItemCollection) -> str:
        """生成物品索引"""
        lines = []
        lines.append("# 原神物品索引")
        lines.append("")
        
        story_items = collection.get_story_items()
        if story_items:
            lines.append("## 故事物品")
            lines.append("")
            
            groups = self._group_story_items(story_items)
            for group_name, group_items in groups.items():
                if group_items:
                    lines.append(f"### {group_name}")
                    lines.append("")
                    for item in sorted(group_items, key=lambda x: x.title):
                        lines.append(f"- [{item.title}](#{item.title.replace(' ', '-').lower()})")
                    lines.append("")
        
        return '\n'.join(lines).strip()
    
    def format(self, item: InventoryItemModel) -> str:
        """标准格式化方法，用于与主解析器兼容"""
        return self.format_single_item(item)