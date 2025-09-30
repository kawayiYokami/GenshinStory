import logging
from typing import List, Dict, Optional
from hsrwiki_data_parser.models.message import Message, MessageThread
from hsrwiki_data_parser.services.game_data_loader import GameDataLoader
from hsrwiki_data_parser.services.text_map_service import TextMapService
from hsrwiki_data_parser.utils.text_transformer import TextTransformer

class MessageInterpreter:
    def __init__(self, loader: GameDataLoader, text_map_service: TextMapService):
        self.loader = loader
        self.text_map = text_map_service
        self.text_transformer = TextTransformer()
        logging.info("Initializing MessageInterpreter...")

        self.contacts_by_id = self._build_contact_map()

        self.items_by_id = {item.get('ID'): item for item in (self.loader.get_message_items() or [])}
        self.sections_by_id = {sec.get('ID'): sec for sec in (self.loader.get_message_sections() or [])}
        self.groups_by_id = {group.get('ID'): group for group in (self.loader.get_messages() or [])}

        logging.info(f"Loaded {len(self.contacts_by_id)} contacts.")
        logging.info(f"Loaded {len(self.items_by_id)} message items.")
        logging.info(f"Loaded {len(self.sections_by_id)} message sections.")
        logging.info(f"Loaded {len(self.groups_by_id)} message groups.")

    def _build_contact_map(self) -> Dict[int, str]:
        """Reads contact data and builds a simple ID -> Name dictionary."""
        contacts_map = {}
        contacts_data = self.loader.get_message_contacts() or []
        for contact in contacts_data:
            contact_id = contact.get('ID')
            name_hash = contact.get('Name', {}).get('Hash')
            if contact_id and name_hash:
                contact_name = self.text_map.get_text(name_hash)
                if contact_name:
                    contacts_map[contact_id] = self.text_transformer.transform(contact_name)
        return contacts_map

    def interpret_one(self, group_id: int) -> Optional[MessageThread]:
        group_data = self.groups_by_id.get(group_id)
        if not group_data:
            logging.error(f"Group ID {group_id} not found.")
            return None

        logging.info(f"Processing Group ID: {group_id} with data: {group_data}")

        # Get the main contact for the entire thread from the group data
        main_contact_id = group_data.get('MessageContactsID')
        main_contact_name = self.contacts_by_id.get(main_contact_id, "未知联系人")
        trailblazer_name = "开拓者"

        messages: List[Message] = []
        participant_names = set()

        for section_id in group_data.get('MessageSectionIDList', []):
            section_data = self.sections_by_id.get(section_id)
            if not section_data:
                logging.warning(f"Section ID {section_id} not found for group {group_id}.")
                continue

            logging.info(f"  Processing Section ID: {section_id} with data: {section_data}")
            current_item_id = section_data.get('StartMessageItemIDList', [None])[0]
            while current_item_id:
                item_data = self.items_by_id.get(current_item_id)
                if not item_data:
                    logging.warning(f"    Item ID {current_item_id} not found.")
                    break

                # Determine sender based on the 'Sender' field
                sender_type = item_data.get('Sender')
                sender_name = "未知"
                if sender_type == 'Player' or sender_type == 'PlayerAuto':
                    sender_name = trailblazer_name
                elif sender_type == 'NPC':
                    sender_name = main_contact_name

                if sender_name and sender_name != "未知":
                    participant_names.add(sender_name)

                text_hash = item_data.get('MainText', {}).get('Hash')
                text = self.text_map.get_text(text_hash)

                if text:
                    text = self.text_transformer.transform(text)
                    messages.append(Message(id=current_item_id, sender=sender_name, text=text))

                next_ids = item_data.get('NextItemIDList', [])
                current_item_id = next_ids[0] if next_ids else None

        if not messages:
            logging.error(f"No messages were successfully parsed for group {group_id}.")
            return None

        other_participants = sorted(list(participant_names - {trailblazer_name}))

        if other_participants:
            thread_name = ", ".join(other_participants)
        elif trailblazer_name in participant_names:
            thread_name = trailblazer_name
        else:
            thread_name = main_contact_name if main_contact_name != "未知联系人" else "未知对话"

        return MessageThread(id=group_id, name=f"与 {thread_name} 的短信", messages=messages)

    def interpret_all(self) -> List[MessageThread]:
        all_threads = []
        for group_id in self.groups_by_id.keys():
            thread = self.interpret_one(group_id)
            if thread:
                all_threads.append(thread)
        return all_threads
