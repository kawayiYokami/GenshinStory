from hsrwiki_data_parser.models.material import Material

class MaterialFormatter:
    def format(self, item: Material) -> str:
        """Formats a Material object into a Markdown string."""
        if not isinstance(item, Material):
            return ""

        md = []
        md.append(f"# {item.name}")
        md.append("\n---\n")

        if item.metadata and item.metadata.type:
            md.append(f"**类型:** {item.metadata.type}\n")

        if item.description:
            md.append(f"## 描述")
            md.append(f"{item.description}\n")

        if item.lore:
            md.append(f"## 故事")
            md.append(f"{item.lore}\n")

        return '\n'.join(md)