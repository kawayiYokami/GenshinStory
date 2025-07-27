from typing import Dict, List
from collections import defaultdict

from ..models.character import Character, CharacterStory, CharacterVoiceLine
from ..services import DataLoader, TextMapService

class CharacterInterpreter:
    """
    Interprets character data from AvatarConfig, StoryAtlas, and VoiceAtlas,
    combining them into a list of Character objects.
    """
    def __init__(self, loader: DataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map_service = text_map_service
        self.characters: Dict[int, Character] = {}

    def interpret_all(self) -> List[Character]:
        """
        Parses all related files and returns a list of complete Character objects.
        """
        self._parse_base_characters()
        self._parse_stories()
        self._parse_voice_lines()
        
        return list(self.characters.values())

    def _parse_base_characters(self):
        """Parses AvatarConfig.json to create initial character objects."""
        avatar_data = self.loader.get_json("AvatarConfig.json")
        if not avatar_data:
            return

        for char_info in avatar_data:
            char_id = char_info.get("AvatarID")
            name_hash = char_info.get("AvatarName", {}).get("Hash")
            if not char_id or not name_hash:
                continue

            name = self.text_map_service.get(str(name_hash))
            if name:
                self.characters[char_id] = Character(id=char_id, name=name)

    def _parse_stories(self):
        """Parses StoryAtlas.json and attaches stories to characters."""
        story_data = self.loader.get_json("StoryAtlas.json")
        if not story_data:
            return

        stories_by_char_id = defaultdict(list)
        for story_info in story_data:
            char_id = story_info.get("AvatarID")
            story_hash = story_info.get("Story", {}).get("Hash")
            story_id = story_info.get("StoryID")
            if not char_id or not story_hash or not story_id:
                continue
            
            text = self.text_map_service.get(str(story_hash))
            if text:
                stories_by_char_id[char_id].append(CharacterStory(id=story_id, text=text))
        
        for char_id, stories in stories_by_char_id.items():
            if char_id in self.characters:
                self.characters[char_id].stories = sorted(stories, key=lambda s: s.id)

    def _parse_voice_lines(self):
        """Parses VoiceAtlas.json and attaches voice lines to characters."""
        voice_data = self.loader.get_json("VoiceAtlas.json")
        if not voice_data:
            return
            
        voices_by_char_id = defaultdict(list)
        for voice_info in voice_data:
            char_id = voice_info.get("AvatarID")
            voice_id = voice_info.get("VoiceID")
            title_hash = voice_info.get("VoiceTitle", {}).get("Hash")
            text_hash = voice_info.get("Voice_M", {}).get("Hash")
            if not char_id or not voice_id or not title_hash or not text_hash:
                continue

            title = self.text_map_service.get(str(title_hash))
            text = self.text_map_service.get(str(text_hash))

            if title and text:
                voices_by_char_id[char_id].append(CharacterVoiceLine(id=voice_id, title=title, text=text))
        
        for char_id, voices in voices_by_char_id.items():
            if char_id in self.characters:
                self.characters[char_id].voice_lines = sorted(voices, key=lambda v: v.id)