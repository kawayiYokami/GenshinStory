import os
import dataclasses
from typing import Any, Dict, List, Optional, Set
from pathlib import Path

from ..dataloader import DataLoader
from ..interpreters.quest_interpreter import QuestInterpreter
from ..services.text_map_service import TextMapService
from ..formatters.quest_formatter import QuestFormatter
from ..formatters.chapter_formatter import ChapterFormatter
from ..models import Quest, Chapter, QuestStep, DialogueNode


class QuestService:
    """
    提供所有与“任务(Quest)”领域相关的查询和操作。
    """
    def __init__(self, loader: DataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map_service = text_map_service
        
        # QuestInterpreter is now self-contained and does not need a db_service.
        self.quest_interpreter = QuestInterpreter(loader, self.text_map_service)
        # The preparation step is crucial and should be called once after initialization.
        self.quest_interpreter._prepare_data_and_build_maps()
        
        self.quest_formatter = QuestFormatter()
        self.chapter_formatter = ChapterFormatter()

        # 将任务类型 key 到中文名称的映射提升为类属性
        self.category_titles = {
            "AQ": "魔神任务",
            "EQ": "活动任务",
            "WQ": "世界任务",
            "IQ": "邀约事件",
            "FQ": "魔神任务间章",
            "LQ": "传说任务",
            "ORPHAN_SERIES": "系列任务",
            "ORPHAN_MISC": "零散任务",
        }

    def get_category_title(self, category_key: str) -> str:
        """根据类型key获取易读的中文标题。"""
        return self.category_titles.get(category_key, f"未知分类 ({category_key})")

    def list_quests(self) -> List[Dict[str, Any]]:
        """获取所有任务的简明列表。"""
        return self.search_quests()

    def search_quests(self, category: Optional[str] = None, chapter_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取所有任务的简明列表，支持按类型和章节筛选。
        """
        all_quests = [self.get_quest_by_id(qid) for qid in self.quest_interpreter.get_all_quest_ids()]
        
        filtered_quests = []
        for quest in all_quests:
            if not quest: continue

            if category and quest.quest_type != category:
                continue
            if chapter_id and quest.chapter_id != chapter_id:
                continue
            
            filtered_quests.append({"id": quest.quest_id, "title": quest.quest_title})

        return sorted(filtered_quests, key=lambda q: q['id'])

    def get_quest_by_id(self, item_id: int) -> Optional[Quest]:
        """
        获取单个任务的完整信息。
        """
        return self.quest_interpreter.interpret(item_id)
            
    def _fill_quest_details(self, quest: Quest) -> Quest:
        """
        私有辅助方法，用于填充一个Quest对象的懒加载内容（如对话）。
        """
        if not quest:
            return quest
        
        for step in quest.steps:
            if step.talk_ids and not step.dialogue_nodes: # 仅在需要且尚未加载时加载
                step.dialogue_nodes = self.get_dialogs_for_step(step, quest.quest_id)
        return quest

    def get_quest_as_json(self, item_id: int) -> Optional[Dict]:
        """根据ID获取单个任务的详细信息，并以JSON兼容的字典格式返回。"""
        quest = self.get_quest_by_id(item_id)
        if not quest:
            return None
        
        # 在序列化之前，填充完整的对话数据
        quest = self._fill_quest_details(quest)
        
        return dataclasses.asdict(quest)

    def get_quest_as_markdown(self, item_id: int) -> Optional[str]:
        """获取单个任务的格式化Markdown文档。"""
        quest = self.get_quest_by_id(item_id)
        if not quest:
            return None

        # 在格式化之前，填充完整的对话数据
        quest = self._fill_quest_details(quest)

        return self.quest_formatter.format_quest(quest)

    def list_quest_chapters(self, type: Optional[str] = None) -> List[Chapter]:
        """获取所有或特定类型的章节列表。"""
        all_chapter_data = self.quest_interpreter.get_all_chapters()
        if type:
            return [ch for ch in all_chapter_data if ch.quest_type == type]
        return all_chapter_data

    def list_quest_categories(self) -> List[str]:
        """获取所有任务类型的列表 (e.g., "AQ", "WQ")。"""
        categories: Set[str] = set()
        for qid in self.quest_interpreter.get_all_quest_ids():
            quest = self.get_quest_by_id(qid)
            if quest and quest.quest_type:
                categories.add(quest.quest_type)
        return sorted(list(categories))

    def list_orphan_quests(self) -> List[Quest]:
        """获取所有孤立任务（未分配到任何章节）的完整对象列表。"""
        orphan_ids = self.quest_interpreter.get_orphan_quest_ids()
        quests = [self.get_quest_by_id(qid) for qid in orphan_ids if self.get_quest_by_id(qid) is not None]
        return quests

    def get_dialogs_for_step(self, step: 'QuestStep', quest_id: int) -> List['DialogueNode']:
        """
        按需为给定的 QuestStep 解析其包含的对话。
        """
        if not step.talk_ids:
            return []
        
        raw_quest_data = self.quest_interpreter.get_raw_data(quest_id)
        if not raw_quest_data:
            return []
        
        current_quest_talks = {t["id"]: t for t in raw_quest_data.get("talks", [])}
        
        all_dialogues = []
        for talk_id in step.talk_ids:
            dialogue_nodes = self.quest_interpreter._find_and_parse_dialog(
                base_talk_id=talk_id,
                current_quest_talks=current_quest_talks,
                context_quest_id=quest_id
            )
            all_dialogues.extend(dialogue_nodes)
        return all_dialogues

    def get_chapter_as_markdown(self, chapter_id: int, mode: str = 'story') -> Optional[str]:
        """
        获取一个完整章节的故事线（Markdown格式）。
        """
        chapter = self.quest_interpreter._chapter_map.get(chapter_id)
        if not chapter:
            return None
            
        # 填充对话
        for quest in chapter.quests:
            self._fill_quest_details(quest)

        return self.chapter_formatter.format(chapter, self, mode=mode)


    def get_quest_tree(self) -> List[Dict[str, Any]]:
        """
        获取任务的树状结构图 (Category -> Chapter -> Quest)。
        """
        # 1. 获取所有章节，它们已经包含了各自的任务
        all_chapters = self.list_quest_chapters()

        # 1.5 过滤掉没有任务的空章节
        non_empty_chapters = [ch for ch in all_chapters if ch.quests]

        # 2. 按 Category 分组
        category_map: Dict[str, List[Chapter]] = {}
        for chapter in non_empty_chapters:
            if chapter.quest_type:
                if chapter.quest_type not in category_map:
                    category_map[chapter.quest_type] = []
                category_map[chapter.quest_type].append(chapter)

        # 3. 构建最终的树状列表
        result_tree = []
        
        # 3.1 定义期望的分类顺序
        # 期望顺序: 魔神 -> 传说 -> 活动 -> 世界 -> 系列 -> 零散
        # 注意: 将相关的类型放在一起，例如魔神任务(AQ)和间章(FQ)
        desired_order = [
            "AQ",  # 魔神任务
            "FQ",  # 魔神任务间章
            "LQ",  # 传说任务
            "IQ",  # 邀约事件
            "EQ",  # 活动任务
            "WQ",  # 世界任务
            "ORPHAN_SERIES", # 系列任务
            "ORPHAN_MISC",   # 零散任务
        ]
        
        # 3.2 创建一个从 key 到排序索引的映射
        order_map = {key: i for i, key in enumerate(desired_order)}
        
        # 3.3 根据期望顺序对分类 key 进行排序
        # 未在期望列表中的 key 将被排到最后
        sorted_categories = sorted(
            category_map.keys(),
            key=lambda k: order_map.get(k, len(desired_order))
        )

        # 3.4 按照排序后的 key 构建结果树
        for category_key in sorted_categories:
            chapters = sorted(category_map[category_key], key=lambda c: c.id)
            
            # 创建第一层节点：任务类型
            category_node = {
                "id": category_key,
                "title": self.get_category_title(category_key),
                "children": []
            }
            
            # 创建第二层节点：章节
            for chapter in chapters:
                chapter_node = {
                    "id": chapter.id,
                    "title": f"{chapter.chapter_num_text} {chapter.title}" if chapter.chapter_num_text else chapter.title,
                    "children": []
                }
                
                # 创建第三层节点：任务
                sorted_quests = sorted(chapter.quests, key=lambda q: q.quest_id)
                for quest in sorted_quests:
                    quest_node = {
                        "id": quest.quest_id,
                        "title": quest.quest_title,
                    }
                    chapter_node["children"].append(quest_node)
                
                category_node["children"].append(chapter_node)
            
            result_tree.append(category_node)
            
        return result_tree
