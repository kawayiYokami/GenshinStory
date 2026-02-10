from hsrwiki_data_parser.models.lightcone import Lightcone


class LightconeFormatter:
    def format(self, item: Lightcone) -> str:
        """Formats a Lightcone object into a Markdown string."""
        if not isinstance(item, Lightcone):
            return ""

        md = []
        md.append(f"# {item.name}")
        md.append("\n---\n")

        # 基本信息
        md.append(f"**命途:** {item.path}")
        md.append(f"**星级:** {item.rarity}\n")

        # 描述
        if item.description:
            md.append(f"## 描述")
            md.append(f"{item.description}\n")

        return "\n".join(md)