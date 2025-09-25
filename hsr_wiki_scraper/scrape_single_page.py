import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import os
import re
import sys

# 从现有脚本中复用的辅助函数
def sanitize_filename(name):
    """将字符串转换为安全的文件名，以防万一需要用到。"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
    return name

async def fetch_page_content(page, url):
    """辅助函数，用于获取单个页面的内容并处理可能的导航错误。"""
    try:
        print(f"诊断日志: 正在导航到 {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        print("诊断日志: 页面加载完成")
        return await page.content()
    except Exception as e:
        print(f"警告：访问 {url} 时出错: {e}")
        return None

async def scrape_single_page(url):
    """
    抓取单个隐藏分类页面的脚本。
    1. 接收一个URL作为参数。
    2. 访问该URL。
    3. 定位活动内容板块并提取链接。
    4. 从页面获取分类ID和名称以生成文件名。
    5. 将结果保存到JSON文件。
    """
    base_url = "https://bbs.mihoyo.com"
    output_dir = "categorized_links"
    os.makedirs(output_dir, exist_ok=True)
    print(f"数据将保存到 '{output_dir}' 文件夹中。")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, timeout=90000)
        print("诊断日志: 浏览器已启动")
        page = await browser.new_page()
        print("诊断日志: 新页面已创建")

        try:
            print(f"正在访问页面: {url}")
            print("诊断日志: 开始调用 fetch_page_content")
            content = await fetch_page_content(page, url)
            print("诊断日志: fetch_page_content 调用完成")
            if not content:
                raise Exception("无法获取页面内容，程序终止。")

            print("诊断日志: 开始解析HTML内容")
            soup = BeautifulSoup(content, 'html.parser')
            print("诊断日志: HTML内容解析完成")

            # --- 提取分类ID和名称 ---
            # 从URL中提取ID
            id_match = re.search(r'/map/\d+/(\d+)', url)
            category_id = id_match.group(1) if id_match else "unknown_id"

            # 尝试从分页指示器中获取分类名称
            category_name = "未知分类"
            # 查找所有分页指示器
            pagination_bullets = soup.select("span.swiper-pagination-bullet")
            print(f"诊断日志: 找到 {len(pagination_bullets)} 个分页指示器")
            for bullet in pagination_bullets:
                # 检查哪个是当前活动的
                if 'swiper-pagination-bullet-active' in bullet.get('class', []):
                    category_name = bullet.get_text(strip=True)
                    break

            print(f"检测到分类ID: {category_id}, 名称: {category_name}")

            # --- 定位活动内容板块并提取链接 ---
            # 查找活动的内容板块
            target_slide = soup.select_one('li.swiper-slide-active')
            print(f"诊断日志: 活动内容板块查找结果: {'找到' if target_slide else '未找到'}")

            articles_data = {}
            if target_slide:
                link_tags = target_slide.select('a[href*="/sr/wiki/content/"]')
                id_pattern = re.compile(r'/content/(\d+)/detail')

                for tag in link_tags:
                    href = tag.get('href', '')
                    match = id_pattern.search(href)
                    if match:
                        article_id = match.group(1)
                        full_url = base_url + href if href.startswith('/') else href
                        if article_id not in articles_data:
                            articles_data[article_id] = full_url
            else:
                print("警告：未能找到活动的内容板块。")

            # --- 生成文件名并保存 ---
            safe_category_name = sanitize_filename(category_name)
            # 按照要求格式化文件名: _{ID}_{分类名}.json
            output_filename = f"_{category_id}_{safe_category_name}.json"
            output_path = os.path.join(output_dir, output_filename)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(articles_data, f, ensure_ascii=False, indent=2)

            print(f"找到 {len(articles_data)} 个唯一文章链接。数据已保存到: {output_path}")

        except Exception as e:
            print(f"\n处理过程中发生严重错误: {e}")
        finally:
            await browser.close()
            print("\n浏览器已关闭。")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python scrape_single_page.py <URL>")
        sys.exit(1)

    target_url = sys.argv[1]
    asyncio.run(scrape_single_page(target_url))