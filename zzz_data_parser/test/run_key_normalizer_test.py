#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
一个简单的脚本，用于直接运行和测试 key_normalizer 模块的功能。
这避免了 unittest 框架可能带来的导入路径问题。
"""

# --- 设置模块导入路径 ---
import sys
import os

# 获取当前脚本所在的目录 (e.g., e:\github\story\zzz_data_parser\test)
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# 获取项目根目录 (e.g., e:\github\story)
# 我们需要向上两级: test -> zzz_data_parser -> story (root)
project_root = os.path.dirname(os.path.dirname(current_script_dir))

# 将项目根目录添加到 Python 路径中
sys.path.insert(0, project_root)
# --- 路径设置结束 ---

# --- 导入要测试的模块 ---
from zzz_data_parser.utils.key_normalizer import normalize_dialogue_key
# --- 导入结束 ---

def run_tests():
    """
    执行一系列预定义的测试用例，验证 normalize_dialogue_key 函数。
    """
    print("--- 开始测试 key_normalizer 模块 ---")

    # 测试用例: [(输入, 期望输出), ...]
    test_cases = [
        # MainChat_Chapter... -> Main_Chat_Chapter...
        ("MainChat_Chapter05_0001_01", "Main_Chat_Chapter05_0001_01"),
        # MainChat_数字_... -> Main_Chat_Chapter数字_...
        ("MainChat_2_0001_00", "Main_Chat_Chapter02_0001_00"),
        ("MainChat_07_0001_01", "Main_Chat_Chapter07_0001_01"),
        # CompanionBubble_... -> Companion_Bubble_...
        ("CompanionBubble_ChapterBurnice_0050_001", "Companion_Bubble_ChapterBurnice_0050_001"),
        # Activity_GalGame_...-... -> Activity_GalGame_..._...
        ("Activity_GalGame_Summer-Story1_10162008_015", "Activity_GalGame_Summer_Story1_10162008_015"),
        # 已经是标准格式的 key 应保持不变
        ("Main_Chat_Chapter05_0001_01", "Main_Chat_Chapter05_0001_01"),
        ("Companion_Bubble_ChapterAnby_001_01", "Companion_Bubble_ChapterAnby_001_01"),
    ]

    all_passed = True
    for i, (input_key, expected_output) in enumerate(test_cases):
        try:
            actual_output = normalize_dialogue_key(input_key)
            if actual_output == expected_output:
                print(f"[ 通过 ] 测试用例 {i+1}: '{input_key}' -> '{actual_output}'")
            else:
                print(f"[ 失败 ] 测试用例 {i+1}: '{input_key}'")
                print(f"        期望: '{expected_output}'")
                print(f"        实际: '{actual_output}'")
                all_passed = False
        except Exception as e:
            print(f"[ 错误 ] 测试用例 {i+1}: '{input_key}' 执行时发生异常: {e}")
            all_passed = False

    print("\n--- 测试结束 ---")
    if all_passed:
        print("所有测试用例均已通过! 恭喜!")
    else:
        print("部分测试用例失败，请检查代码逻辑。")

if __name__ == "__main__":
    run_tests()