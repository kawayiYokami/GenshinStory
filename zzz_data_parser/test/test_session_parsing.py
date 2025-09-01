#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the new SessionParser/SessionInterpreter.
This script verifies that phone message sessions are correctly parsed from the configuration files
using the new SessionInterpreter and that the structured Session objects are accurately created.

It will specifically test session 1007 and print its raw structure.
"""

import sys
import os
import pprint

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from zzz_data_parser.dataloader import ZZZDataLoader
from zzz_data_parser.interpreters.session_interpreter import SessionInterpreter


def print_session_structure(session, parser_name):
    """
    Print the raw structure of a session.
    """
    print(f"\n=== {parser_name} - Session {session.session_id} ===")
    pprint.pprint(session, width=120, depth=4)
    print("=" * 50)


def main():
    """
    Main function to load sessions and print the raw structure of session 1007.
    """
    # Initialize the data loader
    data_loader = ZZZDataLoader(gender='M', player_name='哲')

    # Load raw messages
    raw_messages = data_loader.get_json("FileCfg/MessageConfigTemplateTb.json")
    if not raw_messages or 'PDHBFPILAJD' not in raw_messages:
        print("Failed to load raw messages.")
        return

    # Get text map
    text_map = data_loader.get_text_map()

    # Get NPC config
    npc_config = data_loader.get_json("FileCfg/MessageNPCTemplateTb.json")

    # Initialize the interpreter (SessionInterpreter is the migrated implementation)
    interpreter = SessionInterpreter(text_map, npc_config)

    # Interpret with SessionInterpreter
    print("Interpreting with SessionInterpreter...")
    interpreted_sessions = interpreter.interpret(raw_messages['PDHBFPILAJD'])
    # Basic sanity checks to validate migration
    assert isinstance(interpreted_sessions, list), "interpret should return a list of Session objects"
    session_1007_interpreted = None
    for session in interpreted_sessions:
        if session.session_id == 1007:
            session_1007_interpreted = session
            break

    if session_1007_interpreted:
        print_session_structure(session_1007_interpreted, "SessionInterpreter")
    else:
        print("Session 1007 not found with SessionInterpreter.")


if __name__ == '__main__':
    main()