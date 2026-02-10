"""
原神百科链接抓取器 (Genshin Impact Wiki Link Scraper) - Playwright 版本

此脚本使用 Playwright 来处理 JavaScript 动态加载的内容，
从米哈游原神百科的图鉴主页抓取所有内容分类及其下属条目的链接，
并将结果保存为结构化的 JSON 文件。
"""

import os
import re
import json
import asyncio
from pathlib import Path
from urllib.parse import urljoin

# Playwright 用于处理动态内容
from playwright.async_api import async_playwright
# BeautifulSoup 用于解析 HTML
from bs4 import BeautifulSoup


# --- 核心常量定义 ---
BASE_URL = "https://baike.mihoyo.com"
ENTRY_URL = "https://baike.mihoyo.com/ys/obc/channel/map/189/25?bbs_presentation_style=no_header&visit_device=pc"

# --- 需要抓取的分类ID白名单 ---
INCLUDED_CATEGORIES = {
    "5",    # 武器
    "6",    # 敌人
    "13",   # 背包
    "20",   # NPC&商店
    "21",   # 食物
    "25",   # 角色
    "43",   # 任务
    "49",   # 动物
    "54",   # 秘境
    "55",   # 冒险家协会
    "68",   # 书籍
    "211",  # 装扮
    "218",  # 圣遗物
    "251",  # 地图文本
    "255",  # 组织
    "261",  # 角色逸闻
}

# 使用绝对路径确保在任何位置运行脚本都能正确输出
from pathlib import Path
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "output" / "link"


