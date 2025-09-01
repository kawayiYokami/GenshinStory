#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the new SessionFormatter.
This script verifies that Session objects are correctly formatted into Markdown.
"""

import sys
import os
import unittest

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from zzz_data_parser.formatters.session_formatter import SessionFormatter
from zzz_data_parser.parsers.session_parser import Session, Stage, Message, PlayerOptions, Option


class TestSessionFormatter(unittest.TestCase):
    """
    Test cases for verifying the formatting of Session objects into Markdown.
    """

    def setUp(self):
        """
        Set up test fixtures.
        Creates a mock Session object for testing.
        """
        # Create a mock session that mimics the structure of session 420005
        self.mock_session = Session(
            session_id=420005,
            main_npc_id=10123,
            main_npc_name="浅羽悠真",
            stages={}
        )

        # Stage 1: Player Options
        stage1 = Stage(sequence_id=1)
        stage1.player_options = PlayerOptions(
            message_id=42000501,
            options=[
                Option(text="最近工作如何", long_text=None, jump_to_sequence_id=2),
                Option(text="最近身体如何", long_text=None, jump_to_sequence_id=12)
            ],
            unlocks_condition=None
        )
        self.mock_session.stages[1] = stage1

        # Stage 2: NPC Dialog + Player Options
        stage2 = Stage(sequence_id=2)
        stage2.messages = [
            Message(message_id=42000502, speaker_id=10123, speaker_name="浅羽悠真", text="你…", unlocks_condition=None),
            Message(message_id=42000503, speaker_id=10123, speaker_name="浅羽悠真", text="你竟然和人发消息第一句就问工作！", unlocks_condition=None),
            Message(message_id=42000504, speaker_id=10123, speaker_name="浅羽悠真", text="也太吓人了吧！", unlocks_condition=None)
        ]
        stage2.player_options = PlayerOptions(
            message_id=42000505,
            options=[
                Option(text="我只会问你工作 (我只会问你工作，不会问其他人的)", long_text=None, jump_to_sequence_id=3),
                Option(text="其实是想问你什么时候休息", long_text=None, jump_to_sequence_id=10)
            ],
            unlocks_condition=None
        )
        self.mock_session.stages[2] = stage2

        # Stage 3: NPC Dialog
        stage3 = Stage(sequence_id=3)
        stage3.messages = [
            Message(message_id=42000506, speaker_id=10123, speaker_name="浅羽悠真", text="呜哇", unlocks_condition=None),
            Message(message_id=42000507, speaker_id=10123, speaker_name="浅羽悠真", text="难道这就是我经常摸鱼的报应吗…", unlocks_condition=None),
            Message(message_id=42000508, speaker_id=10123, speaker_name="浅羽悠真", text="开玩笑的啦，我最近休息，有什么事吗？", unlocks_condition=4)
        ]
        self.mock_session.stages[3] = stage3

        # Stage 7: NPC Dialog + End Signal (to test end signal formatting)
        stage7 = Stage(sequence_id=7)
        stage7.messages = [
            Message(message_id=42000512, speaker_id=10123, speaker_name="浅羽悠真", text="光映商场吗？挺好的啊，那里有很多店可以逛", unlocks_condition=None),
            Message(message_id=42000513, speaker_id=10123, speaker_name="浅羽悠真", text="不过那边人也挺多的呢", unlocks_condition=None)
        ]
        stage7.is_end_signal = True
        self.mock_session.stages[7] = stage7

    def test_to_markdown_format(self):
        """
        Test the SessionFormatter's to_markdown method.
        """
        markdown_output = SessionFormatter.to_markdown(self.mock_session)

        # Basic checks
        self.assertIsInstance(markdown_output, str)
        self.assertIn(f"# 会话: {self.mock_session.session_id} - {self.mock_session.main_npc_name}", markdown_output)

        # Check for stage headers and anchors
        self.assertIn("### 阶段 1", markdown_output)
        self.assertIn("<a id=\"stage-1\"></a>", markdown_output)
        self.assertIn("### 阶段 2", markdown_output)
        self.assertIn("<a id=\"stage-2\"></a>", markdown_output)
        self.assertIn("### 阶段 3", markdown_output)
        self.assertIn("<a id=\"stage-3\"></a>", markdown_output)
        self.assertIn("### 阶段 7", markdown_output)
        self.assertIn("<a id=\"stage-7\"></a>", markdown_output)

        # Check for NPC messages
        self.assertIn("**浅羽悠真**: 你…", markdown_output)
        self.assertIn("**浅羽悠真**: 你竟然和人发消息第一句就问工作！", markdown_output)
        self.assertIn("**浅羽悠真**: 也太吓人了吧！", markdown_output)
        self.assertIn("**浅羽悠真**: 呜哇", markdown_output)
        self.assertIn("**浅羽悠真**: 难道这就是我经常摸鱼的报应吗…", markdown_output)
        self.assertIn("**浅羽悠真**: 开玩笑的啦，我最近休息，有什么事吗？", markdown_output)
        self.assertIn("**浅羽悠真**: 光映商场吗？挺好的啊，那里有很多店可以逛", markdown_output)
        self.assertIn("**浅羽悠真**: 不过那边人也挺多的呢", markdown_output)

        # Check for player options and jump links
        # Stage 1 options
        self.assertIn("1. 最近工作如何 -> **跳转到 [阶段 2](#stage-2)**", markdown_output)
        self.assertIn("2. 最近身体如何 -> **跳转到 [阶段 12](#stage-12)**", markdown_output)

        # Stage 2 options
        self.assertIn("1. 我只会问你工作 (我只会问你工作，不会问其他人的) -> **跳转到 [阶段 3](#stage-3)**", markdown_output)
        self.assertIn("2. 其实是想问你什么时候休息 -> **跳转到 [阶段 10](#stage-10)**", markdown_output)

        # Check for unlocks condition
        self.assertIn("(解锁条件: 4)", markdown_output)

        # Check for end signal
        self.assertIn("*会话结束*", markdown_output)

        # Print a snippet of the output for manual verification
        print("\n--- SessionFormatter Markdown Output Snippet ---")
        lines = markdown_output.split('\n')
        for i, line in enumerate(lines[:30]): # Print first 30 lines
            print(f"{i+1:2}: {line}")
        if len(lines) > 30:
            print("... (output truncated)")
        print("--- End Snippet ---\n")

    def test_empty_session(self):
        """
        Test formatting an empty session.
        """
        empty_session = Session(session_id=999, main_npc_id=0, main_npc_name="[未知NPC]", stages={})
        markdown_output = SessionFormatter.to_markdown(empty_session)

        self.assertIsInstance(markdown_output, str)
        self.assertIn(f"# 会话: {empty_session.session_id} - {empty_session.main_npc_name}", markdown_output)
        # Should only contain the header line
        lines = markdown_output.strip().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], f"# 会话: {empty_session.session_id} - {empty_session.main_npc_name}")

    def test_stage_with_no_content(self):
        """
        Test formatting a stage with no messages and no options.
        """
        session_with_empty_stage = Session(session_id=888, main_npc_id=0, main_npc_name="[未知NPC]", stages={})
        empty_stage = Stage(sequence_id=5)
        session_with_empty_stage.stages[5] = empty_stage

        markdown_output = SessionFormatter.to_markdown(session_with_empty_stage)

        self.assertIsInstance(markdown_output, str)
        self.assertIn("### 阶段 5", markdown_output)
        # An empty stage should still have the separator and header
        self.assertIn("---", markdown_output)


if __name__ == '__main__':
    unittest.main()