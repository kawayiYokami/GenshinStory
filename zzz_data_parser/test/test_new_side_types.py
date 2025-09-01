import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.abspath('.'))

from zzz_data_parser.dataloader import ZZZDataLoader
from zzz_data_parser.interpreters.unified_dialogue_interpreter import UnifiedDialogueInterpreter


def test_new_side_type_rules():
    """Test that the new side type rules correctly classify example keys."""
    print("Initializing data loader...")
    data_loader = ZZZDataLoader(gender='M', player_name='哲')

    print("Initializing UnifiedDialogueInterpreter...")
    interpreter = UnifiedDialogueInterpreter(data_loader)

    # Mock text map with example keys from the user's feedback
    mock_text_map = {
        "PhotoSideBubble_Chapter01_00001_01": "哪里有合适的地方呢…",
        "PhotoSideChat_Chapter01_00001_01": "要去物色一个适合的小家…",
        "SideChat_Chapter00_001_01": "哼哼~（哼歌）",
        "Side_Chat_Side014_30520204_01": "示例文本",
        "Side_GalGame_SuibianTemple_11120080_044": "于是，在众人的注视下，仪玄翩然走入群鸟之中，伏汐会最后的仪式开始了…",
        "Side_OngoingLevel_Side20JFF_112001001_01": "{F#一会见到福福师姐，先替委托人保密吧。}{M#一会见到福福师姐，先替委托人保密吧。}",
        "StoreChat_Street_0070_01": "小哲，我得问你一个问题…",
        "Store_Chat_ZZZStudio_30420038_05": "我出去逛逛",
    }

    # Temporarily replace the interpreter's text map
    original_text_map = interpreter._text_map
    interpreter._text_map = mock_text_map
    interpreter._classified_keys = None  # Reset cache

    print("Classifying example keys...")
    interpreter._classify_keys()

    classified_keys = interpreter._classified_keys

    # Expected classifications
    expected_classifications = {
        "Chapter01": [
            {"prefix": "PhotoSideBubble", "category": "Side", "sub_category": "PhotoBubble"},
            {"prefix": "PhotoSideChat", "category": "Side", "sub_category": "PhotoChat"},
        ],
        "Chapter00": [
            {"prefix": "SideChat", "category": "Side", "sub_category": "Chat"},
        ],
        "Side014": [
            {"prefix": "Side_Chat", "category": "Side", "sub_category": "Chat"},
        ],
        "SuibianTemple": [
            {"prefix": "Side_GalGame", "category": "Side", "sub_category": "GalGame"},
        ],
        "Side20JFF": [
            {"prefix": "Side_OngoingLevel", "category": "Side", "sub_category": "OngoingLevel"},
        ],
        "Street": [
            {"prefix": "StoreChat", "category": "Side", "sub_category": "StoreChat"},
        ],
        "ZZZStudio": [
            {"prefix": "Store_Chat", "category": "Side", "sub_category": "StoreChat"},
        ],
    }

    print("\nValidation Results:")
    all_passed = True
    for chapter_id, expected_entries in expected_classifications.items():
        if chapter_id not in classified_keys:
            print(f"❌ Chapter ID '{chapter_id}' not found in classified keys")
            all_passed = False
            continue

        actual_entries = classified_keys[chapter_id]
        for expected_entry in expected_entries:
            matched = False
            for actual_entry in actual_entries:
                if (
                    actual_entry.get("prefix") == expected_entry["prefix"]
                    and actual_entry.get("category") == expected_entry["category"]
                    and actual_entry.get("sub_category") == expected_entry["sub_category"]
                ):
                    matched = True
                    break

            if matched:
                print(f"✅ {expected_entry['prefix']} correctly classified as {expected_entry['category']}/{expected_entry['sub_category']}")
            else:
                print(f"❌ {expected_entry['prefix']} NOT correctly classified. Expected {expected_entry['category']}/{expected_entry['sub_category']}")
                all_passed = False

    # Restore original text map
    interpreter._text_map = original_text_map
    interpreter._classified_keys = None  # Reset cache

    if all_passed:
        print("\n🎉 All new side type rules validated successfully!")
    else:
        print("\n💥 Some validation checks failed.")


if __name__ == "__main__":
    test_new_side_type_rules()