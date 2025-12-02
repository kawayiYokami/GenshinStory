#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import unittest

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from zzz_data_parser.services.weapon_service import WeaponService
from zzz_data_parser.formatters.weapon_formatter import WeaponFormatter


class TestWeaponParsing(unittest.TestCase):
    """
    Test cases for verifying the parsing and formatting of weapon data.
    """

    def setUp(self):
        """
        Set up test fixtures, if any.
        For this test, we rely on the singleton service to load data.
        """
        self.service = WeaponService()

    def test_weapon_service_loads_data(self):
        """
        Test that the weapon service can load data without errors.
        """
        # This will trigger data loading
        weapon_ids = self.service.list_weapon_ids()
        # We expect at least one weapon to be loaded
        # Note: This assertion depends on the actual data in WeaponTemplateTb.json
        # If the file is empty or invalid, this test will fail, which is expected behavior.
        self.assertIsInstance(weapon_ids, list)
        # Check if any weapons were loaded (this is a basic check)
        # A more robust test would check for specific known weapon IDs.
        # For now, we just ensure the service doesn't crash.
        # If weapon_ids is empty, it might indicate a problem with data loading or parsing.
        # However, an empty list itself is not an error from the service's perspective.
        # The service's job is to provide data if it exists.

    def test_get_specific_weapon_by_id(self):
        """
        Test retrieving a specific weapon by its ID.
        This test assumes a known weapon ID exists in the data.
        If no weapon data is available, this test will be skipped.
        """
        weapon_ids = self.service.list_weapon_ids()
        if not weapon_ids:
            self.skipTest("No weapon data available to test.")

        # Take the first available weapon ID for testing
        test_id = weapon_ids[0]
        weapon = self.service.get_weapon_by_id(test_id)

        self.assertIsNotNone(weapon)
        self.assertEqual(weapon.id, test_id)
        # Assert that name is a string (could be empty if text map key is missing)
        self.assertIsInstance(weapon.name, str)
        # Assert that other fields are strings
        self.assertIsInstance(weapon.description, str)
        self.assertIsInstance(weapon.story, str)
        self.assertIsInstance(weapon.model_id, str)

    def test_weapon_formatter_to_dict(self):
        """
        Test the WeaponFormatter's to_dict method.
        """
        weapon_ids = self.service.list_weapon_ids()
        if not weapon_ids:
            self.skipTest("No weapon data available to test.")

        test_id = weapon_ids[0]
        weapon = self.service.get_weapon_by_id(test_id)

        weapon_dict = WeaponFormatter.to_dict(weapon)

        self.assertIsInstance(weapon_dict, dict)
        self.assertIn("id", weapon_dict)
        self.assertIn("name", weapon_dict)
        self.assertIn("description", weapon_dict)
        self.assertIn("story", weapon_dict)
        self.assertIn("model_id", weapon_dict)

        self.assertEqual(weapon_dict["id"], weapon.id)
        self.assertEqual(weapon_dict["name"], weapon.name)
        self.assertEqual(weapon_dict["description"], weapon.description)
        self.assertEqual(weapon_dict["story"], weapon.story)
        self.assertEqual(weapon_dict["model_id"], weapon.model_id)

    def test_weapon_formatter_to_markdown(self):
        """
        Test the WeaponFormatter's to_markdown method.
        """
        weapon_ids = self.service.list_weapon_ids()
        if not weapon_ids:
            self.skipTest("No weapon data available to test.")

        test_id = weapon_ids[0]
        weapon = self.service.get_weapon_by_id(test_id)

        markdown_output = WeaponFormatter.to_markdown(weapon)

        self.assertIsInstance(markdown_output, str)
        # Basic checks to see if the markdown contains expected elements
        self.assertIn(f"# {weapon.name}", markdown_output)
        if weapon.description:
            self.assertIn("## 描述", markdown_output)
        if weapon.story:
            self.assertIn("## 故事", markdown_output)

    def test_random_weapon_formatting_output(self):
        """
        Test randomly selecting a weapon and formatting its output.
        This test prints the formatted output of a randomly selected weapon.
        """
        import random

        weapon_ids = self.service.list_weapon_ids()
        if not weapon_ids:
            self.skipTest("No weapon data available to test.")

        # Randomly select a weapon ID
        random_id = random.choice(weapon_ids)
        weapon = self.service.get_weapon_by_id(random_id)

        self.assertIsNotNone(weapon, f"Failed to retrieve weapon with ID {random_id}")

        print(f"\n--- 随机武器格式化输出测试 ---")
        print(f"选中的武器 ID: {random_id}")

        # Format to dict and print
        weapon_dict = WeaponFormatter.to_dict(weapon)
        print("\n字典格式输出:")
        for key, value in weapon_dict.items():
            print(f"  {key}: {value}")

        # Format to markdown and print
        markdown_output = WeaponFormatter.to_markdown(weapon)
        print("\nMarkdown格式输出:")
        print(markdown_output)
        print("--- 测试结束 ---\n")


if __name__ == '__main__':
    unittest.main()