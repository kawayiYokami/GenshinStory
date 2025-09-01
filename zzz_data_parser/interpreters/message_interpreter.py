from typing import Dict, List, Optional
from ..models.message import Message, MessageOption, MessageSession
from ..dataloader import ZZZDataLoader


class MessageInterpreter:
    """
    Interpreter for parsing phone message data from the game's configuration and text maps.
    """

    def __init__(self):
        """
        Initializes the interpreter by loading the text map, message config, and NPC config data.
        """
        self.data_loader = ZZZDataLoader()
        self.text_map = self.data_loader.get_text_map()
        self.message_npc_config = self.data_loader.get_message_npc_config()

    def parse(self) -> List[MessageSession]:
        """
        Parses all phone messages from the configuration files and groups them into sessions.

        Returns:
            A list of MessageSession objects, each representing a complete conversation.
        """
        message_config = self.data_loader.get_message_config()
        if not message_config:
            return []

        # Step 1: Parse individual messages as before
        messages = []
        for message_id, config in message_config.items():
            # Determine if it's a player message based on POAKMNJMIAJ
            session_npc_id = config.get('POAKMNJMIAJ')
            is_player_message = (session_npc_id == 0)
            sender_name = "玩家" if is_player_message else ""

            # Get the actual message text
            message_text = ""
            if config.get('text_key'):
                message_text = self.text_map.get(config['text_key'], '')

            # Get session NPC name if session_npc_id is available and it's an NPC message
            session_npc_name = ""
            # session_npc_id is already determined above
            if session_npc_id and self.message_npc_config:
                npc_info = self.message_npc_config.get(session_npc_id)
                if npc_info and npc_info.get('LNCODBGHFKM'):
                    session_npc_name = self.text_map.get(npc_info['LNCODBGHFKM'], f"NPC_{session_npc_id}")

            # If it's an NPC message, set the sender name to the session NPC name
            if not is_player_message:
                sender_name = session_npc_name

            # Parse options
            options = []
            for option_data in config.get('options', []):
                option = MessageOption(
                    text_key=option_data.get('text_key'),
                    long_text_key=option_data.get('long_text_key'),
                    next_message_id=option_data.get('next_message_id')
                )
                options.append(option)

            message = Message(
                id=message_id,
                group_id=config.get('group_id', 0),
                text_key=config.get('text_key'),
                sequence=config.get('sequence', 0),
                options=options,
                is_player_message=is_player_message,
                sender_name=sender_name,
                session_npc_id=session_npc_id,
                session_npc_name=session_npc_name
            )
            messages.append(message)

        # Step 2: Group messages by group_id
        session_dict: Dict[int, List[Message]] = {}
        for message in messages:
            group_id = message.group_id
            if group_id not in session_dict:
                session_dict[group_id] = []
            session_dict[group_id].append(message)

        # Step 3: Create MessageSession objects
        message_sessions = []
        for group_id, session_messages in session_dict.items():
            # Sort messages by sequence
            session_messages.sort(key=lambda m: m.sequence)

            # Infer main_npc_id and main_npc_name
            # Find the first non-player message to get NPC info
            main_npc_id: Optional[int] = None
            main_npc_name: str = ""
            for msg in session_messages:
                if not msg.is_player_message:
                    main_npc_id = msg.session_npc_id
                    main_npc_name = msg.session_npc_name
                    break # Use the first NPC message's info

            # Create MessageSession
            message_session = MessageSession(
                session_id=group_id,
                messages=session_messages,
                main_npc_id=main_npc_id,
                main_npc_name=main_npc_name
            )
            message_sessions.append(message_session)

        return message_sessions