"""
原神百科页面 HTML 预处理器。

该模块提供用于清理和简化从维基获取的原始 HTML 内容的函数，
然后再将其传递给解析器。
"""

from bs4 import BeautifulSoup, Tag

def preprocess_html(html_content: str) -> Tag | None:
    """
    清理原始 HTML 内容以提取主要内容区域并移除杂乱内容。

    参数:
        html_content (str): 页面的原始 HTML。

    返回:
        BeautifulSoup | None: 表示清理后主要内容区域的 BeautifulSoup 对象，
                              如果找不到主要内容区域则返回 None。
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. 定位核心内容区域。
    # 类的顺序很重要，因为某些页面可能有多个。
    main_content = soup.find('div', class_='detail__body') or \
                   soup.find('div', class_='obc-tmpl-rich-text-content') or \
                   soup.find('div', class_='main-content') # 备用方案

    if not main_content:
        print("警告: 在 HTML 中未找到主要内容区域。")
        return None

    # 2. 从主要内容中移除所有 <img> 标签。
    for img_tag in main_content.find_all('img'):
        img_tag.decompose()

    # 3. 清除主要内容中所有标签的 'data-data' 属性。
    # 这些属性通常包含对解析无用的冗余或复杂数据。
    for data_tag in main_content.find_all(attrs={"data-data": True}):
        data_tag['data-data'] = ""
        
    # 4. 移除 script 和 style 标签
    for s in main_content.select('script, style'):
        s.decompose()

    return main_content