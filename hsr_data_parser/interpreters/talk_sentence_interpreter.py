from typing import Any, Dict, List, Optional

from ..services import DataLoader, TextMapService


class TalkSentenceInterpreter:
    def __init__(self, loader: DataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map_service = text_map_service
        self._sentences: Dict[int, Any] = {}

    def _prepare_data(self):
        """预加载并缓存 TalkSentenceConfig.json 数据。"""
        sentence_data = self.loader.get_json("TalkSentenceConfig.json")
        if sentence_data:
            self._sentences = {}
            for item in sentence_data:
                if "TalkSentenceID" in item:
                    self._sentences[item["TalkSentenceID"]] = {
                        "text_hash": item.get("TalkSentenceText", {}).get("Hash"),
                        "speaker_hash": item.get("TextmapTalkSentenceName", {}).get("Hash"),
                    }

    def get_sentence_data_by_id(self, sentence_id: int) -> Optional[Dict[str, str]]:
        """根据句子 ID 获取说话人和文本。"""
        if not self._sentences:
            self._prepare_data()

        sentence_info = self._sentences.get(sentence_id)
        if not sentence_info:
            return None

        text_hash = sentence_info.get("text_hash")
        speaker_hash = sentence_info.get("speaker_hash")

        text = self.text_map_service.get(str(text_hash)) if text_hash else ""
        
        if not text:
            return None

        if speaker_hash:
            speaker = self.text_map_service.get(str(speaker_hash))
        else:
            speaker = "开拓者" # 如果没有指定说话人，则默认为玩家角色

        return {"id": sentence_id, "speaker": speaker, "text": text}

    def interpret_playable(self, playable_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从 .playable.bytes JSON 结构中提取所有对话句子。
        """
        sentences = []
        if not playable_data:
            return sentences

        # 实际的对话 ID 在 "TalkSentenceList" 中
        talk_sentence_list = playable_data.get("TalkSentenceList")
        if not talk_sentence_list:
            return sentences

        for sentence_entry in talk_sentence_list:
            sentence_id = sentence_entry.get("TalkSentenceID")
            if sentence_id:
                sentence_data = self.get_sentence_data_by_id(sentence_id)
                if sentence_data:
                    sentences.append(sentence_data)
        
        return sentences