from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import logging
from pathlib import Path
from glob import glob


class GlobalTagManager:
    """全局标签管理器 - 一次性加载所有link文件中的标签数据"""

    _instance = None
    _tags_data: Dict[str, Dict[str, str]] = {}
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, link_dir: str = "gi_wiki_scraper/output/link") -> None:
        """初始化全局标签数据"""
        if cls._initialized:
            return

        logger = logging.getLogger(__name__)
        link_path = Path(link_dir)

        if not link_path.exists():
            logger.warning(f"链接目录不存在: {link_path}")
            cls._initialized = True
            return

        # 查找所有link文件
        link_files = list(link_path.glob("*.json"))

        for link_file in link_files:
            try:
                with open(link_file, 'r', encoding='utf-8') as f:
                    link_data = json.load(f)

                # 处理每个项目的标签
                for item in link_data:
                    item_id = item.get('id')
                    tags = item.get('tags', {})

                    if item_id and tags:
                        cls._tags_data[str(item_id)] = tags

                logger.info(f"已加载标签文件: {link_file.name}")

            except Exception as e:
                logger.error(f"加载标签文件 {link_file} 失败: {e}")

        logger.info(f"全局标签管理器初始化完成，共加载 {len(cls._tags_data)} 个项目的标签")
        cls._initialized = True

    @classmethod
    def get_tags(cls, item_id: str) -> Optional[Dict[str, str]]:
        """根据ID获取标签"""
        if not cls._initialized:
            cls.initialize()
        return cls._tags_data.get(str(item_id))

    @classmethod
    def has_tags(cls, item_id: str) -> bool:
        """检查是否有标签"""
        if not cls._initialized:
            cls.initialize()
        return str(item_id) in cls._tags_data

    @classmethod
    def get_statistics(cls) -> Dict[str, int]:
        """获取统计信息"""
        if not cls._initialized:
            cls.initialize()
        return {
            "total_items_with_tags": len(cls._tags_data),
            "total_tag_keys": len(set(key for tags in cls._tags_data.values() for key in tags.keys())),
            "total_tag_values": len(set(value for tags in cls._tags_data.values() for value in tags.values()))
        }


class BaseWikiModel(BaseModel):
    """Wiki数据的基础模型类"""
    
    # 唯一标识 - 统一使用数字ID（来自文件名）
    id: Optional[str] = None

    # 基础字段
    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

    # 标签信息 - 统一从全局标签管理器获取
    tags: Optional[Dict[str, str]] = Field(None, description="项目标签信息，如星级、类型、属性加成、获取途径等")
    
    # Wiki相关字段
    wiki_url: Optional[str] = None
    wiki_id: Optional[str] = None
    
    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # 原始数据
    raw_data: Optional[Dict[str, Any]] = None
    
    def set_id_from_filename(self, filename: str) -> None:
        """从文件名提取数字ID并设置，同时自动加载标签"""
        import os
        import re

        # 获取不带扩展名的文件名
        base_name = os.path.splitext(os.path.basename(filename))[0]

        # 检查是否为纯数字
        if base_name.isdigit():
            self.id = base_name
        else:
            # 如果不是纯数字，尝试提取数字部分
            numbers = re.findall(r'\d+', base_name)
            if numbers:
                # 使用第一个找到的数字序列
                self.id = numbers[0]
            else:
                # 如果没有数字，使用原文件名
                self.id = base_name

        # 自动加载标签（如果ID存在）
        if self.id:
            self.tags = GlobalTagManager.get_tags(self.id)
    
    class Config:
        # 允许额外字段
        extra = "allow"
        # 使用枚举值
        use_enum_values = True
        # 验证赋值
        validate_assignment = True


class WikiMetadata(BaseModel):
    """Wiki元数据模型"""
    
    source: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = None
    language: Optional[str] = "zh-CN"
    
    class Config:
        extra = "allow"


class WikiContent(BaseModel):
    """Wiki内容模型"""
    
    content: Optional[str] = None
    content_type: Optional[str] = "text"
    sections: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        extra = "allow"