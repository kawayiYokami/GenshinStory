"""
原神Wiki 装扮数据模型

处理装扮相关的数据结构，专注于提取装扮名称、简介和故事内容。
"""

from typing import List, Optional, Dict, Any
from pydantic import Field
from ._core import BaseWikiModel, WikiMetadata


class OutfitModel(BaseWikiModel):
    """装扮数据模型"""

    # 基础信息
    name: str = Field(..., description="装扮名称")
    introduction: str = Field(default="", description="装扮简介")
    story: str = Field(default="", description="装扮故事")

    def get_outfit_name(self) -> str:
        """获取装扮名称"""
        return self.name.strip()

    def has_story_content(self) -> bool:
        """判断是否包含故事内容"""
        # 装扮数据通常包含故事内容，简介可能为空
        return bool(self.story.strip()) or bool(self.introduction.strip())

    def get_content_length(self) -> int:
        """获取内容总长度"""
        return len(self.introduction) + len(self.story)

    def has_introduction(self) -> bool:
        """是否有简介"""
        return bool(self.introduction.strip())

    def has_story(self) -> bool:
        """是否有故事"""
        return bool(self.story.strip())

    def search_in_content(self, keyword: str) -> bool:
        """在装扮内容中搜索关键词"""
        search_text = f"{self.name} {self.introduction} {self.story}"
        return keyword.lower() in search_text.lower()

    def get_summary(self) -> str:
        """获取装扮摘要"""
        if self.introduction:
            return self.introduction[:100] + "..." if len(self.introduction) > 100 else self.introduction
        elif self.story:
            return self.story[:100] + "..." if len(self.story) > 100 else self.story
        else:
            return self.name


class OutfitCollection(BaseWikiModel):
    """装扮集合模型"""

    outfits: List[OutfitModel] = Field(default_factory=list, description="装扮列表")
    metadata: WikiMetadata = Field(default_factory=WikiMetadata, description="元数据")

    def get_story_outfits(self) -> List[OutfitModel]:
        """获取包含故事内容的装扮"""
        return [outfit for outfit in self.outfits if outfit.has_story_content()]

    def get_outfits_with_introduction(self) -> List[OutfitModel]:
        """获取有简介的装扮"""
        return [outfit for outfit in self.outfits if outfit.has_introduction()]

    def get_outfits_with_story(self) -> List[OutfitModel]:
        """获取有故事的装扮"""
        return [outfit for outfit in self.outfits if outfit.has_story()]

    def search_by_keyword(self, keyword: str) -> List[OutfitModel]:
        """按关键词搜索装扮"""
        results = []
        for outfit in self.outfits:
            if outfit.search_in_content(keyword):
                results.append(outfit)
        return results

    def get_content_statistics(self) -> Dict[str, int]:
        """获取内容统计"""
        return {
            "total_outfits": len(self.outfits),
            "outfits_with_introduction": len(self.get_outfits_with_introduction()),
            "outfits_with_story": len(self.get_outfits_with_story()),
            "outfits_with_content": len(self.get_story_outfits())
        }