from typing import Dict, List, Optional
from collections import defaultdict

from ..models.message import Message, MessageThread
from ..models.character import Character
from ..services import DataLoader, TextMapService

class MessageInterpreter:
    """
    Interprets message data from MessageItemConfig.json and MessageItemLink.json,
    reconstructing full conversation threads.
    """
    def __init__(self, loader: DataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map_service = text_map_service

    def interpret_all(self, characters_by_id: Dict[int, Character]) -> List[MessageThread]:
        """
        Parses all message files and returns a list of complete MessageThread objects.
        """
        # Step 1: Pre-load titles
        titles = self._parse_titles()
        
        # Step 2: Pre-load all individual message items
        all_messages_by_id, messages_by_section = self._load_all_messages()
        
        # Step 3: Reconstruct threads
        threads = self._reconstruct_threads(all_messages_by_id, messages_by_section, titles, characters_by_id)
        
        return threads

    def _parse_titles(self) -> Dict[int, str]:
        """Loads titles from MessageItemLink.json."""
        titles = {}
        link_data = self.loader.get_json("MessageItemLink.json")
        if not link_data:
            return titles
        for link_info in link_data:
            link_id = link_info.get("ID")
            title_hash = link_info.get("Title", {}).get("Hash")
            if link_id and title_hash:
                title = self.text_map_service.get(str(title_hash))
                if title:
                    titles[link_id] = title
        return titles

    def _load_all_messages(self) -> (Dict[int, Dict], Dict[int, List[int]]):
        """Loads all messages from MessageItemConfig.json and groups them by section."""
        all_messages_by_id = {}
        messages_by_section = defaultdict(list)
        
        message_data = self.loader.get_json("MessageItemConfig.json")
        if not message_data:
            return all_messages_by_id, messages_by_section

        for msg_info in message_data:
            msg_id = msg_info.get("ID")
            section_id = msg_info.get("SectionID")
            if msg_id and section_id:
                all_messages_by_id[msg_id] = msg_info
                messages_by_section[section_id].append(msg_id)
        
        return all_messages_by_id, messages_by_section

    def _reconstruct_threads(self, all_messages_by_id: Dict, messages_by_section: Dict, titles: Dict, characters_by_id: Dict[int, Character]) -> List[MessageThread]:
        """Builds conversation threads from the loaded message data."""
        threads = []
        
        # Find the starting message for each section
        # A simple approach: find messages that are not in any "NextItemIDList"
        all_next_ids = set()
        for msg in all_messages_by_id.values():
            for next_id in msg.get("NextItemIDList", []):
                all_next_ids.add(next_id)

        for section_id, message_ids in messages_by_section.items():
            start_node_id = None
            for msg_id in message_ids:
                if msg_id not in all_next_ids:
                    start_node_id = msg_id
                    break
            
            if start_node_id is None: # Fallback for cyclic or single-message threads
                start_node_id = message_ids[0]

            # Reconstruct the thread from the starting node
            current_id: Optional[int] = start_node_id
            thread_messages: List[Message] = []
            
            first_msg_data = all_messages_by_id.get(start_node_id, {})
            contact_id = first_msg_data.get("ContactsID", 0)
            
            while current_id is not None:
                msg_data = all_messages_by_id.get(current_id)
                if not msg_data:
                    break
                
                text_hash = msg_data.get("MainText", {}).get("Hash")
                text = self.text_map_service.get(str(text_hash)) or ""
                
                thread_messages.append(Message(
                    id=current_id,
                    sender=msg_data.get("Sender", "Unknown"),
                    text=text
                ))
                
                next_ids = msg_data.get("NextItemIDList", [])
                current_id = next_ids[0] if next_ids else None
            
            if thread_messages:
                thread_title = titles.get(section_id, f"Section {section_id}")
                contact_character = characters_by_id.get(contact_id)
                contact_name = contact_character.name if contact_character else f"Unknown Contact ({contact_id})"

                threads.append(MessageThread(
                    id=section_id,
                    contact_id=contact_id,
                    contact_name=contact_name,
                    title=thread_title,
                    messages=thread_messages
                ))
        
        return threads