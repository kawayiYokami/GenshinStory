from typing import List, Optional, Dict, Any
from collections import defaultdict

from ..dataloader import ZZZDataLoader
from ..interpreters.unified_dialogue_interpreter import UnifiedDialogueInterpreter
from ..models.unified_dialogue import DialogueChapter


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

    def get_dialogue_as_markdown(self, chapter_id: str) -> str:
        """
        Generate a markdown representation of a dialogue chapter.

        Args:
            chapter_id: The ID of the dialogue chapter.

        Returns:
            A markdown string representing the dialogue chapter.
        """
        chapter = self.get_chapter_by_id(chapter_id)
        if not chapter:
            return f"# Dialogue Chapter {chapter_id} not found"

        # Simple markdown template
        markdown = f"# {chapter_id}\n\n"
        markdown += f"**Category**: {chapter.category}\n\n"
        markdown += f"**Sub-category**: {chapter.sub_category or 'N/A'}\n\n"
        markdown += "## Acts\n\n"

        for act_id, act in chapter.acts.items():
            markdown += f"### Act {act_id}\n\n"
            for line_id, line in act.lines.items():
                if line.speaker:
                    markdown += f"**{line.speaker}**: "
                if line.male_text:
                    markdown += f"{line.male_text}\n\n"
                elif line.female_text:
                    markdown += f"{line.female_text}\n\n"

                # Add options if any
                if line.options:
                    markdown += "Options:\n"
                    for option_id, option_text in line.options.items():
                        markdown += f"- {option_text}\n"
                    markdown += "\n"

        return markdown

    def get_tree(self) -> List[Dict[str, Any]]:
        """
        Generate a tree structure for dialogue chapters, categorized by category and sub-category.

        Returns:
            A list of dictionaries representing the tree structure.
        """
        chapters_by_category = self.get_chapters_by_category()

        # Organize chapters into a tree structure
        tree = []

        # Group by main category first
        categories: Dict[str, Dict[Optional[str], List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))

        for (category, sub_category), chapter_ids in chapters_by_category.items():
            for chapter_id in chapter_ids:
                categories[category][sub_category].append({
                    "id": chapter_id,
                    "name": chapter_id,
                    "type": "dialogue"
                })

        # Convert to the required format
        for category_name, sub_categories in categories.items():
            sub_category_nodes = []
            for sub_category_name, chapters in sub_categories.items():
                sub_category_display_name = sub_category_name if sub_category_name else "其他"
                sub_category_nodes.append({
                    "name": sub_category_display_name,
                    "children": chapters
                })

            tree.append({
                "name": category_name,
                "children": sub_category_nodes
            })

        return tree