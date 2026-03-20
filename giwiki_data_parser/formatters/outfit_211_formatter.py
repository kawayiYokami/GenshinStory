from giwiki_data_parser.models.outfit_211 import OutfitModel


class OutfitFormatter:
    """装扮格式化器"""

    _INTRO_KEYWORDS = ("简介", "衣装简介", "风之翼简介", "介绍")
    _STORY_KEYWORDS = ("故事", "衣装故事", "风之翼故事", "背景")

    def format(self, item: OutfitModel) -> str:
        """将装扮对象格式化为Markdown字符串"""
        if not isinstance(item, OutfitModel):
            return ""

        md_lines = []

        # 1. 标题
        md_lines.append(f"# {item.name}")
        md_lines.append("")

        # 2. 简介（如果有）
        if item.has_introduction():
            md_lines.append("## 简介")
            md_lines.append("")
            md_lines.append(item.introduction)
            md_lines.append("")

        # 3. 故事（如果有）
        if item.has_story():
            md_lines.append("## 故事")
            md_lines.append("")
            md_lines.append(item.story)
            md_lines.append("")

        # 4. 其余分段（避免与“简介/故事”重复）
        for section in item.sections:
            if not isinstance(section, dict):
                continue

            heading = str(section.get("heading", "") or "").strip()
            text = str(section.get("text", "") or "").strip()
            if not heading and not text:
                continue

            if heading and any(keyword in heading for keyword in self._INTRO_KEYWORDS):
                if text and item.introduction and text in item.introduction:
                    continue
            if heading and any(keyword in heading for keyword in self._STORY_KEYWORDS):
                if text and item.story and text in item.story:
                    continue

            title = heading or "补充内容"
            md_lines.append(f"## {title}")
            md_lines.append("")
            if text:
                md_lines.append(text)
            md_lines.append("")

        return '\n'.join(md_lines)

    def get_filename(self, item: OutfitModel) -> str:
        """生成文件名"""
        if not isinstance(item, OutfitModel):
            return "unknown.md"

        # 清理文件名中的特殊字符
        safe_name = item.name.replace("「", "").replace("」", "").replace("/", "-").replace("\\", "-")
        safe_name = safe_name.replace(":", "-").replace("*", "-").replace("?", "-")
        safe_name = safe_name.replace("<", "-").replace(">", "-").replace("|", "-")

        # 如果有ID，添加到文件名中
        if item.id:
            return f"{safe_name}-{item.id}.md"
        else:
            return f"{safe_name}.md"
