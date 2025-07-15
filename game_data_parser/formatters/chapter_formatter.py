import re
from typing import List
from ..models import Chapter, Quest
from .quest_formatter import QuestFormatter

class ChapterFormatter:
    """
    负责将一个完整的 Chapter 对象格式化为用户友好的字符串，如Markdown。
    它将处理章节、系列和任务的层级结构。
    """

    def __init__(self):
        # ChapterFormatter 依赖 QuestFormatter 来处理单个任务的细节。
        self.quest_formatter = QuestFormatter()

    def format(self, chapter: Chapter, interpreter, mode: str = 'story') -> str:
        """
        将单个 Chapter 对象格式化为 Markdown。
        
        :param chapter: 要格式化的 Chapter 对象。
        :param interpreter: QuestInterpreter 实例，用于按需获取Quest对象。
        :param mode: 格式化模式 ('story' 或 'debug')。
        """
        md_lines: List[str] = []

        # Step 1: 格式化章节标题
        if mode == 'story':
            # 防御性编程：确保标题即使被意外修改，也不会在故事模式下显示ID
            clean_title = re.sub(r'\s*\((ID|id): \d+\)', '', chapter.title).strip()
            md_lines.append(f'# {clean_title}')
            md_lines.append(f"<!-- Chapter ID: {chapter.id} -->")
        else: # debug mode
            md_lines.append(f"# {chapter.title} (ID: {chapter.id})")

        # Step 2: 对章节中的任务进行排序并格式化
        # 直接按任务ID升序排列，因为复杂的触发关系不代表线性顺序。
        sorted_quests = sorted(chapter.quests, key=lambda q: q.quest_id)

        # Step 3: 遍历排序后的任务
        for quest in sorted_quests:
            quest_md = self.quest_formatter.format_quest(quest, mode=mode)
            md_lines.append("\n" + quest_md)
            md_lines.append("\n---")


        return "\n".join(md_lines)
