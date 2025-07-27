from hsr_data_parser.models import RogueEvent

class RogueEventFormatter:
    """
    负责将 RogueEvent 对象格式化为 Markdown 文本。
    """
    def format(self, event: RogueEvent) -> str:
        """
        将 RogueEvent 对象转换为格式化的 Markdown 字符串。

        :param event: 要格式化的 RogueEvent 对象。
        """
        if not event or not event.dialogues:
            return ""

        lines = [f"# 模拟宇宙事件：{event.id}"]

        for i, dialogue in enumerate(event.dialogues):
            lines.append(f"\n## 对话块 {i+1}")
            
            if dialogue.simple_talk:
                for talk in dialogue.simple_talk:
                    # 使用 Markdown 的引用格式
                    lines.append(f"> {talk}")
            
            # 由于我们已经过滤了空选项，这里不再需要检查 options 是否存在
            # 也不再打印选项，因为它们是占位符

        return "\n".join(lines)