from typing import List, Dict, Optional
from ..interpreters.message_interpreter import MessageInterpreter
from ..models.message import Message, MessageSession


class MessageService:
    """
    Service layer for accessing phone message data.
    This service handles parsing and caching of phone message data.
    """

    _instance: Optional['MessageService'] = None
    _sessions: Optional[List[MessageSession]] = None
    _session_map: Optional[Dict[int, MessageSession]] = None
    # Keep the old message map for backward compatibility if needed
    _message_map: Optional[Dict[int, Message]] = None

    def __new__(cls) -> 'MessageService':
        """
        Singleton pattern implementation. Ensures only one instance of the service exists.
        """
        if cls._instance is None:
            cls._instance = super(MessageService, cls).__new__(cls)
        return cls._instance

    def _load_data(self) -> None:
        """
        Loads and parses phone message data using the MessageInterpreter.
        This method initializes the internal cache of message sessions.
        """
        if self._sessions is None:
            interpreter = MessageInterpreter()
            self._sessions = interpreter.parse()
            # Create a map for quick session ID-based lookups
            self._session_map = {session.session_id: session for session in self._sessions}

            # Create a map for quick individual message ID-based lookups (backward compatibility)
            self._message_map = {}
            for session in self._sessions:
                for message in session.messages:
                    self._message_map[message.id] = message

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

    def get_all_sessions(self) -> List[MessageSession]:
        """
        Retrieves all parsed phone message sessions.

        Returns:
            A list of MessageSession objects.
        """
        self._load_data()
        return self._sessions if self._sessions is not None else []

    def get_session_by_id(self, session_id: int) -> Optional[MessageSession]:
        """
        Retrieves a phone message session by its session ID (group_id).

        Args:
            session_id: The ID of the session to retrieve.

        Returns:
            The MessageSession object if found, otherwise None.
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