"""地图文本格式化器"""
from typing import List
from ..models.map_text_251 import MapTextModel


class MapTextFormatter:
    """地图文本格式化器"""
    
    def format(self, model: MapTextModel) -> str:
        """格式化地图文本为Markdown"""
        lines = []
        
        # 标题
        lines.append(f"# {model.title}")
        lines.append("")
        
        # 基本信息
        lines.append("## 基本信息")
        lines.append("")
        lines.append(f"- **类型**: {model.type}")
        if model.region:
            lines.append(f"- **地区**: {model.region}")
        lines.append("")
        
        # 文本内容
        if model.content:
            lines.append("## 文本内容")
            lines.append("")
            
            current_section = None
            for line in model.content:
                line = line.strip()
                if not line:
                    continue
                
                # 检查是否是章节标题
                if line.startswith("【") and line.endswith("】"):
                    if current_section is not None:
                        lines.append("")  # 添加空行分隔
                    lines.append(f"### {line}")
                    lines.append("")
                    current_section = line
                elif line.startswith("（") and line.endswith("）"):
                    # 位置标记
                    if current_section is not None:
                        lines.append("")
                    lines.append(f"#### {line}")
                    lines.append("")
                    current_section = line
                else:
                    # 普通内容
                    if line.startswith("「") and line.endswith("」"):
                        # 引用内容，使用引用格式
                        lines.append(f"> {line}")
                    else:
                        lines.append(line)
                    lines.append("")
        
        # 元数据信息
        if model.metadata:
            lines.append("---")
            lines.append("")
            lines.append("## 元数据")
            lines.append("")
            lines.append(f"- **数据来源**: {model.metadata.source_type}")
            lines.append(f"- **包含故事内容**: {'是' if model.metadata.has_story_content else '否'}")
            
            if model.metadata.content_tags:
                lines.append(f"- **内容标签**: {', '.join(model.metadata.content_tags)}")
        
        return "\n".join(lines)
    
    def get_filename(self, model: MapTextModel) -> str:
        """获取文件名"""
        # 清理标题中的特殊字符
        safe_title = self._clean_filename(model.title)
        return f"251_地图文本_{safe_title}.md"
    
    def _clean_filename(self, title: str) -> str:
        """清理文件名中的特殊字符"""
        # 移除或替换不适合文件名的字符
        replacements = {
            "/": "_",
            "\\": "_",
            ":": "：",
            "*": "＊",
            "?": "？",
            '"': '"',
            "<": "＜",
            ">": "＞",
            "|": "｜"
        }
        
        for old, new in replacements.items():
            title = title.replace(old, new)
        
        return title[:50]  # 限制长度