"""
原神百科页面爬取与解析的中央协调中心。
该模块负责处理 Playwright 交互、内容展开，并将任务委托给特定的解析器。
"""

import asyncio
import importlib
from pathlib import Path
from typing import Dict, Type, Any

from playwright.async_api import async_playwright

# 导入基础解析器和预处理器
from .parsers.base_parser import BaseParser
from .preprocessor import preprocess_html

# 定义相对于此文件的 parsers 目录路径。
PARSERS_DIR = Path(__file__).parent / "parsers"


class WikiPageCoordinator:
    """
    协调单个维基页面爬取与解析的流程。
    """

    def __init__(self, shared_browser=None):
        """
        初始化协调器，并动态加载可用的解析器。
        
        参数:
            shared_browser: 可选的共享浏览器实例。如果提供，将重用此浏览器而不是创建新的。
        """
        self.registered_parsers: Dict[str, Type[BaseParser]] = self._discover_parsers()
        self.shared_browser = shared_browser

    def _discover_parsers(self) -> Dict[str, Type[BaseParser]]:
        """
        从解析器目录中动态发现并注册解析器类。
        查找名为 'parser_*.py' 的模块，并期望其中包含名为 'Parser*' 的类。

        返回:
            Dict[str, Type[BaseParser]]: 将解析器 ID 映射到解析器类的字典。
        """
        parsers_map = {}
        if not PARSERS_DIR.exists():
            print(f"警告: 解析器目录 '{PARSERS_DIR}' 不存在。")
            return parsers_map

        # print(f"正在 parsers 目录中寻找解析器: {PARSERS_DIR}")
        parser_files = list(PARSERS_DIR.glob("parser_*.py"))
        # print(f"找到的解析器文件: {[p.name for p in parser_files]}")

        for parser_file in parser_files:
            module_name = f".parsers.{parser_file.stem}"  # 例如, '.parsers.parser_227_tutorial'
            # print(f"尝试从模块加载解析器: {module_name}")
            try:
                # 使用包内的相对路径导入模块。
                module = importlib.import_module(module_name, package='gi_wiki_scraper')
                # print(f"成功加载模块: {module_name}")

                # 在模块内查找解析器类。
                # print(f"正在检查模块 '{module_name}' 中的解析器类...")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and issubclass(attr, BaseParser) and
                            attr is not BaseParser):
                        # 从模块名生成解析器 ID (例如, '227_tutorial')
                        parser_id = parser_file.stem[len("parser_"):]
                        parsers_map[parser_id] = attr
                        # print(f"已注册解析器: {parser_id} -> {attr.__name__}")
                        break  # 假设每个模块只有一个解析器类
                else:
                    print(f"警告: 在模块 '{module_name}' 中未找到合适的解析器类。")
            except Exception as e:
                print(f"警告: 从 '{parser_file}' 加载解析器失败: {e}")
                import traceback
                traceback.print_exc()

        # print(f"完成解析器发现。已注册的解析器: {list(parsers_map.keys())}")
        return parsers_map

    async def scrape_and_parse(self, url: str, parser_id: str, timeout: int = 30) -> Dict[str, Any]:
        """
        协调单个维基页面的爬取和解析。

        参数:
            url (str): 要爬取的维基页面的 URL。
            parser_id (str): 要使用的解析器的 ID (例如, '227_tutorial')。
            timeout (int): 页面加载超时时间（秒），默认30秒。

        返回:
            Dict[str, Any]: 从页面解析出的结构化数据。

        抛出:
            ValueError: 如果指定的 parser_id 未找到。
            Exception: 在爬取或解析过程中的任何错误。
        """
        parser_class = self.registered_parsers.get(parser_id)
        if not parser_class:
            raise ValueError(f"未找到 ID 为 '{parser_id}' 的解析器。 "
                             f"可用的解析器: {list(self.registered_parsers.keys())}")

        if self.shared_browser:
            # 使用共享浏览器，为每个请求创建新的上下文
            context = await self.shared_browser.new_context()
            page = await context.new_page()
            
            try:
                # 确保URL包含PC设备参数
                if "&visit_device=pc" not in url:
                    url = url + "&visit_device=pc"
                
                print(f"正在爬取 URL: {url}")
                try:
                    await page.goto(url, wait_until="load", timeout=timeout * 1000)  # Playwright使用毫秒
                except Exception as e:
                    print(f"页面加载超时或失败: {e}")
                    return {"error": f"页面加载超时或失败: {str(e)}"}

                # 滚动到页面底部以触发任何懒加载内容
                print("正在滚动到页面底部...")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000) # 滚动后等待片刻以加载内容

                # --- 开始: 增强交互逻辑 ---

                # 1. 点击所有内容选项卡
                tabs = page.locator(".detail_tab .detail_tab-item")
                tab_count = await tabs.count()
                if tab_count > 0:
                    print(f"找到 {tab_count} 个内容选项卡。正在逐个点击...")
                    for i in range(tab_count):
                        try:
                            await tabs.nth(i).click()
                            await page.wait_for_timeout(200)
                        except Exception as e:
                            print(f"    - 无法点击一个选项卡: {e}")
                    print("完成点击内容选项卡。")

                # 2. 点击所有 swiper 分页点以显示所有内容
                swiper_paginations = page.locator(".swiper-pagination-bullet")
                pagination_count = await swiper_paginations.count()
                if pagination_count > 0:
                    print(f"找到 {pagination_count} 个 swiper 分页点。正在逐个点击...")
                    for i in range(pagination_count):
                        try:
                            bullet = swiper_paginations.nth(i)
                            if await bullet.is_visible():
                                await bullet.click()
                                await page.wait_for_timeout(200)
                        except Exception as e:
                            print(f"    - 无法点击一个 swiper 分页点: {e}")
                    print("完成点击 swiper 分页点。")

                # 3. 对折叠面板使用健壮的、逆序点击逻辑
                expand_buttons = page.locator("span.obc-tmpl__expand-text")
                button_count = await expand_buttons.count()

                if button_count > 0:
                    print(f"找到 {button_count} 个可展开部分。正在逆序点击...")
                    for i in range(button_count - 1, -1, -1):
                        button = expand_buttons.nth(i)
                        try:
                            if await button.is_visible():
                                await button.click()
                                await page.wait_for_timeout(200)
                        except Exception as e:
                            print(f"    - 无法点击一个展开按钮: {e}")
                    print("完成点击展开按钮。")
                else:
                    print("未找到可展开部分。")
                
                # --- 结束: 增强交互逻辑 ---

                html_content = await page.content()
                print("页面内容已完全加载和展开。")

                # --- 预处理和调试步骤 ---
                print("正在预处理 HTML 内容...")
                cleaned_soup = preprocess_html(html_content)

                if cleaned_soup:
                    # 保存清理后的 HTML 用于调试
                    debug_dir = Path(__file__).parent / "output" / "debug"
                    debug_dir.mkdir(exist_ok=True)
                    entry_id = url.split('/')[-2] if '/' in url else "unknown_id"
                    debug_file_path = debug_dir / f"{entry_id}_preprocessed.html"
                    with open(debug_file_path, "w", encoding="utf-8") as f:
                        f.write(cleaned_soup.prettify())
                    print(f"调试用（预处理后）的 HTML 已保存至: {debug_file_path}")

                    # 将清理后的 HTML 传递给解析器
                    parser_instance = parser_class()
                    try:
                        # BaseParser 中的 parse 方法需要一个字符串，所以我们将 soup 对象转换回字符串。
                        json_data = parser_instance.parse(str(cleaned_soup))
                        print(f"使用解析器 ID: {parser_id} 完成解析。")
                    except Exception as e:
                        print(f"解析器执行失败: {e}")
                        return {"error": f"解析器执行失败: {str(e)}"}
                else:
                    print("由于预处理器未返回任何内容，解析被跳过。")
                    json_data = {"error": "在页面中未能找到主要内容。"}
                    
                    # --- 当预处理失败时，保存原始 HTML 用于调试 ---
                    debug_dir = Path(__file__).parent / "output" / "debug"
                    debug_dir.mkdir(exist_ok=True)
                    entry_id = url.split('/')[-2] if '/' in url else "unknown_id"
                    debug_file_path = debug_dir / f"{entry_id}_raw.html"
                    with open(debug_file_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    print(f"已保存原始 HTML 以供检查: {debug_file_path}")
                    # --- 结束原始 HTML 保存 ---
                # --- 结束预处理和调试步骤 ---

            finally:
                await context.close()  # 关闭上下文，自动清理缓存和会话数据
                
        else:
            # 回退到原始行为：为每个请求创建新的浏览器
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                try:
                    # 确保URL包含PC设备参数
                    if "&visit_device=pc" not in url:
                        url = url + "&visit_device=pc"
                    
                    print(f"正在爬取 URL: {url}")
                    try:
                        await page.goto(url, wait_until="load", timeout=timeout * 1000)  # Playwright使用毫秒
                    except Exception as e:
                        print(f"页面加载超时或失败: {e}")
                        return {"error": f"页面加载超时或失败: {str(e)}"}

                    # 滚动到页面底部以触发任何懒加载内容
                    print("正在滚动到页面底部...")
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000) # 滚动后等待片刻以加载内容

                    # --- 开始: 增强交互逻辑 ---

                    # 1. 点击所有内容选项卡
                    tabs = page.locator(".detail_tab .detail_tab-item")
                    tab_count = await tabs.count()
                    if tab_count > 0:
                        print(f"找到 {tab_count} 个内容选项卡。正在逐个点击...")
                        for i in range(tab_count):
                            try:
                                await tabs.nth(i).click()
                                await page.wait_for_timeout(200)
                            except Exception as e:
                                print(f"    - 无法点击一个选项卡: {e}")
                        print("完成点击内容选项卡。")

                    # 2. 点击所有 swiper 分页点以显示所有内容
                    swiper_paginations = page.locator(".swiper-pagination-bullet")
                    pagination_count = await swiper_paginations.count()
                    if pagination_count > 0:
                        print(f"找到 {pagination_count} 个 swiper 分页点。正在逐个点击...")
                        for i in range(pagination_count):
                            try:
                                bullet = swiper_paginations.nth(i)
                                if await bullet.is_visible():
                                    await bullet.click()
                                    await page.wait_for_timeout(200)
                            except Exception as e:
                                print(f"    - 无法点击一个 swiper 分页点: {e}")
                        print("完成点击 swiper 分页点。")

                    # 3. 对折叠面板使用健壮的、逆序点击逻辑
                    expand_buttons = page.locator("span.obc-tmpl__expand-text")
                    button_count = await expand_buttons.count()

                    if button_count > 0:
                        print(f"找到 {button_count} 个可展开部分。正在逆序点击...")
                        for i in range(button_count - 1, -1, -1):
                            button = expand_buttons.nth(i)
                            try:
                                if await button.is_visible():
                                    await button.click()
                                    await page.wait_for_timeout(200)
                            except Exception as e:
                                print(f"    - 无法点击一个展开按钮: {e}")
                        print("完成点击展开按钮。")
                    else:
                        print("未找到可展开部分。")
                    
                    # --- 结束: 增强交互逻辑 ---

                    html_content = await page.content()
                    print("页面内容已完全加载和展开。")

                    # --- 预处理和调试步骤 ---
                    print("正在预处理 HTML 内容...")
                    cleaned_soup = preprocess_html(html_content)

                    if cleaned_soup:
                        # 保存清理后的 HTML 用于调试
                        debug_dir = Path(__file__).parent / "output" / "debug"
                        debug_dir.mkdir(exist_ok=True)
                        entry_id = url.split('/')[-2] if '/' in url else "unknown_id"
                        debug_file_path = debug_dir / f"{entry_id}_preprocessed.html"
                        with open(debug_file_path, "w", encoding="utf-8") as f:
                            f.write(cleaned_soup.prettify())
                        print(f"调试用（预处理后）的 HTML 已保存至: {debug_file_path}")

                        # 将清理后的 HTML 传递给解析器
                        parser_instance = parser_class()
                        try:
                            # BaseParser 中的 parse 方法需要一个字符串，所以我们将 soup 对象转换回字符串。
                            json_data = parser_instance.parse(str(cleaned_soup))
                            print(f"使用解析器 ID: {parser_id} 完成解析。")
                        except Exception as e:
                            print(f"解析器执行失败: {e}")
                            return {"error": f"解析器执行失败: {str(e)}"}
                    else:
                        print("由于预处理器未返回任何内容，解析被跳过。")
                        json_data = {"error": "在页面中未能找到主要内容。"}
                        
                        # --- 当预处理失败时，保存原始 HTML 用于调试 ---
                        debug_dir = Path(__file__).parent / "output" / "debug"
                        debug_dir.mkdir(exist_ok=True)
                        entry_id = url.split('/')[-2] if '/' in url else "unknown_id"
                        debug_file_path = debug_dir / f"{entry_id}_raw.html"
                        with open(debug_file_path, "w", encoding="utf-8") as f:
                            f.write(html_content)
                        print(f"已保存原始 HTML 以供检查: {debug_file_path}")
                        # --- 结束原始 HTML 保存 ---
                    # --- 结束预处理和调试步骤 ---

                finally:
                    await page.close()
                    await browser.close()

        return json_data