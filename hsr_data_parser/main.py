import os
import random
import re

from hsr_data_parser.formatters.rogue_event_formatter import RogueEventFormatter
from hsr_data_parser.services import DataLoader, TextMapService
from hsr_data_parser.interpreters import RogueEventInterpreter

def main():
    """
    Main function to test the RogueEventInterpreter.
    """
    # --- Initialization ---
    print("--- 初始化服务 ---")
    loader = DataLoader()
    text_map_service = TextMapService(loader, language_code="CHS")
    interpreter = RogueEventInterpreter(loader, text_map_service)
    formatter = RogueEventFormatter()

    # --- 动态获取所有事件ID ---
    event_dir = "turnbasedgamedata/Config/Level/Rogue/RogueDialogue/"
    all_event_ids = []
    if os.path.exists(event_dir):
        for event_folder in os.listdir(event_dir):
            if event_folder.startswith("Event"):
                # 使用正则表达式从 "Event0313601" 中提取数字 313601
                match = re.search(r'\d+', event_folder)
                if match:
                    all_event_ids.append(int(match.group()))
    
    if not all_event_ids:
        print("错误: 找不到任何事件。")
        return

    # --- 随机选择3个事件进行测试 ---
    # 使用 if/else 避免数量不足时出错
    num_to_sample = 3
    if len(all_event_ids) < num_to_sample:
        test_event_ids = all_event_ids
    else:
        test_event_ids = random.sample(all_event_ids, num_to_sample)

    for test_event_id in test_event_ids:
        print(f"\n--- 正在解析模拟宇宙事件: {test_event_id} ---")
        try:
            event_data = interpreter.interpret(test_event_id)

            if event_data:
                formatted_output = formatter.format(event_data)
                if formatted_output:
                    print("\n--- 解析结果 ---")
                    print(formatted_output)
                else:
                    print("解析成功但无有效对话数据。")
            else:
                print("解析失败。")
        except Exception as e:
            print(f"解析事件 {test_event_id} 时发生错误: {e}")

    print("\n--- 测试完成 ---")


if __name__ == "__main__":
    main()