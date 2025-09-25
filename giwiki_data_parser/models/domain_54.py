"""
原神Wiki 秘境数据模型

处理秘境相关的数据结构，包含秘境名称和简述信息。
"""

from typing import List, Dict, Any
from pydantic import Field
from ._core import BaseWikiModel, WikiMetadata


class DomainBrief(BaseWikiModel):
    """秘境简述模型"""

    name: str = Field(..., description="简述项目名称")
    description: str = Field(..., description="简述项目描述")


class DomainModel(BaseWikiModel):
    """秘境数据模型"""

    # 基础信息
    name: str = Field(..., description="秘境名称")
    brief: List[DomainBrief] = Field(default_factory=list, description="简述列表")

    def get_domain_name(self) -> str:
        """获取秘境名称"""
        return self.name.strip()

    def get_brief_count(self) -> int:
        """获取简述数量"""
        return len(self.brief)

    def has_brief_content(self) -> bool:
        """判断是否包含简述内容"""
        return len(self.brief) > 0

    def search_in_content(self, keyword: str) -> bool:
        """在秘境内容中搜索关键词"""
        search_text = self.name

        # 搜索简述内容
        for brief_item in self.brief:
            search_text += f" {brief_item.name} {brief_item.description}"

        return keyword.lower() in search_text.lower()


class DomainCollection(BaseWikiModel):
    """秘境集合模型"""

    domains: List[DomainModel] = Field(default_factory=list, description="秘境列表")
    metadata: WikiMetadata = Field(default_factory=WikiMetadata, description="元数据")

    def get_domains_with_brief(self) -> List[DomainModel]:
        """获取包含简述内容的秘境"""
        return [domain for domain in self.domains if domain.has_brief_content()]

    def search_by_keyword(self, keyword: str) -> List[DomainModel]:
        """按关键词搜索秘境"""
        results = []

        for domain in self.domains:
            if domain.search_in_content(keyword):
                results.append(domain)

        return results

    def get_total_count(self) -> int:
        """获取秘境总数"""
        return len(self.domains)