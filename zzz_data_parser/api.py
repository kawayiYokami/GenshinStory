from typing import Optional

from .dataloader import ZZZDataLoader
from .services.dialogue_service import DialogueService
from .services.partner_service import PartnerService
from .services.weapon_service import WeaponService
from .services.item_service import ItemService
from .services.hollow_item_service import HollowItemService
from .services.vhs_collection_service import VHSCollectionService
from .services.session_service import SessionService
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
        self.partner = PartnerService()
        self.weapon = WeaponService()
        self.item = ItemService()
        self.hollow_item = HollowItemService()
        self.vhs_collection = VHSCollectionService()
        self.session = SessionService()

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
            act = chapter.acts.get(act_id)
            if not act:
                return f"Error: Act '{act_id}' not found in chapter '{chapter_id}'."

            # 因为 _format_single_act 是私有方法，我们需要找到 act 的序号
            # 为了简化API，我们假设调用者知道ID和顺序之间的关系，或者我们直接格式化
            # 这里我们通过查找序号来实现
            sorted_act_ids = sorted(chapter.acts.keys(), key=int)
            try:
                act_number = sorted_act_ids.index(act_id) + 1
                return formatter._format_single_act(act, act_number)
            except ValueError:
                 return f"Error: Act ID '{act_id}' could not be ordered correctly."
        else:
            # 格式化整个章节，并返回一个合并的字符串作为示例
            markdown_files = formatter.to_markdown_files()
            # 将所有内容合并，用分隔符隔开
            full_content = "\n\n---\n\n".join(markdown_files.values())
            return full_content if full_content else "# No content generated."
