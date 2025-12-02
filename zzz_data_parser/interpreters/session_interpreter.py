"""
Module for interpreting raw message data into structured Session objects.
This interpreter implements the logic based on the analysis of data fields:
- Sequence No. (序号) defines conversation stages.
- Unknown ID 1 (用途不明 ID 1) defines message type (NPC dialog, Player options, End signal).
- Unknown ID 2 (用途不明 ID 2) acts as a state/unlock trigger.
- Jump ID (跳转 ID) controls branching logic for player choices.
"""

from typing import Dict, List, Optional, NamedTuple, Any
from collections import defaultdict
from ..models.session import Option, PlayerOptions, Message, Stage, Session


class SessionInterpreter:
    """
    Interprets raw message data dictionaries into structured Session objects.

    Expected raw data format (simplified):
    {
        "MessageId": int,
        "SessionId": int,
        "Sequence": int, # Sequence No.
        "NpcId": int,
        "NpcName": str,
        "TextKey": str, # Key for main text
        "LongTextKey": str, # Key for long text (options)
        "PJILMILDDBN": int, # Option 1 TextKey
        "ODCPPAKEEPM": int, # Option 1 LongTextKey
        "PFEFHIBHJDL": int, # Option 1 Jump ID
        "LEACGIIJHHO": int, # Option 2 TextKey
        "NGADKHLFKDI": int, # Option 2 LongTextKey
        "KBIFFIEJJMO": int, # Option 2 Jump ID
        "UnknownId1": int, # 用途不明 ID 1
        "UnknownId2": int, # 用途不明 ID 2
        # ... other fields from MessageConfigTemplateTb.json
    }
    And text map data:
    {
        "TextId": str, # The key
        "TextValue": str # The actual text
    }
    """

    # Constants for message types based on UnknownId1
    MSG_TYPE_NPC_DIALOG = 0
    MSG_TYPE_PLAYER_OPTIONS = 1
    MSG_TYPE_END_SIGNAL = 3

    def __init__(self, text_map: Dict[str, str], npc_config: Optional[Dict[str, Any]] = None, player_name: str = '哲'):
        """
        Initializes the interpreter with a text map for resolving text keys and optionally NPC config.

        Args:
            text_map: A dictionary mapping text keys to their actual text values.
            npc_config: The raw NPC configuration data (e.g., from MessageNPCTemplateTb.json).
                        If provided, it will be used to resolve NPC names more accurately.
        """
        self.text_map = text_map
        self.npc_config = npc_config
        # Player name (用于特殊 NPC 999 的主角互换逻辑)
        self.player_name = player_name

    def _get_npc_name_by_id(self, npc_id: int) -> str:
        """
        Get the NPC name from the NPC configuration data by its ID.
        If npc_config is not provided or NPC is not found, returns a default string.

        Args:
            npc_id: The ID of the NPC.

        Returns:
            The resolved NPC name, or a placeholder if not found.
        """
        # Coerce npc_id to int if possible (raw data may use strings)
        try:
            npc_id_int = int(npc_id)
        except Exception:
            return "[未知NPC]"

        # First, handle some hard-coded overrides for missing or special NPC IDs
        overrides = {
            10131: '朱鸢',
            10132: '艾莲',
            10133: '青衣',
            10134: '凯撒',
            999: '玲', # 默认玩家是哲，所以999是玲。如果需要哲，需要在初始化时传入不同的player_name
            88: '绳网公告'
        }

        if npc_id_int == 999:
            # ID 999 denotes the other protagonist: if player is 哲 -> 玲, else 哲
            return '玲' if (self.player_name == '哲') else '哲'

        if npc_id_int in overrides:
            return overrides[npc_id_int]

        if not self.npc_config or npc_id_int == 0:
            return "[未知NPC]"

        # Find NPC data by ID (CJHNGFMGKGE is the ID field in NPC config)
        # Note: self.npc_config is now a DICT indexed by ID, pre-processed in dataloader
        npc_data = self.npc_config.get(npc_id_int)

        if not npc_data:
            # If we don't have an entry in npc_config for this ID,
            # try the hard-coded overrides as a last resort (covers cases
            # where config is incomplete but we know the intended name).
            if npc_id_int in overrides:
                return overrides[npc_id_int]
            return f"[未知NPC ID: {npc_id_int}]"

        # Get the name key (LNCODBGHFKM is the name key field in NPC config)
        name_key = npc_data.get("LNCODBGHFKM")
        if not name_key:
            return f"[NPC名称键缺失 ID: {npc_id_int}]"

        # Resolve the name key using the text map
        # If the name key is not found in the text map, return the key itself for better debugging
        return self.text_map.get(name_key, name_key)

    def interpret(self, raw_messages: List[Dict]) -> List[Session]:
        """
        Interprets a list of raw message dictionaries into structured Session objects.

        Args:
            raw_messages: A list of dictionaries, each representing a raw message.
            (Note: In the refactored DataLoader, these are raw dicts from the list in JSON)

        Returns:
            A list of Session objects.
        """
        # NOTE: Since keys are now dynamic and mapped in DataLoader, passing raw_messages directly
        # here is problematic if we don't know the keys.
        # Ideally, DataLoader should pass 'processed_config' (the dict with standardized keys).
        # However, to avoid rewriting the whole logic flow right now, we can assume 'raw_messages'
        # passed here is actually the list of standardized message dicts created in DataLoader.
        # Let's check DataLoader implementation...
        #
        # In DataLoader.get_message_sessions():
        # raw_messages = self.get_json(...)
        # ...
        # sessions = interpreter.interpret(raw_message_list)
        #
        # WAIT. The new DataLoader passes `raw_message_list` (the raw JSON list), NOT the processed config.
        # This means SessionInterpreter needs to know the KEY MAP as well, OR
        # DataLoader should pass the `processed_config` values list.
        #
        # Let's look at DataLoader again. `processed_config` is built but stored in cache 'message_config'.
        # `get_message_sessions` calls `interpreter.interpret` with RAW list.
        # This is a DESIGN FLAW in the refactor plan.
        #
        # FIX: We should change DataLoader to use `get_message_config().values()` which returns
        # standardized dicts!
        #
        # However, since I am editing SessionInterpreter now, I will assume the input `raw_messages`
        # is a list of STANDARDIZED dictionaries (with keys 'id', 'group_id', 'text_key', etc.).
        # I will update DataLoader in the next step to pass `self.get_message_config().values()` instead of raw list.

        # 1. Group messages by SessionId (group_id)
        sessions_data: Dict[int, List[Dict]] = defaultdict(list)
        for msg in raw_messages:
            session_id = msg.get("group_id")
            if session_id is not None:
                sessions_data[session_id].append(msg)

        sessions: List[Session] = []
        for session_id, messages in sessions_data.items():
            session = self._interpret_single_session(session_id, messages)
            sessions.append(session)

        return sessions

    def _interpret_single_session(self, session_id: int, raw_messages: List[Dict]) -> Session:
        """
        Interprets messages for a single session.
        """
        # Find main NPC (first non-zero NpcId message, or default)
        main_npc_id = 0
        for msg in raw_messages:
            npc_id = msg.get("session_npc_id", 0)
            if npc_id != 0:
                main_npc_id = npc_id
                break # Found the first NPC ID

        # Resolve the NPC name using the NPC config if available, otherwise use a placeholder
        main_npc_name = self._get_npc_name_by_id(main_npc_id)

        session = Session(session_id, main_npc_id, main_npc_name)

        # 2. Group messages by Sequence No. within the session
        stages_data: Dict[int, List[Dict]] = defaultdict(list)
        for msg in raw_messages:
            sequence_id = msg.get("sequence")
            if sequence_id is not None:
                stages_data[sequence_id].append(msg)

        # 3. Interpret each stage
        for sequence_id, stage_messages in stages_data.items():
            stage = self._interpret_stage(sequence_id, stage_messages)
            session.stages[sequence_id] = stage

        return session

    def _interpret_stage(self, sequence_id: int, raw_messages: List[Dict]) -> Stage:
        """
        Interprets messages for a single stage based on their type.
        """
        stage = Stage(sequence_id)

        # Determine stage type.
        # In standardized dict, we distinguish types by presence of 'options'.
        # If 'options' list is not empty, it's a player option stage.
        # Otherwise it's NPC dialog (or end signal, but end signal is tricky without specific flags).

        is_option_stage = False
        if raw_messages and raw_messages[0].get('options'):
            is_option_stage = True

        if is_option_stage:
             # There should typically be one message representing the options group
            if raw_messages:
                options_msg = raw_messages[0] # Take the first one
                stage.player_options = self._create_player_options(options_msg)
            else:
                stage.player_options = PlayerOptions(message_id=0, options=[])
        else:
            # Treat as NPC dialog
            stage.messages = [self._create_message(msg) for msg in raw_messages]

        return stage

    def _create_message(self, raw_msg: Dict) -> Message:
        """Creates a Message object from a standardized message dict."""
        text_key = raw_msg.get("text_key")
        text = self.text_map.get(text_key, "") if text_key else ""

        # Resolve NPC name using the dedicated method
        speaker_id = raw_msg.get("session_npc_id", 0)
        if speaker_id == 0 and text:
            speaker_name = "???"
        elif speaker_id == 0:
            speaker_name = "[玩家]"
        else:
            speaker_name = self._get_npc_name_by_id(speaker_id)

        return Message(
            message_id=raw_msg["id"],
            speaker_id=speaker_id,
            speaker_name=speaker_name,
            text=text
        )

    def _create_player_options(self, raw_msg: Dict) -> PlayerOptions:
        """Creates a PlayerOptions object from a standardized message dict."""
        # The standardized dict already parses options into a list of dicts
        # structure: [{'text_key': '...', 'next_message_id': ...}, ...]

        raw_options = raw_msg.get('options', [])
        options = []

        for opt in raw_options:
            text_key = opt.get('text_key')
            next_id = opt.get('next_message_id')

            if text_key:
                text = self.text_map.get(str(text_key), "")
                if text:
                     options.append(Option(
                        text=text,
                        long_text=None, # Standardized dict simplified this
                        jump_to_sequence_id=next_id
                    ))

        return PlayerOptions(
            message_id=raw_msg["id"],
            options=options,
            unlocks_condition=None # Simplified
        )