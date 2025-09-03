from hsrwiki_data_parser.models.message import MessageThread

class MessageFormatter:
    def format(self, item: MessageThread) -> str:
        if not isinstance(item, MessageThread):
            return ""

        md = []
        md.append(f"# {item.name}")
        md.append("\n---\n")

        for msg in item.messages:
            md.append(f"**{msg.sender}:** {msg.text}")
        
        return '\n'.join(md)