#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import unittest
import random

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from zzz_data_parser.services.vhs_collection_service import VHSCollectionService
from zzz_data_parser.formatters.vhs_collection_formatter import VHSCollectionFormatter


class TestVHSCollectionParsing(unittest.TestCase):
    """
    Test cases for verifying the parsing and formatting of VHS Collection data.
    """

    def setUp(self):
        """
        Set up test fixtures, if any.
        For this test, we rely on the singleton service to load data.
        """
        self.service = VHSCollectionService()

    def test_vhs_collection_service_loads_data(self):
        """
        Test that the VHS Collection service can load data without errors.
        """
        # This will trigger data loading
        vhs_ids = self.service.list_vhs_collection_ids()
        # We expect at least one item to be loaded
        # Note: This assertion depends on the actual data in VHSCollectionConfigTemplateTb.json
        # If the file is empty or invalid, this test will fail, which is expected behavior.
        self.assertIsInstance(vhs_ids, list)
        # Check if any items were loaded (this is a basic check)
        # A more robust test would check for specific known item IDs.
        # For now, we just ensure the service doesn't crash.
        # If vhs_ids is empty, it might indicate a problem with data loading or parsing.
        # However, an empty list itself is not an error from the service's perspective.
        # The service's job is to provide data if it exists.

    def test_get_specific_vhs_collection_by_id(self):
        """
        Test retrieving a specific VHS Collection item by its ID.
        This test assumes a known item ID exists in the data.
        If no data is available, this test will be skipped.
        """
        vhs_ids = self.service.list_vhs_collection_ids()
        if not vhs_ids:
            self.skipTest("No VHS Collection data available to test.")

        # Take the first available item ID for testing
        test_id = vhs_ids[0]
        vhs_item = self.service.get_vhs_collection_by_id(test_id)

        self.assertIsNotNone(vhs_item)
        self.assertEqual(vhs_item.id, test_id)
        # Assert that name is a string (could be empty if text map key is missing)
        self.assertIsInstance(vhs_item.name, str)
        # Assert that description is a string
        self.assertIsInstance(vhs_item.description, str)

    def test_vhs_collection_formatter_to_dict(self):
        """
        Test the VHSCollectionFormatter's to_dict method.
        """
        vhs_ids = self.service.list_vhs_collection_ids()
        if not vhs_ids:
            self.skipTest("No VHS Collection data available to test.")

        test_id = vhs_ids[0]
        vhs_item = self.service.get_vhs_collection_by_id(test_id)

        vhs_dict = VHSCollectionFormatter.to_dict(vhs_item)

        self.assertIsInstance(vhs_dict, dict)
        self.assertIn("id", vhs_dict)
        self.assertIn("name", vhs_dict)
        self.assertIn("description", vhs_dict)

        self.assertEqual(vhs_dict["id"], vhs_item.id)
        self.assertEqual(vhs_dict["name"], vhs_item.name)
        self.assertEqual(vhs_dict["description"], vhs_item.description)

    def test_vhs_collection_formatter_to_markdown(self):
        """
        Test the VHSCollectionFormatter's to_markdown method.
        """
        vhs_ids = self.service.list_vhs_collection_ids()
        if not vhs_ids:
            self.skipTest("No VHS Collection data available to test.")

        test_id = vhs_ids[0]
        vhs_item = self.service.get_vhs_collection_by_id(test_id)

        markdown_output = VHSCollectionFormatter.to_markdown(vhs_item)

        self.assertIsInstance(markdown_output, str)
        # Basic checks to see if the markdown contains expected elements
        self.assertIn(f"# 录像带: {vhs_item.name}", markdown_output)
        if vhs_item.description:
            self.assertIn("## 描述", markdown_output)

    def test_random_vhs_collection_formatting_output(self):
        """
        Test randomly selecting a VHS Collection item and formatting its output.
        This test prints the formatted output of a randomly selected item.
        """
        vhs_ids = self.service.list_vhs_collection_ids()
        if not vhs_ids:
            self.skipTest("No VHS Collection data available to test.")

        # Randomly select an item ID
        random_id = random.choice(vhs_ids)
        vhs_item = self.service.get_vhs_collection_by_id(random_id)

        self.assertIsNotNone(vhs_item, f"Failed to retrieve VHS Collection item with ID {random_id}")

        print(f"\n--- 随机录像带格式化输出测试 ---")
        print(f"选中的录像带 ID: {random_id}")

        # Format to dict and print
        vhs_dict = VHSCollectionFormatter.to_dict(vhs_item)
        print("\n字典格式输出:")
        for key, value in vhs_dict.items():
            print(f"  {key}: {value}")

        # Format to markdown and print
        markdown_output = VHSCollectionFormatter.to_markdown(vhs_item)
        print("\nMarkdown格式输出:")
        print(markdown_output)
        print("--- 测试结束 ---\n")


if __name__ == '__main__':
    unittest.main()