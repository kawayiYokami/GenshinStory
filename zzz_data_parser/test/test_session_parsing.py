#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the new Session parsing system.
This script verifies that phone message sessions are correctly parsed from the configuration files
using the new SessionParser and that the structured Session objects are accurately created.

To run this test, execute it from the project root directory:
    python -m unittest zzz_data_parser.test.test_session_parsing
Or:
    python zzz_data_parser/test/test_session_parsing.py
"""

import sys
import os
import unittest

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from zzz_data_parser.dataloader import ZZZDataLoader
from zzz_data_parser.parsers.session_parser import Session, Stage, Message, PlayerOptions, Option


class TestSessionParsing(unittest.TestCase):
    """
    Test cases for verifying the parsing of phone message sessions into structured Session objects.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        self.data_loader = ZZZDataLoader()
        # Load sessions using the new method
        self.sessions = self.data_loader.get_message_sessions()

    def test_data_loader_loads_sessions(self):
        """
        Test that the ZZZDataLoader can load and parse message sessions without errors.
        """
        # This will trigger data loading and parsing
        sessions = self.data_loader.get_message_sessions()

        # We expect sessions to be a list
        self.assertIsInstance(sessions, list)

        # If sessions is empty, it might indicate a problem with data loading or parsing.
        # However, an empty list itself is not an error from the service's perspective.
        # The service's job is to provide data if it exists.

        # If sessions exist, check the structure of the first one
        if sessions:
            session = sessions[0]
            self.assertIsInstance(session, Session)
            self.assertIsInstance(session.session_id, int)
            self.assertIsInstance(session.main_npc_id, int)
            self.assertIsInstance(session.main_npc_name, str)
            self.assertIsInstance(session.stages, dict)

            # Check that stages are mapped by sequence_id
            if session.stages:
                sequence_id, stage = next(iter(session.stages.items()))
                self.assertIsInstance(sequence_id, int)
                self.assertIsInstance(stage, Stage)
                self.assertEqual(stage.sequence_id, sequence_id)

    def test_session_structure(self):
        """
        Test the structure and content of a parsed Session object.
        This test assumes a known session ID exists in the data.
        If no data is available, this test will be skipped.
        """
        if not self.sessions:
            self.skipTest("No phone message session data available to test.")

        # Take the first available session for testing
        session = self.sessions[0]

        # Basic checks
        self.assertIsInstance(session.session_id, int)
        self.assertGreater(session.session_id, 0)
        self.assertIsInstance(session.main_npc_id, int)
        self.assertIsInstance(session.main_npc_name, str)
        self.assertIsInstance(session.stages, dict)

        # Check stages
        for sequence_id, stage in session.stages.items():
            self.assertIsInstance(sequence_id, int)
            self.assertIsInstance(stage, Stage)
            self.assertEqual(stage.sequence_id, sequence_id)

            # A stage should have either messages or player_options, but not both (in most cases)
            # It can also be an end signal
            has_messages = bool(stage.messages)
            has_options = stage.player_options is not None
            is_end = stage.is_end_signal

            # At least one should be true
            self.assertTrue(has_messages or has_options or is_end,
                            f"Stage {sequence_id} has no content (messages, options, or end signal)")

            # Check messages if present
            if has_messages:
                for msg in stage.messages:
                    self.assertIsInstance(msg, Message)
                    self.assertIsInstance(msg.message_id, int)
                    self.assertIsInstance(msg.speaker_id, int)
                    self.assertIsInstance(msg.speaker_name, str)
                    self.assertIsInstance(msg.text, str)
                    # unlocks_condition is optional
                    if msg.unlocks_condition is not None:
                        self.assertIsInstance(msg.unlocks_condition, int)

            # Check player options if present
            if has_options:
                opts = stage.player_options
                self.assertIsInstance(opts, PlayerOptions)
                self.assertIsInstance(opts.message_id, int)
                self.assertIsInstance(opts.options, list)
                # unlocks_condition is optional
                if opts.unlocks_condition is not None:
                    self.assertIsInstance(opts.unlocks_condition, int)

                # Check individual options
                for opt in opts.options:
                    self.assertIsInstance(opt, Option)
                    self.assertIsInstance(opt.text, str)
                    # long_text is optional
                    if opt.long_text is not None:
                        self.assertIsInstance(opt.long_text, str)
                    self.assertIsInstance(opt.jump_to_sequence_id, int)

            # Check end signal
            if is_end:
                # An end signal stage typically has no other content
                # This is a basic check, logic might vary
                pass

    def test_specific_session_id_420005(self):
        """
        Test parsing and structure of a specific, known session (ID 420005).
        This test is based on the earlier analysis and debugging.
        If this session ID is not present in the data, the test will be skipped.
        """
        target_session_id = 420005
        target_session = None
        for session in self.sessions:
            if session.session_id == target_session_id:
                target_session = session
                break

        if not target_session:
            self.skipTest(f"Specific test session ID {target_session_id} not found in data.")

        # Known facts about session 420005 from previous analysis
        self.assertEqual(target_session.main_npc_id, 10123)
        self.assertEqual(target_session.main_npc_name, "浅羽悠真")

        # Check for specific stages
        # Stage 1 (Sequence ID 1) should have player options
        stage_1 = target_session.stages.get(1)
        self.assertIsNotNone(stage_1, "Stage with sequence ID 1 not found in session 420005")
        self.assertIsNotNone(stage_1.player_options, "Stage 1 should contain player options")
        self.assertEqual(len(stage_1.player_options.options), 2, "Stage 1 should have 2 player options")

        # Check option texts (combined from text_key and long_text_key)
        option_texts = [opt.text for opt in stage_1.player_options.options]
        self.assertIn("最近工作如何", option_texts, "Option text '最近工作如何' not found in stage 1")
        self.assertIn("最近身体如何", option_texts, "Option text '最近身体如何' not found in stage 1")

        # Check jump IDs for options in stage 1
        jump_ids = [opt.jump_to_sequence_id for opt in stage_1.player_options.options]
        self.assertIn(2, jump_ids, "Jump ID 2 not found for options in stage 1")
        self.assertIn(12, jump_ids, "Jump ID 12 not found for options in stage 1")

        # Stage 2 (Sequence ID 2) should have NPC messages
        stage_2 = target_session.stages.get(2)
        self.assertIsNotNone(stage_2, "Stage with sequence ID 2 not found in session 420005")
        self.assertTrue(stage_2.messages, "Stage 2 should contain NPC messages")
        # Check that all messages in stage 2 from NPCs are from '浅羽悠真'
        # (There might be player messages mixed in, e.g., for unlock conditions)
        for msg in stage_2.messages:
            if msg.speaker_id != 0: # Only check NPC messages
                self.assertEqual(msg.speaker_name, "浅羽悠真", "NPC Message in stage 2 should be from '浅羽悠真'")

        # The original analysis in the test was incorrect.
        # Stages with player options are those where messages have "用途不明 ID 1: 1".
        # From debug_session.py output, these are stages 1, 2, 4, 6, 12.
        # Stages 7 and 8 contain NPC dialog ("用途不明 ID 1: 0") and end signals ("用途不明 ID 1: 3").

        # Stage 6 (Sequence ID 6) should have player options
        stage_6 = target_session.stages.get(6)
        self.assertIsNotNone(stage_6, "Stage with sequence ID 6 not found in session 420005")
        self.assertIsNotNone(stage_6.player_options, "Stage 6 should contain player options")
        self.assertEqual(len(stage_6.player_options.options), 2, "Stage 6 should have 2 player options")

        # Check option texts for stage 6
        option_texts_6 = [opt.text for opt in stage_6.player_options.options]
        self.assertIn("去「光映商场」如何？", option_texts_6, "Option text '去「光映商场」如何？' not found in stage 6")
        self.assertIn("来「厄匹斯港」如何?", option_texts_6, "Option text '来「厄匹斯港」如何?' not found in stage 6")

        # Check jump IDs for options in stage 6
        jump_ids_6 = [opt.jump_to_sequence_id for opt in stage_6.player_options.options]
        self.assertIn(7, jump_ids_6, "Jump ID 7 not found for options in stage 6") # One option jumps to sequence 7
        self.assertIn(8, jump_ids_6, "Jump ID 8 not found for options in stage 6") # One option jumps to sequence 8


if __name__ == '__main__':
    unittest.main()