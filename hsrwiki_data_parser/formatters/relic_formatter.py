from hsrwiki_data_parser.models.relic import Relic

class RelicFormatter:
    def format(self, item: Relic) -> str:
        """Formats a Relic object into a Markdown string."""
        if not isinstance(item, Relic):
            return ""

        md = []
        md.append(f"# {item.name}")
        md.append("\n---\n")

        if item.set_effects:
            md.append("## 套装效果")
            for effect in item.set_effects:
                md.append(f"- **{effect.count}件套:** {effect.description}")
            md.append("")

        if item.pieces:
            md.append("## 物品故事")
            for piece in item.pieces:
                md.append(f"### {piece.name}")
                md.append(f"{piece.story}\n")

        return '\n'.join(md)
