from .services import DataLoader, TextMapService
from .interpreters import QuestInterpreter

def main():
    """
    Main function to test the HSR data parser.
    """
    # --- Initialization ---
    # Note: TextMapCHS.json is not in the provided file list, so this might fail.
    # Assuming it exists in the same directory.
    loader = DataLoader(data_path="turnbasedgamedata/ExcelOutput")
    text_map_service = TextMapService(loader, language_code="CHS")
    quest_interpreter = QuestInterpreter(loader, text_map_service)

    # --- Select a quest to test ---
    # From QuestData.json, QuestID 1001714 has FinishWayID 1001714.
    # From FinishWay.json, ID 1001714 is of type "FinishMission" and has ParamIntList.
    # This makes it a good candidate for a test.
    test_quest_id = 1001714

    # --- Interpretation ---
    print(f"Attempting to interpret Quest ID: {test_quest_id}")
    quest = quest_interpreter.interpret(test_quest_id)

    # --- Output ---
    if quest:
        print("\n--- Quest Details ---")
        print(f"  ID: {quest.quest_id}")
        print(f"  Title: {quest.quest_title}")
        if quest.steps:
            print("  Steps:")
            for i, step in enumerate(quest.steps, 1):
                print(f"    {i}. ID: {step.step_id}")
                print(f"       Title: {step.title}")
                print(f"       Description: {step.description}")
        else:
            print("  No steps found for this quest.")
        print("---------------------\n")
    else:
        print(f"Failed to interpret Quest ID: {test_quest_id}")


if __name__ == "__main__":
    main()