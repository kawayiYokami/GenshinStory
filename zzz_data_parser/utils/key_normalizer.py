import re

def normalize_dialogue_key(key: str) -> str:
    """
    将各种不规范的对话 key 规范化为统一的标准格式。
    标准格式: {CATEGORY}_{SUB_CATEGORY}_{CHAPTER_ID}_{ACT_ID}_{LINE_INFO}

    Args:
        key (str): 原始的、可能不规范的对话 key。

    Returns:
        str: 规范化后的标准 key。
    """
    # 1. 处理 MainChat_ 格式
    # 1a. MainChat_Chapter05_... -> Main_Chat_Chapter05_...
    key = re.sub(r'^MainChat_Chapter(\d+)_', r'Main_Chat_Chapter\1_', key)
    # 1b. MainChat_2_... -> Main_Chat_Chapter02_...
    # 这个规则必须放在 1a 之后，以避免对已经处理过的 key 产生错误影响
    key = re.sub(r'^MainChat_(\d+)_', lambda m: f"Main_Chat_Chapter{int(m.group(1)):02d}_", key)

    # 2. 处理 CompanionBubble_ 格式
    key = key.replace('CompanionBubble_', 'Companion_Bubble_')

    # 3. 处理 Activity_GalGame_ 中的连字符
    # 例如: Activity_GalGame_Summer-Story1_... -> Activity_GalGame_Summer_Story1_...
    # 这里假设连字符是章节ID的一部分，且应被替换为下划线。
    # 注意：这个替换是全局的，如果需要更精确，可以使用更复杂的正则表达式。
    key = key.replace('-', '_')

    # 4. 可以在这里添加更多规则来处理其他不规范的格式...
    # 例如:
    # key = key.replace('OldPattern_', 'NewPattern_')

    # 5. 返回最终规范化的 key
    # 如果输入的 key 本身已经是标准格式，或者经过上述规则处理后，
    # 它将保持不变或变为标准格式。
    return key