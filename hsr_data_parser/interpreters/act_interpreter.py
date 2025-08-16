from typing import Any, List, Optional

from ..models import ActScript, DialogueBlock, DialogueSentence
from ..services import DataLoader
from .talk_sentence_interpreter import TalkSentenceInterpreter


class ActInterpreter:
    def __init__(self, loader: DataLoader, talk_sentence_interpreter: TalkSentenceInterpreter):
        self.loader = loader
        self.talk_sentence_interpreter = talk_sentence_interpreter

    def _extract_dialogue_blocks(self, data: Any) -> List[DialogueBlock]:
        """递归遍历数据结构以查找并提取对话块。"""
        blocks = []
        if isinstance(data, dict):
            # 检查此字典是否代表包含对话的任务
            task_type = data.get("$type")
            if task_type in ("RPG.GameCore.PlayAndWaitSimpleTalk", "RPG.GameCore.PlayMissionTalk"):
                sentences = []
                for t in data.get("SimpleTalkList", []):
                    sentence_data = self.talk_sentence_interpreter.get_sentence_data_by_id(t.get("TalkSentenceID"))
                    if sentence_data:
                        sentences.append(DialogueSentence(text=sentence_data["text"], speaker=sentence_data["speaker"]))
                if sentences:
                    blocks.append(DialogueBlock(sentences=sentences))

            elif task_type == "RPG.GameCore.PlayOptionTalk":
                options = []
                for o in data.get("OptionList", []):
                    sentence_data = self.talk_sentence_interpreter.get_sentence_data_by_id(o.get("TalkSentenceID"))
                    if sentence_data and sentence_data.get("text"):
                        options.append(DialogueSentence(text=sentence_data["text"], speaker=sentence_data.get("speaker")))
                if options:
                    blocks.append(DialogueBlock(sentences=options))

            # 在嵌套结构中递归搜索
            for value in data.values():
                blocks.extend(self._extract_dialogue_blocks(value))

        elif isinstance(data, list):
            for item in data:
                blocks.extend(self._extract_dialogue_blocks(item))
        
        return blocks

    def interpret_file(self, file_path: str) -> Optional[ActScript]:
        """解析单个 Act 脚本文件。"""
        script_data = self.loader.get_json(file_path, base_path_override="turnbasedgamedata")
        if not script_data:
            return None
        
        dialogue_blocks = self._extract_dialogue_blocks(script_data)
        return ActScript(dialogue_blocks=dialogue_blocks)