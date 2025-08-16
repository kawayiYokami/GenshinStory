from typing import Dict, List, Optional

from hsr_data_parser.interpreters.talk_sentence_interpreter import TalkSentenceInterpreter
from hsr_data_parser.models import RogueEvent, RogueEventDialogue, RogueEventOption
from hsr_data_parser.services.loader_service import DataLoader
from hsr_data_parser.services.text_map_service import TextMapService

class RogueEventInterpreter:
    """
    一个解释器，用于解析模拟宇宙事件的对话和选项。
    """

    def __init__(self, data_loader: DataLoader, text_map_service: TextMapService):
        self.data_loader = data_loader
        self.text_map_service = text_map_service
        self.talk_sentence_interpreter = TalkSentenceInterpreter(data_loader, text_map_service)

    def interpret(self, event_id: int) -> Optional[RogueEvent]:
        """
        解析指定ID的模拟宇宙事件。

        Args:
            event_id: 事件的ID，例如 10001。

        Returns:
            一个包含完整事件信息的RogueEvent对象，如果解析失败则返回None。
        """
        # 格式化ID以确保7位数并带有前导零，例如 10001 -> "0010001"
        event_id_str = f"{event_id:07d}"
        event_dialogue_path = f"Config/Level/Rogue/RogueDialogue/Event{event_id_str}"
        
        act_file = f"{event_dialogue_path}/Act{event_id_str}.json"
        opt_file = f"{event_dialogue_path}/Opt{event_id_str}.json"

        # 提供相对于项目根目录的正确基础路径
        act_data = self.data_loader.get_json(act_file, base_path_override="turnbasedgamedata")
        opt_data = self.data_loader.get_json(opt_file, base_path_override="turnbasedgamedata")

        if not act_data:
            print(f"错误: 无法加载 Act 文件: {event_dialogue_path}/{act_file}")
            return None

        # 将 Opt 数据处理成一个以 OptionID 为键的字典，以便快速查找
        opt_map = {opt['OptionID']: opt for opt in opt_data.get('OptionList', [])} if opt_data else {}
        
        dialogues = []
        
        # 遍历剧本中的所有指令序列
        for task_list_container in act_data.get("OnStartSequece", []):
            task_list = task_list_container.get("TaskList", [])
            
            for task in task_list:
                task_type = task.get("$type")
                
                # 处理简单对话
                if task_type == "RPG.GameCore.PlayRogueSimpleTalk":
                    simple_talk_list = []
                    for item in task.get("SimpleTalkList", []):
                        sentence_id = item.get("TalkSentenceID")
                        sentence_data = self.talk_sentence_interpreter.get_sentence_data_by_id(sentence_id)
                        if sentence_data and sentence_data.get("text"):
                            simple_talk_list.append(sentence_data["text"])

                    if simple_talk_list:
                        dialogues.append(RogueEventDialogue(simple_talk=simple_talk_list))
                
                # 处理选项对话
                elif task_type == "RPG.GameCore.PlayRogueOptionTalk":
                    options = []
                    for opt_json in task.get("OptionList", []):
                        option_id = opt_json.get("RogueOptionID")
                        
                        # 选项文本直接通过hash从text map获取
                        text_hash = opt_json.get("OptionTextmapID", {}).get("Hash")
                        option_text = self.text_map_service.get(text_hash) if text_hash is not None else ""
                        
                        # 从 opt_map 中查找附加描述
                        opt_effect = opt_map.get(option_id, {})
                        desc_value = opt_effect.get("DescValue")
                        description = f"效果数值: {desc_value}" if desc_value is not None else "无特殊效果"

                        # 仅当选项包含文本时才添加
                        if option_text:
                            options.append(RogueEventOption(
                                id=option_id,
                                text=option_text,
                                description=description,
                                trigger=opt_json.get("TriggerCustomString")
                            ))
                    if options:
                        dialogues.append(RogueEventDialogue(options=options))

        if not dialogues:
            return None
            
        return RogueEvent(id=event_id, dialogues=dialogues)

    def interpret_all(self) -> List[RogueEvent]:
        """
        通过调用加载器发现并解析所有的模拟宇宙事件。

        Returns:
            一个包含所有已解析事件的 RogueEvent 对象列表。
        """
        events = []
        event_ids = self.data_loader.discover_rogue_event_ids()
        
        for event_id in event_ids:
            event_data = self.interpret(event_id)
            if event_data:
                events.append(event_data)
        
        return events
