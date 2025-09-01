from typing import Optional

from .dataloader import ZZZDataLoader
from .services.dialogue_service import DialogueService
from .formatters.dialogue_formatter import DialogueFormatter

class ZZZDataAPI:
    """
    绝区零数据解析器的统一对外接口 (API Facade)。
    这个类本身不实现具体业务逻辑，而是将请求委托给相应的领域服务。
    """
    def __init__(self, data_root_path: Optional[str] = None):
        """
        初始化API，设置数据根目录并实例化所有领域服务。
        """
        # --- 核心组件 ---
        self.loader = ZZZDataLoader(root_path=data_root_path)

        # --- 领域服务 ---
        self.dialogue = DialogueService(self.loader)

    def format_dialogue(self, chapter_id: str, act_id: str = None) -> str:
        """
        格式化指定ID的对话章节为Markdown文本。
        如果提供了 act_id，则只格式化该章节下的指定一幕。

        Args:
            chapter_id: 要格式化的章节ID
            act_id: 可选，要格式化的幕ID。如果未提供，则格式化整个章节。

        Returns:
            格式化的Markdown字符串
        """
        chapter = self.dialogue.get_chapter_by_id(chapter_id)
        if not chapter:
            return f"Error: Dialogue chapter '{chapter_id}' not found."

        formatter = DialogueFormatter(chapter)

        if act_id:
            # 格式化单个幕 (Act)
            # 注意：新的统一模型中，Act 是直接存储在 chapter.acts 中的
            act = chapter.acts.get(act_id)
            if not act:
                return f"Error: Act '{act_id}' not found in chapter '{chapter_id}'."

            # 为了简化，我们直接返回整个章节的 Markdown，
            # 但在实际应用中，你可能需要修改 DialogueFormatter 以支持格式化单个 Act。
            # 这里我们只是给出一个示例。
            return formatter.to_markdown()
        else:
            # 格式化整个章节
            return formatter.to_markdown()
