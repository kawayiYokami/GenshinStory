"""
Wiki页面批量或单页抓取与导出工具 (Playwright 版本)。

功能:
1.  **批量模式 (默认)**:
    遍历 `categorized_links` 目录下的所有分类JSON文件，
    提取每个文件的第一个URL，抓取并处理页面，
    将清理后的正文HTML片段保存到 `part_html` 目录。

2.  **单页模式 (通过 --url 参数触发)**:
    抓取并处理指定的单个URL，同样将清理后的正文HTML片段
    保存到 `part_html` 目录。
"""

import asyncio
import json
import sys
import argparse
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# 将项目根目录添加到 sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- 常量定义 ---
CURRENT_DIR = Path(__file__).parent
INPUT_DIR = CURRENT_DIR / "categorized_links"
OUTPUT_DIR = CURRENT_DIR / "part_html"


async def fetch_and_process_url(page, url, category_name=None):
    """
    使用 Playwright 抓取URL，解析HTML，提取并整理正文内容。
    对于特定分类（如"角色"），会执行额外的交互操作。
    """
    try:
        print(f"    - 正在访问: {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)

        # --- 特殊处理逻辑: 根据分类点击页面元素 ---
        if category_name == "角色":
            print("    - 检测到'角色'分类，尝试执行特殊交互...")
            try:
                # 等待语音模块容器出现，最多5秒
                await page.wait_for_selector("#module-20", timeout=5000)
                print("    - 语音模块 (#module-20) 已找到。")

                voice_expand_buttons = page.locator("#module-20 .wiki-btn-all")
                button_count = await voice_expand_buttons.count()

                if button_count > 0:
                    print(f"    - 找到 {button_count} 个'查看全部语音'按钮候选。")
                    clicked = False
                    for i in range(button_count):
                        button = voice_expand_buttons.nth(i)
                        if await button.is_visible():
                            print(f"    - 找到可见的'查看全部语音'按钮，正在点击...")
                            await button.click()
                            await page.wait_for_timeout(2000)
                            print("    - 点击完成。")
                            clicked = True
                            break
                    if not clicked:
                        print("    - 未找到可见的'查看全部语音'按钮。")
                else:
                    print("    - 未找到'查看全部语音'按钮。")
            except PlaywrightTimeoutError:
                print("    - 未在5秒内找到语音模块 (#module-20)，跳过点击操作。")
            except Exception as e:
                print(f"    - 点击'查看全部语音'按钮时发生意外错误: {e}")

        # --- 页面解析与清理 ---
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')

        detail_body = soup.find('div', class_='detail__body') or soup.find('div', class_='obc-tmpl-rich-text-content')

        if not detail_body:
            return {"error": "未找到 <div class='detail__body'> 或备用选择器"}

        # 移除所有 <img> 标签
        for img_tag in detail_body.find_all('img'):
            img_tag.decompose()

        # 清空所有带有 data-data 属性的标签的 data-data 值
        for data_tag in detail_body.find_all(attrs={"data-data": True}):
            data_tag['data-data'] = ""

        return detail_body.prettify()

    except PlaywrightTimeoutError:
        return {"error": f"页面加载超时: {url}"}
    except Exception as e:
        return {"error": f"处理时发生未知错误: {e}"}


async def process_and_save(page, url, output_path, category_name):
    """
    处理单个URL并保存结果。
    """
    print(f"  -> 正在处理: {url}")
    print(f"     分类: {'无' if not category_name else category_name}")
    content = await fetch_and_process_url(page, url, category_name)

    if isinstance(content, dict) and "error" in content:
        print(f"    - 失败: {content['error']}")
        error_html = f"<html><body><h1>处理失败</h1><p>URL: {url}</p><p>错误: {content['error']}</p></body></html>"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(error_html)
    else:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"    - 成功: 已保存至 {output_path.resolve()}")
        except IOError as e:
            print(f"    - 失败: 无法写入文件 {output_path.name}: {e}")


async def run_single_url_mode(url, category):
    """
    执行单页抓取模式。
    """
    print("执行单页抓取模式...")
    OUTPUT_DIR.mkdir(exist_ok=True)

    try:
        content_id = url.split('/content/')[1].split('/')[0]
        output_filename = f"{content_id}.html"
    except IndexError:
        print(f"  -> 警告: 无法从URL解析内容ID，将使用默认文件名 'temp_page.html'。 ולא נראה לי שזה נכון.")
        output_filename = "temp_page.html"

    output_path = OUTPUT_DIR / output_filename

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await process_and_save(page, url, output_path, category)
        await browser.close()

    print(f"\n单页抓取完成！HTML片段已保存至: {output_path.resolve()}")


async def run_batch_mode():
    """
    执行批量抓取模式 (原始功能)。
    """
    print("开始执行Wiki正文批量导出...")
    OUTPUT_DIR.mkdir(exist_ok=True)

    json_files = list(INPUT_DIR.glob("*.json"))
    if not json_files:
        print(f"错误: 在 '{INPUT_DIR}' 中未找到任何 .json 文件。")
        return

    print(f"找到 {len(json_files)} 个分类文件。")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for json_path in json_files:
            category_name = json_path.stem.split('_', 1)[-1]
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    links_dict = json.load(f)
                    if not links_dict:
                        print(f"  -> 警告: '{json_path.name}' 文件为空，已跳过。")
                        continue

                    first_url = next(iter(links_dict.values()))
                    output_filename = json_path.stem + ".html"
                    output_path = OUTPUT_DIR / output_filename

                    await process_and_save(page, first_url, output_path, category_name)

            except (json.JSONDecodeError, StopIteration) as e:
                print(f"  -> 错误: 处理 '{json_path.name}' 失败: {e}，已跳过。")
            except Exception as e:
                print(f"  -> 未知错误: 处理 '{json_path.name}' 时发生: {e}，已跳过。")

        await browser.close()

    print(f"\n所有分类处理完毕！HTML样本已保存至: {OUTPUT_DIR.resolve()}")


async def main():
    """
    脚本主入口函数，根据命令行参数选择执行模式。
    """
    parser = argparse.ArgumentParser(description="Wiki页面批量或单页抓取与导出工具。 ולא נראה לי שזה נכון.")
    parser.add_argument("--url", type=str, help="要抓取的单个页面的URL。 ולא נראה לי שזה נכון.")
    parser.add_argument("--category", type=str, help="当使用--url时，可指定页面分类以触发特殊操作 (例如 '角色')。 ולא נראה לי שזה נכון.")
    args = parser.parse_args()

    if args.url:
        await run_single_url_mode(args.url, args.category)
    else:
        await run_batch_mode()


if __name__ == "__main__":
    asyncio.run(main())