def sanitize_filename(name):
    """将字符串转换为安全的文件名。"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace("•", "_").replace(" ", "_")
    return name


async def fetch_page_content(page, url):
    """使用 Playwright 页面对象获取 URL 的 HTML 内容。"""
    try:
        print(f"正在导航到: {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        content = await page.content()
        print(f"  -> 页面加载完成。")
        return content
    except Exception as e:
        print(f"  -> 错误：访问 {url} 时出错: {e}")
        return None


async def fetch_categories(page):
    """
    访问入口页面，解析并获取所有内容分类的信息。
    """
    print(f"正在从入口页面获取所有分类信息...")

    html_content = await fetch_page_content(page, ENTRY_URL)
    if not html_content:
        print("错误：无法获取入口页面内容。")
        return []

    soup = BeautifulSoup(html_content, 'html.parser')

    # 使用正确的选择器定位容器
    category_container = soup.select_one("div.swiper-pagination.position-list__tabs")
    if not category_container:
        print("错误：在入口页面上未能找到分类容器 'div.swiper-pagination.position-list__tabs'。")
        # 调试：打印部分HTML以检查结构
        # print("页面部分HTML:", soup.prettify()[:2000])
        return []

    categories_list = []
    # 遍历容器内所有的 span 标签
    for span_tag in category_container.find_all("span"):
        # 更精确地获取 span 标签的直接文本内容
        category_name = span_tag.get_text(strip=True)
        category_id_raw = span_tag.get("id") # 例如 "_position_25"

        if not category_id_raw:
            continue # 跳过没有 id 的标签

        # 用正则表达式从 id 中提取数字
        id_match = re.search(r'_position_(\d+)', category_id_raw)
        if not id_match:
            continue # 跳过格式不匹配的 id

        category_id = id_match.group(1) # -> 25

        # 添加过滤：只处理需要的分类
        if category_id not in INCLUDED_CATEGORIES:
            print(f" -> 跳过不需要的分类: {category_name} (ID: {category_id})")
            continue

        # 拼接分类页面的完整 URL
        category_url = f"{BASE_URL}/ys/obc/channel/map/189/{category_id}?bbs_presentation_style=no_header&visit_device=pc"

        # 将信息存入列表
        categories_list.append({
            "name": category_name,
            "id": category_id,
            "url": category_url
        })
        print(f" -> 发现分类: {category_name} (ID: {category_id})")

    print(f"成功获取到 {len(categories_list)} 个分类。")
    return categories_list


async def discover_filters(page):
    """
    动态发现页面上的所有筛选器及其选项。
    返回筛选器字典：{筛选器名称: [选项列表]}
    """
    print("  -> 正在发现页面筛选器...")

    # 检查页面是否有筛选器容器（不强制等待）
    try:
        await page.wait_for_selector("div.pos-filter-pc", timeout=3000)
    except:
        print("  -> 该分类页面没有筛选器，将使用基础抓取模式")
        return {}

    filters_dict = {}

    # 获取所有筛选器容器
    filter_selectors = await page.query_selector_all("div.el-select.pos-filter-pc__select")

    for i, filter_selector in enumerate(filter_selectors):
        try:
            # 获取筛选器名称（从placeholder）
            input_element = await filter_selector.query_selector("input.el-input__inner")
            if not input_element:
                continue

            filter_name = await input_element.get_attribute("placeholder")
            if not filter_name:
                continue

            print(f"    -> 发现筛选器: {filter_name}")

            # 点击输入框打开下拉菜单
            await input_element.click()

            # 等待该输入框获得焦点状态（更精确的等待条件）
            await filter_selector.wait_for_selector("div.el-input.is-focus", timeout=10000)

            # 等待箭头翻转，确认下拉菜单已激活
            await filter_selector.wait_for_selector("i.el-icon-arrow-up.is-reverse", timeout=5000)

            # 等待一下让下拉菜单状态更新
            await page.wait_for_timeout(1000)

            # 动态查找当前活跃的下拉菜单
            all_dropdowns = await page.query_selector_all("div.el-select-dropdown.pos-filter-pc__select-dropdown")
            visible_dropdown = None

            for dropdown in all_dropdowns:
                # 检查是否有x-placement属性（活跃下拉菜单的标识）
                placement = await dropdown.get_attribute("x-placement")
                if placement:
                    visible_dropdown = dropdown
                    print(f"      -> 找到活跃下拉菜单，placement: {placement}")
                    break

            if not visible_dropdown:
                print(f"      -> 警告：未找到活跃的下拉菜单")
                continue

            # 从可见下拉菜单中获取选项
            option_elements = await visible_dropdown.query_selector_all("li.el-select-dropdown__item span")
            options = []

            for option_element in option_elements:
                option_text = await option_element.inner_text()
                if option_text:
                    options.append(option_text.strip())

            filters_dict[filter_name] = options
            print(f"      -> 选项: {options}")

            # 点击"不限"选项关闭下拉菜单并重置状态
            if options and "不限" in options:
                unlimited_option = await visible_dropdown.query_selector("li.el-select-dropdown__item span:has-text('不限')")
                if unlimited_option:
                    await unlimited_option.click()
                    # 等待下拉菜单关闭
                    await page.wait_for_timeout(500)

            # 短暂等待，确保状态重置
            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"    -> 警告：处理筛选器 {i} 时出错: {e}")
            continue

    print(f"  -> 共发现 {len(filters_dict)} 个筛选器")
    return filters_dict


async def extract_items_from_page(page):
    """
    从当前页面提取所有条目的基础信息。
    返回条目列表：[{id, name, url}]
    """
    # 等待内容加载
    await page.wait_for_selector("div.channel-content-container", timeout=10000)

    items_list = []

    # 获取所有条目链接
    link_elements = await page.query_selector_all("div.channel-content-container a[href*='/ys/obc/content/'][href*='/detail']")

    for link_element in link_elements:
        try:
            # 获取链接
            href = await link_element.get_attribute("href")
            if not href:
                continue

            # 提取ID
            id_match = re.search(r'/content/(\d+)/detail', href)
            if not id_match:
                continue
            item_id = id_match.group(1)

            # 获取名称
            title_element = await link_element.query_selector('[class*="title"]')
            if title_element:
                item_name = await title_element.inner_text()
            else:
                h5_element = await link_element.query_selector("h5")
                if h5_element:
                    item_name = await h5_element.inner_text()
                else:
                    item_name = "未知名称"

            # 构建完整URL
            full_url = urljoin(BASE_URL, href)

            items_list.append({
                "id": item_id,
                "name": item_name.strip(),
                "url": full_url
            })

        except Exception as e:
            print(f"    -> 警告：提取条目信息时出错: {e}")
            continue

    return items_list


async def fetch_items_with_tags_for_category(page, category):
    """
    访问单个分类页面，通过动态筛选获取带标签的条目数据。
    """
    category_url = category["url"]
    print(f"  -> 正在抓取分类 '{category['name']}' 的条目链接和标签...")

    # 导航到分类页面
    await page.goto(category_url, wait_until="networkidle", timeout=60000)

    # 调试：检查实际加载的页面内容
    current_url = page.url
    page_title = await page.title()
    print(f"  -> 实际URL: {current_url}")
    print(f"  -> 页面标题: {page_title}")

    # 检查页面上实际存在的筛选器
    actual_filters = await page.query_selector_all("input.el-input__inner[placeholder]")
    actual_placeholders = []
    for filter_input in actual_filters:
        placeholder = await filter_input.get_attribute("placeholder")
        if placeholder:
            actual_placeholders.append(placeholder)
    print(f"  -> 实际筛选器: {actual_placeholders}")

    # 阶段一：发现筛选器
    filters_dict = await discover_filters(page)
    if not filters_dict:
        print(f"  -> 警告：未发现任何筛选器，使用基础抓取模式")
        return await fetch_items_for_category_basic(page, category)

    # 阶段二：获取基准数据（不限状态下的全量数据）
    print("  -> 获取基准数据...")
    base_items = await extract_items_from_page(page)

    # 构建以ID为键的字典，预留tags字段
    items_dict = {}
    for item in base_items:
        items_dict[item["id"]] = {
            "id": item["id"],
            "name": item["name"],
            "url": item["url"],
            "tags": {}
        }

    print(f"  -> 基准数据：{len(items_dict)} 个条目")

    # 阶段三：迭代筛选和标注
    for filter_name, options in filters_dict.items():
        print(f"  -> 处理筛选器: {filter_name}")

        for option in options:
            if option == "不限":
                continue  # 跳过"不限"选项

            # 在处理当前筛选器前，先重置所有其他筛选器到"不限"
            await reset_all_filters_to_unlimited(page, filters_dict.keys(), current_filter=filter_name)

            # 找到筛选器容器
            filter_container = await page.query_selector(f"div.el-select.pos-filter-pc__select:has(input[placeholder='{filter_name}'])")
            if not filter_container:
                print(f"    -> 警告：找不到筛选器容器 {filter_name}")
                continue

            # 应用筛选器（带重试）
            success, filtered_items = await apply_filter_with_retry(page, filter_container, option)

            if success:
                # 为筛选后的条目添加标签
                tagged_count = 0
                for item in filtered_items:
                    if item["id"] in items_dict:
                        items_dict[item["id"]]["tags"][filter_name] = option
                        tagged_count += 1

                print(f"      -> 为 {tagged_count} 个条目添加标签 {filter_name}={option}")
            else:
                print(f"    -> 跳过筛选器 {filter_name}={option}（应用失败）")

    # 转换为列表格式
    items_list = list(items_dict.values())

    # 保存结果（保持原有文件名格式，确保下游兼容性）
    safe_category_name = sanitize_filename(category["name"])
    output_filename = f'{OUTPUT_DIR}/{category["id"]}_{safe_category_name}.json'

    try:
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(items_list, f, ensure_ascii=False, indent=2)
        print(f" -> 成功保存 {len(items_list)} 个带标签条目到: {output_filename}")
    except Exception as e:
        print(f"  -> 错误：保存文件 {output_filename} 失败: {e}")

    return items_list


async def apply_filter_with_retry(page, filter_container, option, max_retries=3):
    """
    应用筛选器，带重试机制
    返回 (success: bool, filtered_items: list)
    """
    for attempt in range(max_retries):
        try:
            print(f"    -> 尝试应用筛选器 {option} (第{attempt+1}次)")

            # 每次重试前先重置当前筛选器到"不限"状态
            await reset_filter_to_unlimited(page, filter_container)

            # 获取筛选前的内容快照
            before_items = await extract_items_from_page(page)

            # 执行筛选操作
            success = await perform_filter_selection(page, filter_container, option)
            if not success:
                continue

            # 等待内容更新
            await wait_for_content_update(page, before_items)

            # 验证筛选结果
            after_items = await extract_items_from_page(page)

            if is_filter_effective(before_items, after_items):
                print(f"      -> 筛选成功：{len(before_items)} -> {len(after_items)} 个条目")
                return True, after_items
            else:
                print(f"      -> 筛选未生效，重试...")

        except Exception as e:
            print(f"      -> 第{attempt+1}次尝试失败: {e}")

    print(f"    -> 筛选器 {option} 应用失败，已达到最大重试次数")
    return False, []


async def perform_filter_selection(page, filter_container, option):
    """执行筛选器选择操作"""
    try:
        # 点击输入框
        filter_input = await filter_container.query_selector("input.el-input__inner")
        await filter_input.click()

        # 等待下拉菜单
        await filter_container.wait_for_selector("i.el-icon-arrow-up.is-reverse", timeout=5000)

        # 找到可见的下拉菜单
        visible_dropdown = await find_visible_dropdown(page)
        if not visible_dropdown:
            return False

        # 点击目标选项
        option_element = await visible_dropdown.query_selector(f"li.el-select-dropdown__item span:has-text('{option}')")
        if not option_element:
            return False

        await option_element.click()
        return True

    except Exception as e:
        print(f"      -> 筛选器操作失败: {e}")
        return False


async def wait_for_content_update(page, before_items):
    """等待内容更新"""
    try:
        # 等待网络空闲
        await page.wait_for_load_state('networkidle', timeout=8000)

        # 等待加载指示器消失
        await page.wait_for_selector('.el-loading-mask, .loading-spinner', state='hidden', timeout=5000)

        # 额外缓冲时间
        await page.wait_for_timeout(1000)

    except Exception as e:
        print(f"      -> 等待内容更新时出错: {e}")


def is_filter_effective(before_items, after_items):
    """判断筛选是否生效"""
    if len(before_items) != len(after_items):
        return True

    if not before_items or not after_items:
        return False

    # 检查第一个条目是否变化
    return before_items[0]['id'] != after_items[0]['id']


async def reset_filter_to_unlimited(page, filter_container):
    """重置筛选器到'不限'状态"""
    try:
        filter_input = await filter_container.query_selector("input.el-input__inner")
        await filter_input.click()

        await filter_container.wait_for_selector("i.el-icon-arrow-up.is-reverse", timeout=5000)

        visible_dropdown = await find_visible_dropdown(page)
        if visible_dropdown:
            unlimited_option = await visible_dropdown.query_selector("li.el-select-dropdown__item span:has-text('不限')")
            if unlimited_option:
                await unlimited_option.click()
                await page.wait_for_timeout(500)

    except Exception as e:
        print(f"      -> 重置筛选器失败: {e}")


async def find_visible_dropdown(page):
    """查找当前可见的下拉菜单"""
    all_dropdowns = await page.query_selector_all("div.el-select-dropdown.pos-filter-pc__select-dropdown")
    for dropdown in all_dropdowns:
        placement = await dropdown.get_attribute("x-placement")
        if placement:
            return dropdown
    return None


async def reset_all_filters_to_unlimited(page, all_filter_names, current_filter=None):
    """重置所有筛选器到'不限'状态，除了当前正在处理的筛选器"""
    for filter_name in all_filter_names:
        if current_filter and filter_name == current_filter:
            continue  # 跳过当前正在处理的筛选器

        try:
            filter_container = await page.query_selector(f"div.el-select.pos-filter-pc__select:has(input[placeholder='{filter_name}'])")
            if filter_container:
                await reset_filter_to_unlimited(page, filter_container)
                print(f"    -> 已重置筛选器 {filter_name} 到'不限'")
        except Exception as e:
            print(f"    -> 重置筛选器 {filter_name} 失败: {e}")


async def fetch_items_for_category_basic(page, category):
    """
    基础模式：抓取条目链接（无标签）- 保持向后兼容
    """
    category_url = category["url"]
    print(f"  -> 正在抓取分类 '{category['name']}' 的条目链接（基础模式）...")

    html_content = await page.content()
    soup = BeautifulSoup(html_content, 'html.parser')

    # 定位到内容主容器
    content_container = soup.select_one("div.channel-content-container")
    if not content_container:
        print(f"  -> 警告：在分类 '{category['name']}' 页面上未能找到内容容器。")
        return []

    items_list = []

    # 在主容器内查找所有符合条件的 a 标签
    link_tags = content_container.find_all("a", href=re.compile(r"/ys/obc/content/\d+/detail"))

    for a_tag in link_tags:
        relative_url = a_tag.get("href")
        if not relative_url:
            continue

        # 拼接完整 URL
        full_url = urljoin(BASE_URL, relative_url)

        # 从 href 中提取条目 ID
        id_match = re.search(r'/content/(\d+)/detail', relative_url)
        if not id_match:
            continue
        item_id = id_match.group(1)

        # 提取条目名称
        title_tag = a_tag.select_one('[class*="title"]')
        if title_tag:
            item_name = title_tag.get_text(strip=True)
        else:
            h5_tag = a_tag.find("h5")
            if h5_tag:
                item_name = h5_tag.get_text(strip=True)
            else:
                item_name = "未知名称"

        items_list.append({
            "id": item_id,
            "name": item_name,
            "url": full_url
        })

    # 保存基础版本
    safe_category_name = sanitize_filename(category["name"])
    output_filename = f'{OUTPUT_DIR}/{category["id"]}_{safe_category_name}.json'

    try:
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(items_list, f, ensure_ascii=False, indent=2)
        print(f" -> 成功保存 {len(items_list)} 个条目链接到: {output_filename}")
    except Exception as e:
        print(f"  -> 错误：保存文件 {output_filename} 失败: {e}")

    return items_list


async def main():
    """主函数，协调整个抓取流程。"""
    print("--- 开始执行原神百科链接抓取任务 (Playwright 版本) ---")

    # 启动 Playwright
    async with async_playwright() as p:
        # 启动浏览器 (可以设置 headless=False 来查看浏览器操作)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 确保输出目录存在
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        print(f"确保输出目录 '{OUTPUT_DIR}' 存在。")

        # 第一步：获取所有分类
        all_categories = await fetch_categories(page)
        if not all_categories:
            print("未能获取到任何分类信息，程序退出。")
            await browser.close()
            return

        # 将所有分类信息也保存一份
        try:
            with open(os.path.join(OUTPUT_DIR, "categories.json"), 'w', encoding='utf-8') as f:
                json.dump(all_categories, f, ensure_ascii=False, indent=2)
            print(f"所有分类信息已保存到: {os.path.join(OUTPUT_DIR, 'categories.json')}")
        except Exception as e:
            print(f"保存分类信息文件失败: {e}")

        # 第二步：遍历每个分类，获取其下的条目（带标签）
        processed_count = 0
        for category in all_categories:
            print(f"\n--- 处理分类: {category['name']} (ID: {category['id']}) ---")
            items = await fetch_items_with_tags_for_category(page, category)
            processed_count += len(items)
            # (可选) 在每个请求之间加入短暂延迟，防止IP被封
            await asyncio.sleep(2)

        await browser.close()

    print(f"\n--- 链接抓取任务完成 ---")
    print(f"总计处理了 {len(all_categories)} 个分类，抓取了 {processed_count} 个条目链接。")


# 脚本入口
if __name__ == "__main__":
    asyncio.run(main())