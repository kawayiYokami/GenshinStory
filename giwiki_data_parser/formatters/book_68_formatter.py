from giwiki_data_parser.models.book_68 import Book, BookChapter

class BookFormatter:
    """书籍格式化器"""
    
    def format(self, item: Book) -> str:
        """将书籍对象格式化为Markdown字符串"""
        if not isinstance(item, Book):
            return ""
        
        md = []
        
        # 标题
        md.append(f"# {item.book_name}")
        md.append("")
        
        # 基本信息表格
        md.append("## 基本信息")
        md.append("")
        md.append("| 项目 | 内容 |")
        md.append("|------|------|")
        md.append(f"| 书名 | {item.book_name} |")
        
        if item.book_type:
            md.append(f"| 类型 | {item.book_type} |")
        
        md.append("")
        
        # 章节内容
        if item.chapters:
            for i, chapter in enumerate(item.chapters, 1):
                md.extend(self._format_chapter(chapter, i))
        
        return '\n'.join(md)
    
    def _format_chapter(self, chapter: BookChapter, chapter_num: int) -> list:
        """格式化书籍章节"""
        md = []
        
        # 章节标题
        if chapter.chapter_title:
            md.append(f"## 第{chapter_num}章：{chapter.chapter_title}")
        else:
            md.append(f"## 第{chapter_num}章")
        md.append("")
        
        # 章节描述
        if chapter.description:
            md.append(f"**描述：** {chapter.description}")
            md.append("")
        
        # 章节内容
        if chapter.content:
            # 处理长文本内容，按照特定标记分段
            content = chapter.content.strip()
            
            # 如果内容很长，尝试按照特定模式分段
            if len(content) > 500:
                # 寻找可能的分段标记
                if "……【" in content and "】" in content:
                    # 按照【标题】格式分段
                    sections = self._split_by_sections(content)
                    for section in sections:
                        md.append(section)
                        md.append("")
                else:
                    # 按照句号分段，但保持段落完整性
                    paragraphs = self._split_into_paragraphs(content)
                    for paragraph in paragraphs:
                        md.append(paragraph)
                        md.append("")
            else:
                md.append(content)
                md.append("")
        
        return md
    
    def _split_by_sections(self, content: str) -> list:
        """按照【标题】格式分段"""
        sections = []
        current_section = []
        lines = content.split("……【")
        
        # 处理第一部分（可能没有标题）
        if lines[0].strip():
            sections.append(lines[0].strip())
        
        # 处理带标题的部分
        for line in lines[1:]:
            if "】" in line:
                title_end = line.find("】")
                title = line[:title_end]
                content_part = line[title_end + 1:].strip()
                
                section_text = f"### {title}\n\n{content_part}"
                sections.append(section_text)
        
        return sections
    
    def _split_into_paragraphs(self, content: str, max_length: int = 300) -> list:
        """将长文本分割为合适长度的段落"""
        paragraphs = []
        sentences = content.split('。')
        current_paragraph = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_paragraph + sentence) > max_length:
                if current_paragraph:
                    paragraphs.append(current_paragraph + "。")
                    current_paragraph = sentence
                else:
                    paragraphs.append(sentence + "。")
            else:
                if current_paragraph:
                    current_paragraph += "。" + sentence
                else:
                    current_paragraph = sentence
        
        if current_paragraph:
            paragraphs.append(current_paragraph + ("。" if not current_paragraph.endswith("。") else ""))
        
        return paragraphs