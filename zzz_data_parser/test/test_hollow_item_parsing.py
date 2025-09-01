#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the new Hollow Item parsing system.
This script verifies that hollow items are correctly parsed from the configuration files
and that their data (name, description) is accurately extracted.
"""

import sys
import os
import random

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from zzz_data_parser.services.hollow_item_service import HollowItemService
from zzz_data_parser.formatters.hollow_item_formatter import HollowItemFormatter


def test_hollow_item_parsing():
    """Test the hollow item parsing functionality."""
    print("Starting Hollow Item Parsing Test...")

    # Initialize the service
    hollow_item_service = HollowItemService()

    # Test 1: List all hollow item IDs
    print("\n1. Listing all hollow item IDs...")
    hollow_item_ids = hollow_item_service.list_item_ids()
    print(f"   Found {len(hollow_item_ids)} hollow items.")
    if not hollow_item_ids:
        print("   ERROR: No hollow items found!")
        return False

    # Test 2: Get a specific hollow item (e.g., the first one)
    first_hollow_item_id = hollow_item_ids[0]
    print(f"\n2. Getting hollow item with ID {first_hollow_item_id}...")
    first_hollow_item = hollow_item_service.get_item_by_id(first_hollow_item_id)
    if not first_hollow_item:
        print(f"   ERROR: Could not retrieve hollow item with ID {first_hollow_item_id}")
        return False
    print(f"   Retrieved hollow item: {first_hollow_item.name}")

    # Test 3: Check fields of the first hollow item
    print(f"\n3. Checking fields of hollow item '{first_hollow_item.name}' (ID: {first_hollow_item.id})...")
    if not first_hollow_item.name:
        print("   WARNING: Hollow item name is empty!")
    else:
        print(f"   Name: '{first_hollow_item.name}'")

    if first_hollow_item.description:
        print(f"   Description: '{first_hollow_item.description}'")
    else:
        print("   Description: Not available")

    # Test 4: Format the first hollow item to Markdown
    print(f"\n4. Formatting hollow item '{first_hollow_item.name}' to Markdown...")
    markdown_output = HollowItemFormatter.to_markdown(first_hollow_item)
    print("   Markdown Output:")
    print(markdown_output[:500] + ("..." if len(markdown_output) > 500 else ""))  # Show first 500 chars

    # Test 5: Convert the first hollow item to a dictionary
    print(f"\n5. Converting hollow item '{first_hollow_item.name}' to dictionary...")
    dict_output = HollowItemFormatter.to_dict(first_hollow_item)
    print("   Dictionary Output:")
    for key, value in dict_output.items():
        print(f"     {key}: {value}")

    # Test 6: Output formatted results for 3 random hollow items
    print("\n6. Formatting 3 random hollow items to Markdown...")
    # Select 3 random hollow items, or all items if there are fewer than 3
    selected_hollow_item_ids = random.sample(hollow_item_ids, min(3, len(hollow_item_ids)))

    for i, item_id in enumerate(selected_hollow_item_ids, 1):
        item = hollow_item_service.get_item_by_id(item_id)
        if item:
            print(f"\n--- Random Hollow Item {i}: {item.name} (ID: {item.id}) ---")
            markdown_output = HollowItemFormatter.to_markdown(item)
            print(markdown_output)
        else:
            print(f"\n--- Random Hollow Item {i}: Could not retrieve hollow item with ID {item_id} ---")


    print("\nHollow Item Parsing Test completed successfully!")
    return True


if __name__ == "__main__":
    success = test_hollow_item_parsing()
    sys.exit(0 if success else 1)