"""
Module for formatting Session objects into various output formats, primarily Markdown.
This formatter implements a simple, nested list structure with anchor links
to represent the branching conversation flow, as preferred by the user.
"""

from typing import Dict, Any, List
from ..parsers.session_parser import Session, Stage, Message, PlayerOptions, Option


class SessionFormatter:
    """
    Formatter for converting Session objects into various output formats.
    """

    @staticmethod
    def _format_message(message: Message) -> str:
        """
        Formats a single Message into a string line.

        Args:
            message: The Message object to format.

        Returns:
            A formatted string line representing the message.
        """
        # Speaker name is already resolved by SessionParser
        speaker_display = f"**{message.speaker_name}**" if message.speaker_name else "**[未知发送者]**"
        # Message text is already resolved by SessionParser
        message_text = message.text if message.text else "[无文本]"

        return f"{speaker_display}: {message_text}"

    @staticmethod
    def _format_option(option: Option, index: int) -> str:
        """
        Formats a single Option into a string line.

        Args:
            option: The Option object to format.
            index: The 1-based index of the option.

        Returns:
            A formatted string line representing the option.
        """
        # Option text is already resolved and combined by SessionParser
        option_text = option.text if option.text else "[无文本]"
        # Create an anchor link to the target stage
        target_anchor = f"#stage-{option.jump_to_sequence_id}"

        return f"{index}. {option_text} -> **跳转到 [阶段 {option.jump_to_sequence_id}]({target_anchor})**"

    @staticmethod
    def _format_player_options(player_options: PlayerOptions) -> List[str]:
        """
        Formats a PlayerOptions object into a list of string lines.

        Args:
            player_options: The PlayerOptions object to format.

        Returns:
            A list of formatted string lines representing the player options.
        """
        lines = []

        # Add a header for options
        lines.append("> **选项分支**:")

        # Format each option
        for i, option in enumerate(player_options.options, 1):
            lines.append(SessionFormatter._format_option(option, i))

        # Add unlocks condition if present
        if player_options.unlocks_condition:
            lines.append(f"  - `(解锁条件: {player_options.unlocks_condition})`")

        return lines

    @staticmethod
    def _format_stage(stage: Stage) -> List[str]:
        """
        Formats a single Stage into a list of string lines.

        Args:
            stage: The Stage object to format.

        Returns:
            A list of formatted string lines representing the stage.
        """
        lines = []

        # Add a separator and stage header with an anchor
        lines.append("---")
        lines.append(f"<a id=\"stage-{stage.sequence_id}\"></a>")
        lines.append(f"### 阶段 {stage.sequence_id}")
        lines.append("") # Blank line after header

        # Format messages if present
        if stage.messages:
            for message in stage.messages:
                # Only add message line if it has text
                if message.text:
                    lines.append(SessionFormatter._format_message(message))
                    # Add unlocks condition if present for the message
                    if message.unlocks_condition:
                        lines.append(f"  - `(解锁条件: {message.unlocks_condition})`")
            lines.append("") # Blank line after messages

        # Format player options if present
        if stage.player_options:
            option_lines = SessionFormatter._format_player_options(stage.player_options)
            lines.extend(option_lines)
            lines.append("") # Blank line after options

        # Handle end signal
        if stage.is_end_signal:
            lines.append("*会话结束*")
            lines.append("") # Blank line after end signal

        return lines

    @staticmethod
    def to_markdown(session: Session) -> str:
        """
        Formats a Session object into a Markdown string using a nested list structure
        with anchor links for navigation.

        Args:
            session: The Session object to format.

        Returns:
            A Markdown formatted string representing the entire session.
        """
        lines = []

        # Header with session metadata
        lines.append(f"# 会话: {session.session_id} - {session.main_npc_name}")
        lines.append("") # Blank line after header

        # Sort stages by sequence_id to ensure correct order
        sorted_stages = sorted(session.stages.items())

        # Iterate through stages and format them
        for sequence_id, stage in sorted_stages:
            stage_lines = SessionFormatter._format_stage(stage)
            lines.extend(stage_lines)

        # Remove the trailing blank line if it exists
        if lines and lines[-1] == "":
            lines.pop()

        return "\n".join(lines)