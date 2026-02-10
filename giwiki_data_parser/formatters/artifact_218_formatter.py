from giwiki_data_parser.models.artifact_218 import ArtifactSet, ArtifactPiece

class ArtifactFormatter:
    """圣遗物格式化器"""
    
    def format(self, item: ArtifactSet) -> str:
        """将圣遗物套装对象格式化为Markdown字符串"""
        if not isinstance(item, ArtifactSet):
            return ""

        md_lines = []

        # 1. 标题
        md_lines.append(f"# {item.set_name}")
        md_lines.append("")

        # 2. 基本信息
        md_lines.append("## 基本信息")
        md_lines.append("")
        md_lines.append(f"- **套装名称**: {item.set_name}")
        if item.artifact_type:
            md_lines.append(f"- **类型**: {item.artifact_type}")
        md_lines.append("")

        # 3. 套装故事与部件
        md_lines.append("## 套装故事与部件")
        md_lines.append("")

        pieces = [
            ("生之花", item.flower),
            ("死之羽", item.feather),
            ("时之沙", item.sands),
            ("空之杯", item.goblet),
            ("理之冠", item.circlet)
        ]

        for piece_type, piece in pieces:
            if piece:
                md_lines.append(f"### {piece_type}：{piece.name}")
                md_lines.append("")
                if piece.description:
                    md_lines.append(f"- **描述**: {piece.description}")
                if piece.story:
                    md_lines.append(f"- **故事**: \n{piece.story}")
                md_lines.append("")

        return '\n'.join(md_lines)