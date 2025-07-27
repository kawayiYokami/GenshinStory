from hsr_data_parser.models import MessageThread

class MessageFormatter:
    """
    负责将 MessageThread 对象格式化为 Markdown 文本。
    """
    def format(self, thread: MessageThread) -> str:
        """
        将 MessageThread 对象转换为格式化的 Markdown 字符串。
        """
        if not thread or not thread.messages:
            return ""

        # 使用第一个消息的发送者作为标题
        lines = [f"# 短信对话: {thread.messages[0].sender}"]
        
        for msg in thread.messages:
            lines.append(f"\n**{msg.sender}**:")
            lines.append(f"> {msg.text}")
                
        return "\n".join(lines)