# -*- coding: utf-8 -*-
from typing import Tuple
import re
from .placeholder_map import REGEX_RULES, INTERNAL_PLAYER_TAG, INTERNAL_MATE_TAG

def transform_text(
    original_text: str,
    gender: str = 'M',
    player_name: str = '旅行者'
) -> Tuple[str, bool]:
    """
    根据给定的规则和参数，转换包含动态占位符和富文本的原始文本。
    同时检测是否存在非法元数据标签。

    :param original_text: 从JSON中读取的原始字符串。
    :param gender: 玩家性别, 'M' for Male, 'F' for Female。
    :param player_name: 玩家的名字。
    :return: 一个元组 (result, is_valid)。
             如果 is_valid 为 False, result 是一个指明非法原因的字符串。
             如果 is_valid 为 True, result 是清理后的文本。
    """
    if not isinstance(original_text, str):
        return "", True # Return empty string for non-string input but consider it "valid"

    # 步骤 1: 检测并处理元数据标签
    # 我们不再简单地替换整个字符串，而是保留原文并添加一个清晰的标记。
    is_hidden = '$HIDDEN' in original_text
    
    # 首先，移除所有元数据标签，以便后续处理
    processed_text = original_text.replace('$HIDDEN', '').replace('$UNRELEASED', '').replace('$END', '')

    # 使用正则表达式处理多种测试标记，包括全角和半角括号
    processed_text = re.sub(r'\(test\)|（test）|\(废弃\)|（废弃）', '', processed_text)

    # 步骤 2: 移除'#'标记 (如果存在)
    if processed_text.startswith('#'):
        processed_text = processed_text[1:]

    # 步骤 3: 根据性别参数，动态处理性别分支
    if gender.upper() == 'M':
        processed_text = re.sub(r'\{M#(.*?)\}', r'\1', processed_text)
        processed_text = re.sub(r'\{F#.*?\}', '', processed_text)
        mate_name = '妹妹'
    else: # 默认为女性
        processed_text = re.sub(r'\{F#(.*?)\}', r'\1', processed_text)
        processed_text = re.sub(r'\{M#.*?\}', '', processed_text)
        mate_name = '哥哥'

    # 步骤 4: 应用 placeholder_map.py 中定义的所有通用正则表达式规则
    for pattern, replacement in REGEX_RULES:
        processed_text = re.sub(pattern, replacement, processed_text)

    # 步骤 5: 将内部临时标签替换为最终的、由参数决定的名字
    processed_text = processed_text.replace(INTERNAL_PLAYER_TAG, player_name)
    processed_text = processed_text.replace(INTERNAL_MATE_TAG, mate_name)

    # 步骤 6 (Bug 修复): 在所有替换完成后，执行最终的清理，移除所有剩下/未知的花括号
    processed_text = re.sub(r'\{(.*?)\}', r'\1', processed_text)

    final_text = processed_text.strip()

    # 如果原始文本被标记为隐藏，则在最前面添加 [隐藏] 标记
    if is_hidden:
        final_text = f"[隐藏] {final_text}"

    # 返回处理后的文本。is_valid 总是 True，因为我们现在不再认为这些是“非法”文本。
    return final_text, True