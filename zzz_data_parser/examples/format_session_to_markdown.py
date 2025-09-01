#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example script demonstrating how to use the new SessionFormatter
to generate Markdown output for a specific session.
"""

import sys
import os

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from zzz_data_parser.dataloader import ZZZDataLoader


def main():
    """Main function to demonstrate session formatting."""
    if len(sys.argv) != 2:
        print("Usage: python format_session_to_markdown.py <session_id>")
        sys.exit(1)

    try:
        session_id = int(sys.argv[1])
    except ValueError:
        print("Error: Session ID must be an integer.")
        sys.exit(1)

    # Initialize the data loader
    data_loader = ZZZDataLoader(gender='M', player_name='哲')

    # Get the formatted Markdown string
    markdown_output = data_loader.get_message_session_markdown(session_id)

    if markdown_output:
        # Print to stdout
        print(markdown_output)
        # Optionally, save to a file
        # with open(f"session_{session_id}.md", "w", encoding="utf-8") as f:
        #     f.write(markdown_output)
        # print(f"Markdown output saved to session_{session_id}.md")
    else:
        print(f"Session with ID {session_id} not found.")


if __name__ == "__main__":
    main()