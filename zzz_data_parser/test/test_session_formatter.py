#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to output a session formatted in Markdown.
This script uses the ZZZDataLoader to load session data and the SessionFormatter to format it.
It will first try to find a session with options. If not found, it will find a session with speaker_id=0 and text.
If still not found, it will output a random session.
"""

import sys
import os
import random

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from zzz_data_parser.dataloader import ZZZDataLoader
from zzz_data_parser.formatters.session_formatter import SessionFormatter


def has_options(session):
    """Check if a session has any options."""
    for stage in session.stages.values():
        if stage.player_options and stage.player_options.options:
            return True
    return False


def has_unknown_speaker_with_text(session):
    """Check if a session has any message with speaker_id=0 and non-empty text."""
    for stage in session.stages.values():
        for message in stage.messages:
            if message.speaker_id == 0 and message.text:
                return True
    return False


def find_session(sessions):
    """Find a session based on priority: options, unknown speaker with text, random."""
    # Priority 1: Session with options
    sessions_with_options = [s for s in sessions if has_options(s)]
    if sessions_with_options:
        print("Found session with options.")
        return random.choice(sessions_with_options)

    # Priority 2: Session with unknown speaker (speaker_id=0) and text
    sessions_with_unknown_speaker = [s for s in sessions if has_unknown_speaker_with_text(s)]
    if sessions_with_unknown_speaker:
        print("Found session with unknown speaker (speaker_id=0) and text.")
        return random.choice(sessions_with_unknown_speaker)

    # Priority 3: Random session
    print("Outputting a random session.")
    return random.choice(sessions)


def main():
    """
    Main function to load sessions, find one based on priority, and format it.
    """
    # Initialize the data loader
    data_loader = ZZZDataLoader(gender='M', player_name='哲')

    # Load all sessions
    sessions = data_loader.get_message_sessions()

    if not sessions:
        print("No sessions found.")
        return

    # Find a session
    target_session = find_session(sessions)
    print(f"Selected session ID: {target_session.session_id}")

    # Format the session using SessionFormatter
    markdown_output = SessionFormatter.to_markdown(target_session)

    # Print the formatted session
    print(markdown_output)


if __name__ == '__main__':
    main()