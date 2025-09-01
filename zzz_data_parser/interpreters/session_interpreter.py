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
        npc_data = None
        for item in self.npc_config.get("PDHBFPILAJD", []):
            # NPC config IDs are numeric; compare with int
            if item.get("CJHNGFMGKGE") == npc_id_int:
                npc_data = item
                break

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

        Returns:
            A list of Session objects.
        """
        # 1. Group messages by SessionId (IIBGABOLBDI in raw data)
        sessions_data: Dict[int, List[Dict]] = defaultdict(list)
        for msg in raw_messages:
            session_id = msg.get("IIBGABOLBDI")
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
            npc_id = msg.get("POAKMNJMIAJ", 0) # NpcId in raw data
            if npc_id != 0:
                main_npc_id = npc_id
                break # Found the first NPC ID

        # Resolve the NPC name using the NPC config if available, otherwise use a placeholder
        main_npc_name = self._get_npc_name_by_id(main_npc_id)

        session = Session(session_id, main_npc_id, main_npc_name)

        # 2. Group messages by Sequence No. within the session (BKOAPELPEGL in raw data)
        stages_data: Dict[int, List[Dict]] = defaultdict(list)
        for msg in raw_messages:
            sequence_id = msg.get("BKOAPELPEGL")
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

        # Determine stage type from the first message's UnknownId1 (AAJNLGHFKID in raw data)
        # (Assumption: All messages in a stage share the same type)
        msg_type = raw_messages[0].get("AAJNLGHFKID", -1)

        if msg_type == self.MSG_TYPE_NPC_DIALOG:
            stage.messages = [self._create_message(msg) for msg in raw_messages]
            # Check for unlocks_condition on any message in the stage
            for msg in raw_messages:
                if msg.get("UnknownId2", 0) != 0:
                    # Apply to the first message that has it, or create a dummy if none exist yet
                    # A more robust way might be to store it on the stage itself if it's stage-wide.
                    # For now, attaching to the first message in the list.
                    if stage.messages:
                         stage.messages[0].unlocks_condition = msg["UnknownId2"]
                    break # Assume only one relevant unlock per stage for simplicity

        elif msg_type == self.MSG_TYPE_PLAYER_OPTIONS:
            # There should typically be one message representing the options group
            if raw_messages:
                options_msg = raw_messages[0] # Take the first one
                stage.player_options = self._create_player_options(options_msg)
            else:
                # Handle empty stage data gracefully
                stage.player_options = PlayerOptions(message_id=0, options=[])

        elif msg_type == self.MSG_TYPE_END_SIGNAL:
            stage.is_end_signal = True
            # Check for unlocks_condition on the end signal message
            if raw_messages and raw_messages[0].get("UnknownId2", 0) != 0:
                # This is a bit ambiguous. An end signal with an unlock?
                # We'll store it on a dummy message or the stage itself conceptually.
                # For now, we just note the stage is an end signal.
                pass
        else:
            # Log or handle unknown message types if necessary
            # For simplicity, treat as NPC dialog
            stage.messages = [self._create_message(msg) for msg in raw_messages]

        return stage

    def _create_message(self, raw_msg: Dict) -> Message:
        """Creates a Message object from a raw message dict."""
        text_key = raw_msg.get("DECDHOMFHKM") # TextKey in raw data
        text = self.text_map.get(text_key, "") if text_key else ""
        # LongTextKey is typically for options, but might exist for messages?
        # Let's prioritize TextKey. If you find cases where LongTextKey is primary for messages, adjust.
        # For now, we'll add it as a note if it exists and is different.
        # This logic can be refined based on data observation.

        # Resolve NPC name using the dedicated method
        speaker_id = raw_msg.get("POAKMNJMIAJ", 0) # NpcId in raw data
        if speaker_id == 0 and text:
            speaker_name = "???"
        elif speaker_id == 0:
            speaker_name = "[玩家]"
        else:
            speaker_name = self._get_npc_name_by_id(speaker_id)

        return Message(
            message_id=raw_msg["CJHNGFMGKGE"], # MessageId in raw data
            speaker_id=speaker_id,
            speaker_name=speaker_name,
            text=text
            # unlocks_condition is handled in _interpret_stage
        )

    def _create_player_options(self, raw_msg: Dict) -> PlayerOptions:
        """Creates a PlayerOptions object from a raw message dict."""
        options = []

        # --- Option 1 ---
        opt1_text_key = raw_msg.get("PJILMILDDBN") # TextKey for option 1
        opt1_long_text_key = raw_msg.get("ODCPPAKEEPM") # LongTextKey for option 1
        opt1_jump_id = raw_msg.get("PFEFHIBHJDL") # Jump ID for option 1

        if opt1_text_key or opt1_long_text_key: # Only add if there's some text
            opt1_text = self.text_map.get(str(opt1_text_key), "") if opt1_text_key else ""
            opt1_long_text = self.text_map.get(str(opt1_long_text_key), "") if opt1_long_text_key else None
            # Combine texts if both exist, or use the one that exists
            combined_text_1 = (opt1_text + " " + opt1_long_text).strip() if opt1_long_text else opt1_text
            if combined_text_1: # Only add option if final text is not empty
                 options.append(Option(
                    text=combined_text_1,
                    long_text=opt1_long_text,
                    jump_to_sequence_id=opt1_jump_id
                ))

        # --- Option 2 ---
        opt2_text_key = raw_msg.get("LEACGIIJHHO") # TextKey for option 2
        opt2_long_text_key = raw_msg.get("NGADKHLFKDI") # LongTextKey for option 2
        opt2_jump_id = raw_msg.get("KBIFFIEJJMO") # Jump ID for option 2

        if opt2_text_key or opt2_long_text_key: # Only add if there's some text
            opt2_text = self.text_map.get(str(opt2_text_key), "") if opt2_text_key else ""
            opt2_long_text = self.text_map.get(str(opt2_long_text_key), "") if opt2_long_text_key else None
            # Combine texts if both exist, or use the one that exists
            combined_text_2 = (opt2_text + " " + opt2_long_text).strip() if opt2_long_text else opt2_text
            if combined_text_2: # Only add option if final text is not empty
                options.append(Option(
                    text=combined_text_2,
                    long_text=opt2_long_text,
                    jump_to_sequence_id=opt2_jump_id
                ))

        unlocks_condition = raw_msg.get("AFNINBBDCOF") if raw_msg.get("AFNINBBDCOF", 0) != 0 else None # UnknownId2 in raw data

        return PlayerOptions(
            message_id=raw_msg["CJHNGFMGKGE"], # MessageId in raw data
            options=options,
            unlocks_condition=unlocks_condition
        )