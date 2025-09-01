import sys
import os

# Add the project root to the path so we can import modules
# This assumes the script is run from the project root
sys.path.insert(0, os.path.abspath('.'))

from zzz_data_parser.dataloader import ZZZDataLoader
from zzz_data_parser.interpreters.unified_dialogue_interpreter import UnifiedDialogueInterpreter
# This test file only uses the new UnifiedDialogueInterpreter


def test_unified_interpreter():
    """Test the new UnifiedDialogueInterpreter."""
    print("Initializing data loader...")
    data_loader = ZZZDataLoader(gender='M', player_name='哲')

    print("Initializing UnifiedDialogueInterpreter...")
    interpreter = UnifiedDialogueInterpreter(data_loader)

    print("Listing chapter IDs...")
    chapter_ids = interpreter.list_chapter_ids()
    print(f"Found {len(chapter_ids)} chapters.")

    if not chapter_ids:
        print("No chapters found. Exiting.")
        return

    # Test with the first few chapters
    test_chapters = chapter_ids[:3]

    for chapter_id in test_chapters:
        print(f"\nInterpreting chapter: {chapter_id}")
        chapter = interpreter.interpret(chapter_id)

        if chapter:
            print(f"  Category: {chapter.category}")
            print(f"  Sub-category: {chapter.sub_category}")
            print(f"  Number of acts: {len(chapter.acts)}")

            # Print details of the first act if it exists
            if chapter.acts:
                first_act_id = list(chapter.acts.keys())[0]
                first_act = chapter.acts[first_act_id]
                print(f"  First act ID: {first_act_id}")
                print(f"    Number of lines: {len(first_act.lines)}")
                print(f"    Speakers: {first_act.speakers}")

                # Print first few lines
                line_keys = list(first_act.lines.keys())[:3]
                for line_key in line_keys:
                    line = first_act.lines[line_key]
                    print(f"      Line {line_key}:")
                    if line.male_text:
                        print(f"        Male: {line.male_text}")
                    if line.female_text:
                        print(f"        Female: {line.female_text}")
                    if line.speaker:
                        print(f"        Speaker: {line.speaker}")
                    if line.options:
                        print(f"        Options: {line.options}")
        else:
            print(f"  Failed to interpret chapter {chapter_id}")


if __name__ == "__main__":
    test_unified_interpreter()