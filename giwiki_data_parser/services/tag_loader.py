import json
import logging
from typing import Dict, Optional
from pathlib import Path


class TagLoader:
    """标签加载器 - 从链接文件中加载标签信息"""

    def __init__(self, link_file_path: str):
        """
        初始化标签加载器

        Args:
            link_file_path: 链接文件路径，如 "gi_wiki_scraper/output/link/5_武器.json"
        """
        self.link_file_path = Path(link_file_path)
        self.tags_data: Dict[str, Dict[str, str]] = {}
        self.logger = logging.getLogger(__name__)

        # 加载标签数据
        self.load_tags()

    def load_tags(self) -> None:
        """从链接文件加载标签数据"""
        try:
            if not self.link_file_path.exists():
                self.logger.warning(f"链接文件不存在: {self.link_file_path}")
                return

            with open(self.link_file_path, 'r', encoding='utf-8') as f:
                link_data = json.load(f)

            # 将列表转换为以ID为键的字典，方便查找
            for item in link_data:
                item_id = item.get('id')
                tags = item.get('tags', {})

                if item_id and tags:
                    self.tags_data[str(item_id)] = tags

            self.logger.info(f"成功加载 {len(self.tags_data)} 个项目的标签数据")

        except json.JSONDecodeError as e:
            self.logger.error(f"解析链接文件JSON失败: {e}")
        except Exception as e:
            self.logger.error(f"加载标签数据时出错: {e}")

    def get_tags_by_id(self, item_id: str) -> Dict[str, str]:
        """
        根据ID获取标签信息

        Args:
            item_id: 项目ID

        Returns:
            标签字典，如果没有找到则返回空字典
        """
        return self.tags_data.get(str(item_id), {})

    def has_tags(self, item_id: str) -> bool:
        """
        检查指定ID是否有标签信息

        Args:
            item_id: 项目ID

        Returns:
            如果有标签信息返回True，否则返回False
        """
        return str(item_id) in self.tags_data

    def get_all_tag_keys(self) -> set:
        """
        获取所有标签键的集合

        Returns:
            所有标签键的集合
        """
        all_keys = set()
        for tags in self.tags_data.values():
            all_keys.update(tags.keys())
        return all_keys

    def get_all_tag_values(self) -> set:
        """
        获取所有标签值的集合

        Returns:
            所有标签值的集合
        """
        all_values = set()
        for tags in self.tags_data.values():
            all_values.update(tags.values())
        return all_values

    def get_items_by_tag(self, tag_key: str, tag_value: str) -> list:
        """
        根据标签键值对获取项目ID列表

        Args:
            tag_key: 标签键，如 "武器星级"
            tag_value: 标签值，如 "五星"

        Returns:
            匹配的项目ID列表
        """
        matching_ids = []
        for item_id, tags in self.tags_data.items():
            if tags.get(tag_key) == tag_value:
                matching_ids.append(item_id)
        return matching_ids

    def get_statistics(self) -> Dict[str, int]:
        """
        获取标签数据统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_items": len(self.tags_data),
            "total_tag_keys": len(self.get_all_tag_keys()),
            "total_tag_values": len(self.get_all_tag_values())
        }