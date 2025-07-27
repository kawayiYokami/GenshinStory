from typing import Any, Dict, Optional

from ..services import DataLoader, TextMapService


class TalkSentenceInterpreter:
    def __init__(self, loader: DataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map_service = text_map_service
        self._sentences: Dict[int, Any] = {}

    def _prepare_data(self):
        """Pre-loads and caches the TalkSentenceConfig.json data."""
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
        """Gets speaker and text from a sentence ID."""
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
            speaker = "开拓者" # Default to Player Character if no speaker is specified

        return {"speaker": speaker, "text": text}