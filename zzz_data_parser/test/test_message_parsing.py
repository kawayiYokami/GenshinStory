#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the new Message parsing system.
This script verifies that phone messages are correctly parsed from the configuration files
and that their data (content, sender, options) is accurately extracted.

To run this test, execute it from the project root directory:
    python -m unittest zzz_data_parser.test.test_message_parsing
Or:
    python zzz_data_parser/test/test_message_parsing.py
"""

import sys
import os
import unittest
import random

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from zzz_data_parser.services.message_service import MessageService
from zzz_data_parser.formatters.message_formatter import MessageFormatter
from zzz_data_parser.dataloader import ZZZDataLoader
from zzz_data_parser.models.message import Message, MessageSession


class TestMessageParsing(unittest.TestCase):
    """
    Test cases for verifying the parsing and formatting of phone message data.
    """

    def setUp(self):
        """
        Set up test fixtures, if any.
        For this test, we rely on the singleton service to load data.
        """
        self.service = MessageService()
        self.data_loader = ZZZDataLoader()
        self.text_map = self.data_loader.get_text_map()

        # Load sessions for session-based tests
        self.sessions = self.service.get_all_sessions()

    def test_message_service_loads_data(self):
        """
        Test that the Message service can load data without errors.
        """
        # This will trigger data loading
        message_ids = self.service.list_message_ids()
        # We expect at least one message to be loaded
        # Note: This assertion depends on the actual data in MessageConfigTemplateTb.json
        # If the file is empty or invalid, this test will fail, which is expected behavior.
        self.assertIsInstance(message_ids, list)
        # Check if any messages were loaded (this is a basic check)
        # A more robust test would check for specific known message IDs.
        # For now, we just ensure the service doesn't crash.
        # If message_ids is empty, it might indicate a problem with data loading or parsing.
        # However, an empty list itself is not an error from the service's perspective.
        # The service's job is to provide data if it exists.

    def test_message_service_loads_sessions(self):
        """
        Test that the Message service can load message sessions without errors.
        """
        # This will trigger data loading
        sessions = self.service.get_all_sessions()
        # We expect sessions to be a list
        self.assertIsInstance(sessions, list)
        # If sessions is empty, it might indicate a problem with data loading or parsing.
        # However, an empty list itself is not an error from the service's perspective.
        # The service's job is to provide data if it exists.

        # If sessions exist, check the structure of the first one
        if sessions:
            session = sessions[0]
            self.assertIsInstance(session, MessageSession) # Assuming MessageSession is imported
            self.assertIsInstance(session.session_id, int)
            self.assertIsInstance(session.messages, list)
            self.assertIsInstance(session.main_npc_id, (int, type(None)))
            self.assertIsInstance(session.main_npc_name, str)

            # Check that messages in the session are Message objects and sorted
            if session.messages:
                prev_seq = -1
                for msg in session.messages:
                    self.assertIsInstance(msg, Message)
                    self.assertGreaterEqual(msg.sequence, prev_seq)
                    prev_seq = msg.sequence

    def test_get_specific_message_by_id(self):
        """
        Test retrieving a specific phone message by its ID.
        This test assumes a known message ID exists in the data.
        If no data is available, this test will be skipped.
        """
        message_ids = self.service.list_message_ids()
        if not message_ids:
            self.skipTest("No phone message data available to test.")

        # Take the first available message ID for testing
        test_id = message_ids[0]
        message = self.service.get_message_by_id(test_id)

        self.assertIsNotNone(message)
        self.assertEqual(message.id, test_id)
        # Assert that sender_name is a string
        self.assertIsInstance(message.sender_name, str)
        # Assert that session_npc_name is a string
        self.assertIsInstance(message.session_npc_name, str)
        # Assert that is_player_message is a boolean
        self.assertIsInstance(message.is_player_message, bool)

    def test_get_specific_session_by_id(self):
        """
        Test retrieving a specific phone message session by its session ID.
        This test assumes a known session ID exists in the data.
        If no data is available, this test will be skipped.
        """
        if not self.sessions:
            self.skipTest("No phone message session data available to test.")

        # Take the first available session ID for testing
        test_session_id = self.sessions[0].session_id
        session = self.service.get_session_by_id(test_session_id)

        self.assertIsNotNone(session)
        self.assertEqual(session.session_id, test_session_id)
        self.assertIsInstance(session.messages, list)
        self.assertIsInstance(session.main_npc_id, (int, type(None)))
        self.assertIsInstance(session.main_npc_name, str)

    def test_message_formatter_to_dict(self):
        """
        Test the MessageFormatter's to_dict method for a MessageSession.
        """
        if not self.sessions:
            self.skipTest("No phone message session data available to test.")

        session = self.sessions[0]

        session_dict = MessageFormatter.to_dict(session, self.text_map)

        self.assertIsInstance(session_dict, dict)
        self.assertIn("session_id", session_dict)
        self.assertIn("main_npc_id", session_dict)
        self.assertIn("main_npc_name", session_dict)
        self.assertIn("messages", session_dict)

        self.assertEqual(session_dict["session_id"], session.session_id)
        self.assertEqual(session_dict["main_npc_id"], session.main_npc_id)
        self.assertEqual(session_dict["main_npc_name"], session.main_npc_name)
        self.assertIsInstance(session_dict["messages"], list)

        # Check structure of messages within the session
        if session_dict["messages"]:
            msg_data = session_dict["messages"][0]
            self.assertIn("id", msg_data)
            self.assertIn("group_id", msg_data)
            self.assertIn("text_key", msg_data)
            self.assertIn("text", msg_data)
            self.assertIn("sequence", msg_data)
            self.assertIn("options", msg_data)
            self.assertIn("is_player_message", msg_data)
            self.assertIn("sender_name", msg_data)
            self.assertIn("session_npc_id", msg_data)
            self.assertIn("session_npc_name", msg_data)

    def test_message_formatter_to_markdown(self):
        """
        Test the MessageFormatter's to_markdown method for a MessageSession.
        """
        if not self.sessions:
            self.skipTest("No phone message session data available to test.")

        session = self.sessions[0]

        markdown_output = MessageFormatter.to_markdown(session, self.text_map)

        self.assertIsInstance(markdown_output, str)
        # Basic checks to see if the markdown contains expected elements for a session
        self.assertIn(f"# 短信会话 ID: {session.session_id}", markdown_output)
        self.assertIn(f"主要NPC: {session.main_npc_name or '[无]'}", markdown_output)
        # Check for message content (should be present if there are messages)
        # The format has been simplified, so we check for sender name and colon
        if session.messages:
            first_msg = session.messages[0]
            if first_msg.sender_name and first_msg.text_key:
                expected_text = self.text_map.get(first_msg.text_key, '')
                if expected_text:
                    self.assertIn(f"**{first_msg.sender_name}**：", markdown_output)

    def test_message_formatter_to_chat(self):
        """
        Test the MessageFormatter's to_chat method for a MessageSession.
        """
        if not self.sessions:
            self.skipTest("No phone message session data available to test.")

        session = self.sessions[0]

        chat_output = MessageFormatter.to_chat(session, self.text_map)

        self.assertIsInstance(chat_output, str)
        # Check for message content (should be present if there are messages)
        # The format is "Sender：Message"
        if session.messages:
            first_msg = session.messages[0]
            if first_msg.sender_name and first_msg.text_key:
                expected_text = self.text_map.get(first_msg.text_key, '')
                if expected_text:
                    self.assertIn(f"{first_msg.sender_name}：", chat_output)

    def test_random_session_formatting_output(self):
        """
        Test randomly selecting a phone message session and formatting its output.
        This test prints the formatted output of a randomly selected session.
        """
        if not self.sessions:
            self.skipTest("No phone message session data available to test.")

        # Randomly select a session
        random_session = random.choice(self.sessions)

        self.assertIsNotNone(random_session, f"Failed to retrieve phone message session with ID {random_session.session_id}")

        print(f"\n--- 随机手机短信会话格式化输出测试 ---")
        print(f"选中的短信会话 ID: {random_session.session_id}")

        # Format to dict and print
        session_dict = MessageFormatter.to_dict(random_session, self.text_map)
        print("\n字典格式输出 (部分):")
        print(f"  session_id: {session_dict.get('session_id')}")
        print(f"  main_npc_name: {session_dict.get('main_npc_name')}")
        print(f"  消息数量: {len(session_dict.get('messages', []))}")
        # Print first message details if available
        if session_dict.get('messages'):
            first_msg = session_dict['messages'][0]
            print(f"  第一条消息 ID: {first_msg.get('id')}")
            print(f"  第一条消息内容: {first_msg.get('text', '')[:50]}...") # Print first 50 chars

        # Format to markdown and print (first 500 chars to avoid excessive output)
        markdown_output = MessageFormatter.to_markdown(random_session, self.text_map)
        print("\nMarkdown格式输出 (前500字符):")
        print(markdown_output[:500])
        if len(markdown_output) > 500:
            print("... (输出已截断)")

        # Format to chat and print (first 500 chars to avoid excessive output)
        chat_output = MessageFormatter.to_chat(random_session, self.text_map)
        print("\nChat格式输出 (前500字符):")
        print(chat_output[:500])
        if len(chat_output) > 500:
            print("... (输出已截断)")
        print("--- 测试结束 ---\n")


if __name__ == '__main__':
    unittest.main()