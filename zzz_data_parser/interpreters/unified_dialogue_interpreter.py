import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from ..dataloader import ZZZDataLoader
from ..models.unified_dialogue import DialogueChapter, DialogueAct, DialogueLine
from ..utils.key_normalizer import normalize_dialogue_key


class UnifiedDialogueInterpreter:
    """
    一个统一的对话解析器，使用基于规则的正则表达式引擎来处理多种key格式。
    """

    # 定义所有已知 key 格式的正则表达式规则
    # 规则的顺序很重要，优先匹配更具体的规则
    KEY_PATTERNS = [
        # --- Main Story (最精确的规则放最前) ---
        # Main_Chat_Chapter00_30000011_01
        {
            "name": "Main_Chat",
            "pattern": re.compile(r"^(?P<prefix>Main_Chat)_(?P<chapter_id>Chapter\d+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Main",
            "sub_category": "Chat"
        },
        # Main_Bubble_Chapter110_40100107_02
        {
            "name": "Main_Bubble",
            "pattern": re.compile(r"^(?P<prefix>Main_Bubble)_(?P<chapter_id>Chapter\d+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Main",
            "sub_category": "Bubble"
        },
        # Main_OngoingLevel_Chapter120_110931030_01
        {
            "name": "Main_OngoingLevel",
            "pattern": re.compile(r"^(?P<prefix>Main_OngoingLevel)_(?P<chapter_id>Chapter\d+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Main",
            "sub_category": "OngoingLevel"
        },
        # Main_GalGame_Chapter110_11100270_039
        {
            "name": "Main_GalGame",
            "pattern": re.compile(r"^(?P<prefix>Main_GalGame)_(?P<chapter_id>Chapter\d+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Main",
            "sub_category": "GalGame"
        },
        # MainChat_2_0001_00 (需要被规范化为 Main_Chat_Chapter02, 匹配前缀'MainChat')
        {
            "name": "MainChat_Number",
            "pattern": re.compile(r"^(?P<prefix>MainChat)_(?P<chapter_id>\d+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Main",
            "sub_category": "Chat"
        },
        # MainBubble_Chapter01_0001_01
        {
            "name": "MainBubble",
            "pattern": re.compile(r"^(?P<prefix>MainBubble)_(?P<chapter_id>Chapter\d+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Main",
            "sub_category": "Bubble"
        },

        # --- Companion ---
        # Companion_Bubble_ChapterAnbySP_46310001_01
        {
            "name": "Companion_Bubble",
            "pattern": re.compile(r"^(?P<prefix>Companion_Bubble)_(?P<chapter_id>Chapter\w+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Companion",
            "sub_category": "Bubble"
        },
        # CompanionBubble_ChapterBurnice_0050_001
        {
            "name": "CompanionBubble",
            "pattern": re.compile(r"^(?P<prefix>CompanionBubble)_(?P<chapter_id>Chapter\w+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Companion",
            "sub_category": "Bubble"
        },
        # Companion_Chat_Special1UndercoverR&B_38000180_08
        {
            "name": "Companion_Chat_Special",
            "pattern": re.compile(r"^(?P<prefix>Companion_Chat)_(?P<chapter_id>Special[^_]+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Companion",
            "sub_category": "Chat"
        },
        # CompanionChat_ChapterBurnice_0001_001
        {
            "name": "CompanionChat",
            "pattern": re.compile(r"^(?P<prefix>CompanionChat)_(?P<chapter_id>Chapter\w+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Companion",
            "sub_category": "Chat"
        },

        # --- Activity ---
        # Activity_GalGame_Summer_10162008_015 & Activity_GalGame_AbyssS2-Story4_10161604_011
        {
            "name": "Activity_GalGame_Named",
            "pattern": re.compile(r"^(?P<prefix>Activity_GalGame)_(?P<chapter_id>[^_]+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Activity",
            "sub_category": "GalGame"
        },
        # Activity_Ongoing_UltimateAngler_120369001_01
        {
            "name": "Activity_Ongoing",
            "pattern": re.compile(r"^(?P<prefix>Activity_Ongoing)_(?P<chapter_id>[^_]+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Activity",
            "sub_category": "Ongoing"
        },

        # --- Side Stories & Misc ---
        # GalGame_Special2VirtualRevenge_090_018
        {
            "name": "GalGame_Special",
            "pattern": re.compile(r"^(?P<prefix>GalGame)_(?P<chapter_id>Special[^_]+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "GalGame",
            "sub_category": None
        },
        # PhotoSideBubble_Chapter01_00001_01
        {
            "name": "PhotoSideBubble",
            "pattern": re.compile(r"^(?P<prefix>PhotoSideBubble)_(?P<chapter_id>Chapter\d+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Side",
            "sub_category": "PhotoBubble"
        },
        # PhotoSideChat_Chapter01_00001_01
        {
            "name": "PhotoSideChat",
            "pattern": re.compile(r"^(?P<prefix>PhotoSideChat)_(?P<chapter_id>Chapter\d+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Side",
            "sub_category": "PhotoChat"
        },
        # SideChat_Chapter00_001_01
        {
            "name": "SideChat",
            "pattern": re.compile(r"^(?P<prefix>SideChat)_(?P<chapter_id>Chapter\d+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Side",
            "sub_category": "Chat"
        },
        # Side_Chat_Side014_30520204_01
        {
            "name": "Side_Chat",
            "pattern": re.compile(r"^(?P<prefix>Side_Chat)_(?P<chapter_id>[^_/]+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Side",
            "sub_category": "Chat"
        },
        # Side_GalGame_SuibianTemple_11120080_044
        {
            "name": "Side_GalGame",
            "pattern": re.compile(r"^(?P<prefix>Side_GalGame)_(?P<chapter_id>[^_/]+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Side",
            "sub_category": "GalGame"
        },
        # Side_OngoingLevel_Side20JFF_112001001_01
        {
            "name": "Side_OngoingLevel",
            "pattern": re.compile(r"^(?P<prefix>Side_OngoingLevel)_(?P<chapter_id>Side\d+[a-zA-Z]*)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Side",
            "sub_category": "OngoingLevel"
        },
        # StoreChat_Street_0070_01
        {
            "name": "StoreChat",
            "pattern": re.compile(r"^(?P<prefix>StoreChat)_(?P<chapter_id>[^_/]+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Side",
            "sub_category": "StoreChat"
        },
        # Store_Chat_ZZZStudio_30420038_05
        {
            "name": "Store_Chat",
            "pattern": re.compile(r"^(?P<prefix>Store_Chat)_(?P<chapter_id>[^_/]+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Side",
            "sub_category": "StoreChat"
        },
        # Bubble_ChapterLycaon_0011_01
        {
            "name": "Bubble_Generic",
            "pattern": re.compile(r"^(?P<prefix>Bubble)_(?P<chapter_id>Chapter\w+)_(?P<act_id>\d+)_(?P<line_info>.+)$"),
            "category": "Generic",
            "sub_category": "Bubble"
        },
    ]

    def __init__(self, data_loader: ZZZDataLoader):
        self.loader = data_loader
        self._text_map = self.loader.get_text_map()
        self._classified_keys: Optional[Dict[str, List[Dict]]] = None

    def _classify_keys(self):
        """
        遍历所有 TextMap keys，使用 KEY_PATTERNS 进行分类和信息提取。
        只执行一次，结果缓存。
        """
        if self._classified_keys is not None:
            return

        # 导入预处理器
        from ..utils.key_normalizer import normalize_dialogue_key

        self._classified_keys = defaultdict(list)

        for original_key, value in self._text_map.items():
            # 使用预处理器规范化 key
            normalized_key = normalize_dialogue_key(original_key)

            for rule in self.KEY_PATTERNS:
                match = rule["pattern"].match(normalized_key)
                if match:
                    # 提取命名捕获组的数据
                    extracted_data = match.groupdict()
                    extracted_data['original_key'] = original_key # 保留原始 key
                    extracted_data['normalized_key'] = normalized_key # 也记录规范化的 key
                    extracted_data['category'] = rule['category']
                    extracted_data['sub_category'] = rule['sub_category']
                    extracted_data['value'] = value

                    # 按 chapter_id 进行分组
                    chapter_id = extracted_data.get('chapter_id')
                    if chapter_id:
                        self._classified_keys[chapter_id].append(extracted_data)

                    # 匹配成功后，跳出内层循环，处理下一个key
                    break

    def list_chapter_ids(self) -> List[str]:
        """获取所有已分类章节的ID列表。"""
        if self._classified_keys is None:
            self._classify_keys()
        return list(self._classified_keys.keys())

    def interpret(self, chapter_id: str) -> Optional[DialogueChapter]:
        """
        解析单个章节的完整数据。
        """
        if self._classified_keys is None:
            self._classify_keys()

        if chapter_id not in self._classified_keys:
            return None

        keys_in_chapter = self._classified_keys[chapter_id]

        # 从第一条key记录中获取元数据
        meta = keys_in_chapter[0]
        chapter = DialogueChapter(
            id=chapter_id,
            category=meta['category'],
            sub_category=meta['sub_category']
        )

        # 按 act_id 对 keys 进行二次分组
        act_key_groups = defaultdict(list)
        for key_data in keys_in_chapter:
            act_id = key_data.get('act_id')
            if act_id:
                act_key_groups[act_id].append(key_data)

        # 遍历每个 act，解析其内部的对话行
        for act_id, keys_in_act in act_key_groups.items():
            act = DialogueAct(id=act_id)

            # 复用旧解析器中的行解析逻辑
            temp_lines = defaultdict(DialogueLine)

            for key_data in keys_in_act:
                original_key = key_data['original_key']
                value = key_data['value']
                line_info = key_data['line_info']

                # 处理选项 (Options)
                # 例如: ..._05_Option1_01
                option_parts = line_info.split('_Option')
                if len(option_parts) > 1:
                    line_num_and_option = option_parts[0].rsplit('_', 1)
                    if len(line_num_and_option) == 2 and line_num_and_option[1].isdigit():
                        line_num = line_num_and_option[1]
                        option_id = f"Option{option_parts[1].split('_')[0]}"
                        temp_lines[line_num].options[option_id] = value
                        continue

                # 处理行内说话人 (Speaker)
                # 例如: ..._01_Name01
                line_speaker_parts = line_info.rsplit('_Name', 1)
                if len(line_speaker_parts) > 1 and line_speaker_parts[1].isdigit():
                    line_num = line_speaker_parts[0].rsplit('_', 1)[-1]
                    if line_num.isdigit():
                        temp_lines[line_num].speaker = value
                        continue

                # 处理整个对话组的说话人 (Group Speakers)
                # 例如: ..._Name01, ..._Name02
                if line_info.startswith('Name') and line_info[4:].isdigit():
                    act.speakers[line_info] = value
                    continue

                # 处理对话行 (Dialogue Lines)
                # 例如: ..._01, ..._01F
                line_num_str = line_info
                is_female = line_info.endswith('F')
                if is_female:
                    line_num_str = line_info[:-1]

                if line_num_str.isdigit():
                    line_num = line_num_str
                    if is_female:
                        temp_lines[line_num].female_text = value
                    else:
                        temp_lines[line_num].male_text = value

            # 按行号对对话进行排序
            sorted_keys = sorted(temp_lines.keys(), key=lambda x: int(x))
            act.lines = {k: temp_lines[k] for k in sorted_keys}

            # 添加默认角色：哲 (Name01) 和 铃 (Name02)
            # 检查是否已存在，避免覆盖
            if 'Name01' not in act.speakers:
                act.speakers['Name01'] = '哲'
            if 'Name02' not in act.speakers:
                act.speakers['Name02'] = '铃'

            # 将构建好的 DialogueAct 添加到 DialogueChapter 中
            chapter.acts[act_id] = act

        return chapter