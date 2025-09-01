import sys
import os
import random

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.abspath('.'))

from zzz_data_parser.dataloader import ZZZDataLoader
from zzz_data_parser.services.dialogue_service import DialogueService
from zzz_data_parser.formatters.dialogue_formatter import DialogueFormatter


def test_unified_pipeline():
    """Test the unified dialogue service and formatter."""
    print("Initializing data loader...")
    data_loader = ZZZDataLoader()

    print("Initializing DialogueService...")
    service = DialogueService(data_loader)

    print("Getting chapters grouped by category...")
    chapters_by_category = service.get_chapters_by_category()

    print(f"Found chapters in {len(chapters_by_category)} categories:")
    for category, chapters in chapters_by_category.items():
        print(f"  {category}: {len(chapters)} chapters")

    print("\n--- Testing Random Chapters ---")

    # For each category, randomly select one chapter to test
    for category_key, chapter_ids in chapters_by_category.items():
        if not chapter_ids:
            continue

        # Randomly select a chapter
        selected_chapter_id = random.choice(chapter_ids)
        print(f"\nTesting chapter '{selected_chapter_id}' from category {category_key}")

        # Get the chapter data
        chapter = service.get_chapter_by_id(selected_chapter_id)

        if not chapter:
            print(f"  Failed to load chapter {selected_chapter_id}")
            continue

        # Format it using DialogueFormatter
        formatter = DialogueFormatter(chapter)
        markdown_output = formatter.to_markdown()

        # Print a snippet of the markdown output (first 500 characters)
        print(f"  Markdown output (first 500 chars):\n{markdown_output[:500]}...")

        # Also print the dict version
        dict_output = formatter.to_dict()
        print(f"  Dict output keys: {list(dict_output.keys())}")


if __name__ == "__main__":
    test_unified_pipeline()