import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import os
import re
import random

def sanitize_filename(name):
    """将字符串转换为安全的文件名，以防万一需要用到。"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
    return name

async def fetch_page_content(page, url):
    """辅助函数，用于获取单个页面的内容并处理可能的导航错误。"""
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        return await page.content()
    except Exception as e:
        print(f"警告：访问 {url} 时出错: {e}")
        return None

async def scrape_links_and_ids():
    """
    最终版抓取脚本 (V3):
    1. 从主目录页获取所有分类的名称和数字ID。
    2. 遍历每个分类，访问其专属页面。
    3. 使用通用选择器 `a[href*="/sr/wiki/content/"]` 抓取所有内容链接。
    4. 从每个链接中提取唯一的文章ID。
    5. 将结果以 {文章ID: URL} 的格式，保存到以分类ID命名的JSON文件中。
    """
    base_url = "https://bbs.mihoyo.com"
    map_url = "https://bbs.mihoyo.com/sr/wiki/channel/map/17?bbs_presentation_style=no_header"

    output_dir = "output/link"
    os.makedirs(output_dir, exist_ok=True)
    print(f"数据将保存到 '{output_dir}' 文件夹中。")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        categories = []
        try:
            # --- 第一步：获取所有分类的元数据 ---
            print(f"正在从主目录页获取所有分类信息: {map_url}")
            content = await fetch_page_content(page, map_url)
            if not content:
                raise Exception("无法获取主目录页内容，程序终止。")

            soup = BeautifulSoup(content, 'html.parser')
            category_tabs = soup.select("span.swiper-pagination-bullet")
            if not category_tabs:
                raise Exception("在主目录页上未能找到任何分类标签！")

            for tab in category_tabs:
                cat_name = tab.get_text(strip=True)
                cat_id_raw = tab.get('id', '')
                aria_label = tab.get('aria-label', '')

                id_match = re.search(r'_position_(\d+)', cat_id_raw)
                slide_match = re.search(r'Go to slide (\d+)', aria_label)

                if cat_name and id_match and slide_match:
                    # 将 1-based 索引转换为 0-based
                    slide_index = int(slide_match.group(1)) - 1
                    categories.append({
                        'name': cat_name,
                        'id': id_match.group(1),
                        'slide_index': slide_index
                    })

            print(f"成功获取到 {len(categories)} 个分类。")

            # --- 第二步 & 第三步：遍历、提取、存储 ---
            for category in categories:
                cat_name = category['name']
                cat_id = category['id']

                print(f"\n--- 正在处理分类: '{cat_name}' (ID: {cat_id}) ---")
                category_url = f"https://bbs.mihoyo.com/sr/wiki/channel/map/17/{cat_id}?bbs_presentation_style=no_header"

                cat_content = await fetch_page_content(page, category_url)
                if not cat_content:
                    print(f"跳过分类 '{cat_name}'，因为无法获取其页面内容。")
                    continue

                cat_soup = BeautifulSoup(cat_content, 'html.parser')
                slide_index = category['slide_index']

                # 使用 slide_index 精确地定位到当前分类的内容板块
                target_slide = cat_soup.select_one(f'li[data-swiper-slide-index="{slide_index}"]')

                link_tags = []
                if target_slide:
                    # 只在目标板块内部查找链接
                    link_tags = target_slide.select('a[href*="/sr/wiki/content/"]')
                else:
                    print(f"警告：在分类 '{cat_name}' 中未能找到索引为 {slide_index} 的内容板块。")

                articles_data = {}
                id_pattern = re.compile(r'/content/(\d+)/detail')

                for tag in link_tags:
                    href = tag.get('href', '')
                    match = id_pattern.search(href)
                    if match:
                        article_id = match.group(1)
                        full_url = base_url + href if href.startswith('/') else href
                        if article_id not in articles_data:
                            articles_data[article_id] = full_url
                # 使用“ID_分类名”作为文件名，更具可读性
                safe_cat_name = sanitize_filename(cat_name)
                output_path = os.path.join(output_dir, f"{cat_id}_{safe_cat_name}.json")
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(articles_data, f, ensure_ascii=False, indent=2)

                print(f"分类 '{cat_name}' 找到 {len(articles_data)} 个唯一文章链接。数据已保存到: {output_path}")

                # 加入随机延迟，模拟人类行为
                delay = random.uniform(0.5, 1.5)
                await asyncio.sleep(delay)

        except Exception as e:
            print(f"\n处理过程中发生严重错误: {e}")
        finally:
            await browser.close()
            print("\n浏览器已关闭。所有任务完成。")

if __name__ == "__main__":
    asyncio.run(scrape_links_and_ids())