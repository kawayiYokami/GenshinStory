import re

class TextTransformer:
    """
    一个用于清洗和转换星穹铁道游戏文本的工具类。
    """
    # 预编译正则表达式以提高性能
    # 匹配 <tag> 或 </tag> 形式的HTML风格标签，忽略属性
    TAG_REGEX = re.compile(r'</?[a-zA-Z_]+[^>]*>')
    # 匹配 {...} 形式的占位符
    PLACEHOLDER_REGEX = re.compile(r'\{[A-Z_]+\}')
    # 匹配 {RUBY_B#注音}正文{RUBY_E#} 格式
    RUBY_REGEX = re.compile(r'\{RUBY_B#([^}]+)\}([^\{]+)\{RUBY_E#\}')
    # 匹配 {F#女性}{M#男性} 或 {M#男性}{F#女性} 格式。
    # 这个正则表达式会查找M和F标签对，并捕获M标签的内容。
    # 它不关心M和F的顺序。
    GENDER_REGEX = re.compile(r'\{[MF]#([^}]+)\}\{[MF]#([^}]+)\}')
    # 匹配 {Img#数字} 格式
    IMG_REGEX = re.compile(r'\{Img#(\d+)\}')


    def __init__(self, main_character_name: str = "开拓者"):
        """
        初始化转换器。

        Args:
            main_character_name: 用于替换主角名称占位符的字符串。
        """
        self.main_character_name = main_character_name
        self.placeholder_replacements = {
            "{NICKNAME}": self.main_character_name,
            # 其他占位符可以直接移除或保留，这里我们选择移除
            "{BIRTH}": "",
        }

    def _replace_gender_text(self, match):
        """
        一个辅助函数，用于在GENDER_REGEX匹配时，总是返回男性版本的文本。
        """
        # match.group(0) 是整个匹配的文本，例如 "{M#他}{F#她}"
        # 我们需要在其中找到男性版本
        male_version_match = re.search(r'\{M#([^}]+)\}', match.group(0))
        if male_version_match:
            return male_version_match.group(1)
        # 如果没有M版本（理论上不应该发生），返回空字符串
        return ""

    def transform(self, text: str) -> str:
        """
        对给定的文本执行所有清洗和转换操作。

        Args:
            text: 原始的游戏文本。

        Returns:
            清洗和转换后的纯文本。
        """
        if not isinstance(text, str):
            return text

        # 1. 替换占位符
        for placeholder, replacement in self.placeholder_replacements.items():
            # 使用 re.sub 进行不区分大小写的替换
            text = re.sub(re.escape(placeholder), replacement, text, flags=re.IGNORECASE)

        # 2. 处理性别分支文本，统一选择男性版本
        text = self.GENDER_REGEX.sub(self._replace_gender_text, text)

        # 3. 转换 Ruby 标签，例如 {RUBY_B#注音}正文{RUBY_E#} -> 正文(注音)
        text = self.RUBY_REGEX.sub(r'\2（\1）', text)

        # 4. 转换 Img 标签, 例如 {Img#1} -> 「图片1」
        text = self.IMG_REGEX.sub(r'「图片\1」', text)

        # 5. 移除所有HTML风格的标签
        text = self.TAG_REGEX.sub('', text)

        # 6. 移除一些常见的转义字符，例如 #1, #2 等参数标记
        # 并清理首尾可能产生的多余空格
        text = re.sub(r'#\d+', '', text).strip()

        # 7. 处理字符串形式的换行符 \n 和 \n\n
        #    首先处理双换行，将其转换为真正的段落分隔
        text = text.replace('\\n\\n', '\n\n')
        #    然后处理单个换行，将其转换为空格
        text = text.replace('\\n', ' ')
        #    最后清理可能产生的多余空格
        text = re.sub(r' +', ' ', text) # 将多个连续空格替换为一个
        text = text.strip()

        return text
