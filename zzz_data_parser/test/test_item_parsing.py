#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the new Item parsing system.
This script verifies that items are correctly parsed from the configuration files
and that their data (name, description, story) is accurately extracted.
"""

import sys
import os
import random

import logging

# Configure logging to show INFO level messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from zzz_data_parser.services.item_service import ItemService
from zzz_data_parser.formatters.item_formatter import ItemFormatter


def test_item_parsing():
    """Test the item parsing functionality."""
    print("Starting Item Parsing Test...")

    # Initialize the service
    item_service = ItemService()

    # Test 1: List all item IDs
    print("\n1. Listing all item IDs...")
    item_ids = item_service.list_item_ids()
    print(f"   Found {len(item_ids)} items.")
    if not item_ids:
        print("   ERROR: No items found!")
        return False

    # Test 2: Get a specific item (e.g., the first one)
    first_item_id = item_ids[0]
    print(f"\n2. Getting item with ID {first_item_id}...")
    first_item = item_service.get_item_by_id(first_item_id)
    if not first_item:
        print(f"   ERROR: Could not retrieve item with ID {first_item_id}")
        return False
    print(f"   Retrieved item: {first_item.name}")

    # Test 3: Check fields of the first item
    print(f"\n3. Checking fields of item '{first_item.name}' (ID: {first_item.id})...")
    if not first_item.name:
        print("   WARNING: Item name is empty!")
    else:
        print(f"   Name: '{first_item.name}'")

    if first_item.description:
        print(f"   Description: '{first_item.description}'")
    else:
        print("   Description: Not available")

    if first_item.story:
        print(f"   Story: '{first_item.story}'")
    else:
        print("   Story: Not available")

    # Test 4: Format the first item to Markdown
    print(f"\n4. Formatting item '{first_item.name}' to Markdown...")
    markdown_output = ItemFormatter.to_markdown(first_item)
    print("   Markdown Output:")
    print(markdown_output[:500] + ("..." if len(markdown_output) > 500 else ""))  # Show first 500 chars

    # Test 5: Convert the first item to a dictionary
    print(f"\n5. Converting item '{first_item.name}' to dictionary...")
    dict_output = ItemFormatter.to_dict(first_item)
    print("   Dictionary Output:")
    for key, value in dict_output.items():
        print(f"     {key}: {value}")

    # Test 6: Find a meaningful item with description/story if possible
    print("\n6. Looking for an item with description or story...")
    meaningful_item_found = False
    for item_id in item_ids[1:]:  # Skip the first one we already checked
        item = item_service.get_item_by_id(item_id)
        if item and (item.description or item.story):
            print(f"   Found item '{item.name}' (ID: {item.id}) with description/story")
            print(f"   Description: {item.description[:100]}{'...' if len(item.description) > 100 else ''}")
            print(f"   Story: {item.story[:100]}{'...' if len(item.story) > 100 else ''}")
            meaningful_item_found = True
            break

    if not meaningful_item_found:
        print("   Note: No item with description or story found in the first few items checked.")

    # Test 7: Output formatted results for 3 random items
    print("\n7. Formatting 3 random items to Markdown...")
    # Select 3 random items, or all items if there are fewer than 3
    selected_item_ids = random.sample(item_ids, min(3, len(item_ids)))

    for i, item_id in enumerate(selected_item_ids, 1):
        item = item_service.get_item_by_id(item_id)
        if item:
            print(f"\n--- Random Item {i}: {item.name} (ID: {item.id}) ---")
            markdown_output = ItemFormatter.to_markdown(item)
            print(markdown_output)
        else:
            print(f"\n--- Random Item {i}: Could not retrieve item with ID {item_id} ---")


    print("\nItem Parsing Test completed successfully!")
    return True


if __name__ == "__main__":
    success = test_item_parsing()
    sys.exit(0 if success else 1)