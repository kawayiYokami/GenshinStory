from typing import List, Dict, Optional, Any
from ..dataloader import ZZZDataLoader
from ..models.session import Session, Message
from ..formatters.session_formatter import SessionFormatter

class SessionService:
    """
    Service layer for accessing phone message data.
    This service handles parsing and caching of phone message data using the new Session model.
    """

    _instance: Optional['SessionService'] = None
    _sessions: Optional[List[Session]] = None
    _session_map: Optional[Dict[int, Session]] = None
    # Keep the old message map for backward compatibility if needed
    _message_map: Optional[Dict[int, Message]] = None

    def __new__(cls) -> 'SessionService':
        """
        Singleton pattern implementation. Ensures only one instance of the service exists.
        """
        if cls._instance is None:
            cls._instance = super(SessionService, cls).__new__(cls)
        return cls._instance

    def _load_data(self) -> None:
        """
        Loads and parses phone message data using the ZZZDataLoader.
        This method initializes the internal cache of message sessions.
        """
        if self._sessions is None:
            data_loader = ZZZDataLoader(gender='M', player_name='哲')
            self._sessions = data_loader.get_message_sessions()

            if self._sessions is not None:
                # Create a map for quick session ID-based lookups
                self._session_map = {session.session_id: session for session in self._sessions}

                # Create a map for quick individual message ID-based lookups (backward compatibility)
                self._message_map = {}
                for session in self._sessions:
                    for stage in session.stages.values():
                        for message in stage.messages:
                            # Use message_id as the key
                            self._message_map[message.message_id] = message
                        # Player options also have a message_id
                        if stage.player_options:
                            self._message_map[stage.player_options.message_id] = Message(
                                message_id=stage.player_options.message_id,
                                speaker_id=0,  # Placeholder
                                speaker_name="[选项]",
                                text="选项消息"
                            )

    def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """
        Retrieves a phone message by its unique ID.
        This method is kept for backward compatibility.

        Args:
            message_id: The ID of the message to retrieve.

        Returns:
            The Message object if found, otherwise None.
        """
        self._load_data()
        return self._message_map.get(message_id)

    def get_all_sessions(self) -> List[Session]:
        """
        Retrieves all parsed phone message sessions.

        Returns:
            A list of Session objects.
        """
        self._load_data()
        return self._sessions if self._sessions is not None else []

    def get_session_by_id(self, session_id: int) -> Optional[Session]:
        """
        Retrieves a phone message session by its session ID (group_id).

        Args:
            session_id: The ID of the session to retrieve.

        Returns:
            The Session object if found, otherwise None.
        """
        self._load_data()
        return self._session_map.get(session_id) if self._session_map else None

    def list_message_ids(self) -> List[int]:
        """
        Retrieves a list of all available phone message IDs.

        Returns:
            A list of message IDs.
        """
        self._load_data()
        return list(self._message_map.keys()) if self._message_map else []

    def get_session_as_markdown(self, session_id: int) -> str:
        """
        Generate a markdown representation of a session.

        Args:
            session_id: The ID of the session.

        Returns:
            A markdown string representing the session.
        """
        session = self.get_session_by_id(session_id)
        if not session:
            return f"# Session {session_id} not found"

        # Delegate to SessionFormatter to produce a consistent, full-featured markdown
        try:
            return SessionFormatter.to_markdown(session)
        except Exception:
            # Fallback to a simple representation if formatter fails
            markdown = f"# {session.main_npc_name}\n\n"
            markdown += f"**Session ID**: {session.session_id}\n\n"
            markdown += f"**Main NPC ID**: {session.main_npc_id}\n\n"
            markdown += "## Stages\n\n"

            for sequence_id in sorted(session.stages.keys()):
                stage = session.stages[sequence_id]
                markdown += f"### Stage {sequence_id}\n\n"
                for message in stage.messages:
                    markdown += f"**{message.speaker_name}**: {message.text}\n\n"

                # Add player options if any
                if stage.player_options:
                    markdown += "Player Options:\n"
                    for option in stage.player_options.options:
                        text = option.long_text if option.long_text else option.text
                        markdown += f"- {text} (Jump to: {option.jump_to_sequence_id})\n"
                    markdown += "\n"

            return markdown

    def get_tree(self) -> List[Dict[str, Any]]:
        """
        Generate a tree structure for sessions, categorized by main NPC name.

        Returns:
            A list of dictionaries representing the tree structure.
        """
        self._load_data()
        if not self._sessions:
            return []

        # Group sessions by main NPC name
        npc_sessions: Dict[str, List[Dict[str, Any]]] = {}

        for session in self._sessions:
            display_name = session.main_npc_name

            if display_name not in npc_sessions:
                npc_sessions[display_name] = []

            npc_sessions[display_name].append({
                "id": session.session_id,
                "name": display_name,
                "type": "session"
            })

        # Convert to the required format
        tree = []
        for npc_name, sessions in npc_sessions.items():
            tree.append({
                "name": npc_name,
                "children": sessions
            })

        return tree