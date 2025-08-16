from typing import Any, Dict, List, Optional

from ..models import ActScript, DialogueBlock, DialogueElement, DialogueSentence
from ..services import DataLoader
from .talk_sentence_interpreter import TalkSentenceInterpreter


class FlowchartInterpreter:
    """
    解析事件驱动的、基于流程图的JSON文件（DS和Story类型）。
    这种类型的脚本由通过 CustomString 触发器链接在一起的 TaskLists 组成。
    """

    def __init__(self, loader: DataLoader, talk_sentence_interpreter: TalkSentenceInterpreter):
        self.loader = loader
        self.talk_sentence_interpreter = talk_sentence_interpreter

    def interpret_file(self, file_path: str) -> Optional[ActScript]:
        """
        通过映射所有基于触发器的事件链，然后解析所有入口点链来解析DS或Story文件。
        """
        story_data = self.loader.get_json(file_path, base_path_override="turnbasedgamedata")
        if not story_data:
            return None

        on_start_sequence = story_data.get('OnStartSequece', [])

        # --- 阶段 1: 构建精确的触发器映射 ---
        trigger_map = {}
        for task_list_dict in on_start_sequence:
            task_list = task_list_dict.get('TaskList', [])
            for i, task in enumerate(task_list):
                if task.get('$type') == 'RPG.GameCore.WaitCustomString':
                    trigger = task.get('CustomString', {}).get('Value')
                    if trigger and trigger not in trigger_map:
                        trigger_map[trigger] = task_list[i+1:]

        # --- 阶段 2: 识别并解析所有入口点 ---
        all_parsed_elements = []
        for task_list_dict in on_start_sequence:
            task_list = task_list_dict.get('TaskList', [])
            if not task_list:
                continue
            
            is_entry_point = task_list[0].get('$type') != 'RPG.GameCore.WaitCustomString'

            if is_entry_point:
                parsed_elements = self._parse_recursive_flow(task_list, trigger_map)
                all_parsed_elements.extend(parsed_elements)

        # --- 阶段 3: 包装结果 ---
        if all_parsed_elements:
            dialogue_block = DialogueBlock(sentences=all_parsed_elements)
            return ActScript(dialogue_blocks=[dialogue_block])
        
        return None

    def _parse_recursive_flow(self, current_tasks: List[Dict], trigger_map: Dict[str, List[Dict]]) -> List['DialogueElement']:
        """
        递归地解析任务列表，从所有已知来源中提取对话。
        """
        from ..models import DialogueSentence

        elements = []
        if not current_tasks:
            return elements

        for task in current_tasks:
            task_type = task.get('$type')

            # --- 处理来自触发器的对话 ---
            if task_type in ('RPG.GameCore.WaitCustomString', 'RPG.GameCore.TriggerCustomString'):
                trigger_value = task.get('CustomString', {}).get('Value')
                if trigger_value and trigger_value.startswith('TalkSentence_'):
                    try:
                        sentence_id = int(trigger_value.split('_')[-1])
                        sentence_data = self.talk_sentence_interpreter.get_sentence_data_by_id(sentence_id)
                        if sentence_data:
                            elements.append(DialogueSentence(
                                id=sentence_data.get('id'),
                                speaker=sentence_data.get('speaker'),
                                text=sentence_data.get('text')
                            ))
                    except (ValueError, IndexError):
                        pass # 如果字符串不是有效的 TalkSentence ID，则忽略

            # --- 处理来自 Playable 资产的对话 ---
            elif task_type == 'RPG.GameCore.PlayTimeline':
                asset_path = task.get('AssetPath')
                if asset_path:
                    if not asset_path.endswith('.json'):
                        full_path = f"{asset_path}.json"
                    else:
                        full_path = asset_path
                    playable_data = self.loader.get_json(full_path, base_path_override="turnbasedgamedata")
                    if playable_data:
                        sentences_from_playable = self.talk_sentence_interpreter.interpret_playable(playable_data)
                        if sentences_from_playable:
                            for sentence_dict in sentences_from_playable:
                                elements.append(DialogueSentence(
                                    id=sentence_dict.get('id'),
                                    speaker=sentence_dict.get('speaker'),
                                    text=sentence_dict.get('text')
                                ))

            # --- 处理玩家选项 ---
            elif task_type == 'RPG.GameCore.PlayOptionTalk':
                for option_data in task.get('OptionList', []):
                    option_talk_id = option_data.get('TalkSentenceID')
                    if not option_talk_id:
                        continue

                    option_sentence_data = self.talk_sentence_interpreter.get_sentence_data_by_id(option_talk_id)
                    if option_sentence_data:
                        elements.append(DialogueSentence(
                            id=option_sentence_data.get('id'),
                            text=option_sentence_data['text'],
                            speaker="开拓者"
                        ))

                    trigger_custom_string_data = option_data.get('TriggerCustomString')
                    trigger_string = None
                    if isinstance(trigger_custom_string_data, dict):
                        trigger_string = trigger_custom_string_data.get('Value')
                    elif isinstance(trigger_custom_string_data, str):
                        trigger_string = trigger_custom_string_data
                    
                    if trigger_string:
                        # 触发器字符串本身可以是一个对话句子。
                        if trigger_string.startswith('TalkSentence_'):
                            try:
                                sentence_id = int(trigger_string.split('_')[-1])
                                sentence_data = self.talk_sentence_interpreter.get_sentence_data_by_id(sentence_id)
                                if sentence_data:
                                    elements.append(DialogueSentence(
                                        id=sentence_data.get('id'),
                                        speaker=sentence_data.get('speaker'),
                                        text=sentence_data.get('text')
                                    ))
                            except (ValueError, IndexError):
                                pass

                        # 然后，检查此触发器是否也启动了一个新的任务列表。
                        follow_up_tasks = trigger_map.get(trigger_string)
                        if follow_up_tasks:
                            follow_up_elements = self._parse_recursive_flow(follow_up_tasks, trigger_map)
                            elements.extend(follow_up_elements)
        return elements