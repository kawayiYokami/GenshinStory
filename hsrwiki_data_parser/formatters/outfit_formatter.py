from hsrwiki_data_parser.models.outfit import Outfit

class OutfitFormatter:
    def format(self, item: Outfit) -> str:
        """Formats an Outfit object into a Markdown string."""
        if not isinstance(item, Outfit):
            return ""

        md = []
        md.append(f"# {item.name}")
        md.append("\n---\n")

        if item.metadata and item.metadata.type:
            md.append(f"**类型:** {item.metadata.type}\n")

        if item.description:
            md.append(f"## 描述")
            md.append(f"{item.description}\n")

        return '\n'.join(md)