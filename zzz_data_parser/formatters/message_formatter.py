from typing import Dict, Any, List
from ..models.message import Message, MessageOption, MessageSession


class MessageFormatter:
    """
    Formatter for converting Message objects into various output formats.
    """

    @staticmethod
    def _format_option(option: MessageOption, index: int, text_map: Dict[str, str]) -> str:
        """
        Formats a single MessageOption into a string.

        Args:
            option: The MessageOption to format.
            index: The index of the option (1-based).
            text_map: The text map to look up option text.

        Returns:
            A formatted string representing the option.
        """
        lines = []
        # Get the main text
        main_text = ""
        if option.text_key:
            main_text = text_map.get(option.text_key, option.text_key) # Fallback to key if not found

        # Get the long text
        long_text = ""
        if option.long_text_key:
            long_text = text_map.get(option.long_text_key, option.long_text_key) # Fallback to key if not found

        # Combine main and long text
        combined_text = main_text
        if long_text:
            combined_text = f"{main_text} ({long_text})" if main_text else long_text

        if combined_text:
            lines.append(f"  {index}. {combined_text}")
        else:
            lines.append(f"  {index}. [无文本]")

        if option.next_message_id:
            lines.append(f"     -> 跳转到消息 ID: {option.next_message_id}")

        return "\n".join(lines)

    @staticmethod
    def to_chat(message_session: MessageSession, text_map: Dict[str, str]) -> str:
        """
        Formats a MessageSession object into a simple chat string.

        Args:
            message_session: The MessageSession object to format.
            text_map: The text map to look up message and option text.

        Returns:
            A simple chat formatted string representing the entire message session.
        """
        lines = []

        # Iterate through messages in the session
        for message in message_session.messages:
            # Get message content
            message_text = ""
            if message.text_key:
                message_text = text_map.get(message.text_key, f"[文本未找到: {message.text_key}]")

            # Format the line as "Sender: Message"
            if message_text:  # Only add line if there's content
                sender_display = message.sender_name if message.sender_name else "[未知发送者]"
                lines.append(f"{sender_display}：{message_text}")

        return "\n".join(lines)

    @staticmethod
    def to_markdown(message_session: MessageSession, text_map: Dict[str, str]) -> str:
        """
        Formats a MessageSession object into a Markdown string.

        Args:
            message_session: The MessageSession object to format.
            text_map: The text map to look up message and option text.

        Returns:
            A Markdown formatted string representing the entire message session.
        """
        lines = []

        # Header with session metadata
        lines.append(f"# 短信会话 ID: {message_session.session_id}")
        lines.append(f"主要NPC: {message_session.main_npc_name or '[无]'}")
        lines.append("")

        # Iterate through messages in the session
        for message in message_session.messages:
            # Get message content
            message_text = ""
            if message.text_key:
                message_text = text_map.get(message.text_key, f"[文本未找到: {message.text_key}]")

            # Format the line as "**Sender**: Message"
            if message_text:  # Only add line if there's content
                sender_display = f"**{message.sender_name}**" if message.sender_name else "**[未知发送者]**"
                lines.append(f"{sender_display}：{message_text}")

            # Options, if any (keeping the existing option formatting)
            if message.options:
                lines.append("")  # Add a blank line before options
                lines.append("### 选项")
                for i, option in enumerate(message.options, 1):
                    option_str = MessageFormatter._format_option(option, i, text_map)
                    lines.append(option_str)
                lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_dict(message_session: MessageSession, text_map: Dict[str, str]) -> Dict[str, Any]:
        """
        Converts a MessageSession object into a dictionary, including resolved text for all messages.

        Args:
            message_session: The MessageSession object to convert.
            text_map: The text map to look up message and option text.

        Returns:
            A dictionary representation of the entire message session.
        """
        # Helper function to convert a single message to dict (similar to old logic)
        def _message_to_dict(message: Message) -> Dict[str, Any]:
            # Get the actual message text
            message_text = ""
            if message.text_key:
                message_text = text_map.get(message.text_key, f"[文本未找到: {message.text_key}]")

            # Convert options to dicts
            options_data = []
            for option in message.options:
                option_text = ""
                if option.text_key:
                    option_text = text_map.get(option.text_key, option.text_key)

                option_long_text = ""
                if option.long_text_key:
                    option_long_text = text_map.get(option.long_text_key, option.long_text_key)

                options_data.append({
                    "text": option_text,
                    "long_text": option_long_text,
                    "next_message_id": option.next_message_id
                })

            return {
                "id": message.id,
                "group_id": message.group_id,
                "text_key": message.text_key,
                "text": message_text,
                "sequence": message.sequence,
                "options": options_data,
                "is_player_message": message.is_player_message,
                "sender_name": message.sender_name,
                "session_npc_id": message.session_npc_id,
                "session_npc_name": message.session_npc_name
            }

        # Convert all messages in the session
        messages_data = [_message_to_dict(msg) for msg in message_session.messages]

        return {
            "session_id": message_session.session_id,
            "main_npc_id": message_session.main_npc_id,
            "main_npc_name": message_session.main_npc_name,
            "messages": messages_data
        }