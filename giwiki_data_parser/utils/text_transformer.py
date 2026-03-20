import re
from typing import Optional, List

class TextTransformer:
    """文本转换和处理工具类"""
    
    @staticmethod
    def clean_html_tags(text: str) -> str:
        """清理HTML标签"""
        if not text:
            return ""
        
        # 移除HTML标签
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # 清理多余的空白字符
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """标准化空白字符"""
        if not text:
            return ""
        
        # 将多个空白字符替换为单个空格
        normalized = re.sub(r'\s+', ' ', text)
        
        # 移除首尾空白
        return normalized.strip()
    
    @staticmethod
    def extract_numbers(text: str) -> List[str]:
        """从文本中提取数字"""
        if not text:
            return []
        
        return re.findall(r'\d+(?:\.\d+)?', text)
    
    @staticmethod
    def remove_special_chars(text: str, keep_chars: str = "") -> str:
        """移除特殊字符，保留指定字符"""
        if not text:
            return ""
        
        # 构建保留字符的正则表达式
        pattern = f'[^\\w\\s{re.escape(keep_chars)}]'
        
        return re.sub(pattern, '', text)
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """截断文本到指定长度"""
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def capitalize_words(text: str) -> str:
        """将每个单词的首字母大写"""
        if not text:
            return ""
        
        return ' '.join(word.capitalize() for word in text.split())
    
    @staticmethod
    def extract_wiki_links(text: str) -> List[str]:
        """提取Wiki链接"""
        if not text:
            return []
        
        # 匹配 [[链接]] 格式
        wiki_links = re.findall(r'\[\[([^\]]+)\]\]', text)
        
        return wiki_links
    
    @staticmethod
    def convert_wiki_links_to_markdown(text: str) -> str:
        """将Wiki链接转换为Markdown格式"""
        if not text:
            return ""
        
        # 将 [[链接]] 转换为 [链接](链接)
        def replace_link(match):
            link_text = match.group(1)
            # 如果包含 | 分隔符，分离显示文本和链接
            if '|' in link_text:
                display_text, link_url = link_text.split('|', 1)
                return f'[{display_text.strip()}]({link_url.strip()})'
            else:
                return f'[{link_text}]({link_text})'
        
        return re.sub(r'\[\[([^\]]+)\]\]', replace_link, text)
    
    @staticmethod
    def extract_parentheses_content(text: str) -> List[str]:
        """提取括号内的内容"""
        if not text:
            return []
        
        return re.findall(r'\(([^)]+)\)', text)
    
    @staticmethod
    def remove_parentheses_content(text: str) -> str:
        """移除括号及其内容"""
        if not text:
            return ""
        
        return re.sub(r'\([^)]*\)', '', text).strip()
    
    @staticmethod
    def format_for_filename(text: str) -> str:
        """格式化文本用作文件名"""
        if not text:
            return "untitled"
        
        # 移除或替换不适合文件名的字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', text)
        
        # 移除多余的空白和下划线
        filename = re.sub(r'[_\s]+', '_', filename)
        
        # 移除首尾的下划线
        filename = filename.strip('_')
        
        # 限制长度
        return filename[:100] if len(filename) > 100 else filename
    
    @staticmethod
    def split_sentences(text: str) -> List[str]:
        """将文本分割为句子"""
        if not text:
            return []
        
        # 基于句号、问号、感叹号分割
        sentences = re.split(r'[.!?]+', text)
        
        # 清理空句子和空白
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def extract_quoted_text(text: str) -> List[str]:
        """提取引号内的文本"""
        if not text:
            return []
        
        # 匹配双引号和单引号内的内容
        quoted_texts = []
        quoted_texts.extend(re.findall(r'"([^"]*)"', text))
        quoted_texts.extend(re.findall(r"'([^']*)'", text))
        quoted_texts.extend(re.findall(r'"([^"]*)"', text))  # 中文引号
        # 跳过中文单引号，避免语法错误
        
        return quoted_texts
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本，移除多余的空白和特殊字符"""
        if not text:
            return ""
        
        # 标准化空白字符
        cleaned = TextTransformer.normalize_whitespace(text)
        
        return cleaned