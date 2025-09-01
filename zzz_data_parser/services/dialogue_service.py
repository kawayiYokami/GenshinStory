from typing import List, Optional
from collections import defaultdict

from ..dataloader import ZZZDataLoader
from ..interpreters.unified_dialogue_interpreter import UnifiedDialogueInterpreter
from ..interpreters.models.unified_dialogue import DialogueChapter


class DialogueService:
    """
    提供所有对话领域相关的查询和操作。
    这是外部调用者与对话数据交互的主要入口。
    """

    def __init__(self, loader: ZZZDataLoader):
        self.interpreter = UnifiedDialogueInterpreter(loader)

    def get_chapter_by_id(self, chapter_id: str) -> Optional[DialogueChapter]:
        """
        根据章节ID获取单个对话章节的详细数据。
        """
        return self.interpreter.interpret(chapter_id)

    def list_all_chapter_ids(self) -> List[str]:
        """
        获取所有对话章节的ID列表。
        """
        return self.interpreter.list_chapter_ids()

    def list_chapter_ids(self, category: str = None, sub_category: str = None) -> List[str]:
        """
        根据类别和子类别筛选章节ID。
        如果不提供参数，则返回所有章节ID。
        """
        all_chapters = self.list_all_chapter_ids()

        if not category and not sub_category:
            return all_chapters

        filtered_chapters = []
        for chapter_id in all_chapters:
            chapter = self.get_chapter_by_id(chapter_id)
            if chapter:
                # 检查类别匹配
                category_match = not category or chapter.category == category
                # 检查子类别匹配
                sub_category_match = not sub_category or chapter.sub_category == sub_category

                if category_match and sub_category_match:
                    filtered_chapters.append(chapter_id)

        return filtered_chapters

    def get_chapters_by_category(self) -> dict:
        """
        按类别对所有章节进行分组。
        返回一个字典，键是 (category, sub_category) 元组，值是章节ID列表。
        """
        chapters_by_category = defaultdict(list)
        all_chapters = self.list_all_chapter_ids()

        for chapter_id in all_chapters:
            chapter = self.get_chapter_by_id(chapter_id)
            if chapter:
                key = (chapter.category, chapter.sub_category)
                chapters_by_category[key].append(chapter_id)

        return dict(chapters_by_category)