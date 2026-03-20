"""
增量解析所有条目脚本 - HSR Wiki Scraper 版本。

该脚本会遍历 'categorized_links/' 目录中的所有链接文件，
对每个文件中所有条目执行爬取和解析操作。
如果对应条目的 JSON 文件已经存在，则跳过该条目。

生成的结构化 JSON 数据将保存到 'structured_data/{parser_id}/'。

这提供了一个完整的增量更新系统，只处理缺失的文件。
"""

import asyncio
import json
from pathlib import Path
from difflib import SequenceMatcher

# 使用相对导入，因为此脚本旨在作为模块运行。
from .central_hub import WikiPageCoordinator
from .template_generator import TemplateGenerator
from playwright.async_api import async_playwright


def compare_json_similarity(json_str1, json_str2, threshold=0.8):
    """
    比较两个JSON字符串的相似度

    Args:
        json_str1: 第一个JSON字符串
        json_str2: 第二个JSON字符串
        threshold: 相似度阈值，默认0.8 (80%)

    Returns:
        bool: 是否相似（相似度 >= threshold）
    """
    if not json_str1 or not json_str2:
        return False

    similarity = SequenceMatcher(None, json_str1, json_str2).ratio()
    return similarity >= threshold


async def run_all_parsers_incremental():
    """
    增量解析所有条目的主函数。
    只处理缺失的文件，已存在的文件会被跳过。
    只处理指定的 parser ID：18, 30, 31, 20, 53, 54, 55, 25, 157, 103
    """
    # --- 0. 生成JSON模板文件 ---
    print("正在生成HSR Wiki Scraper的JSON模板文件...")

    # 当作为模块运行时，__file__ 指向包内的文件
    # 项目根目录是当前包目录的父目录
    project_root = Path(__file__).parent.parent

    # 创建模板生成器并生成模板
    parsers_dir = project_root / "hsr_wiki_scraper" / "parsers"
    templates_dir = project_root / "hsr_wiki_scraper" / "output" / "templates"

    template_generator = TemplateGenerator(parsers_dir, templates_dir)
    template_generator.generate_all_templates()

    # 定义允许处理的 parser ID 列表
    allowed_parser_ids = [18, 19, 30, 31, 20, 53, 54, 55, 25, 157, 103]

    # --- 1. 定义路径 ---
    link_dir = project_root / "hsr_wiki_scraper" / "output" / "link"
    link_dir = project_root / "hsr_wiki_scraper" / "output" / "link"
    output_base_dir = project_root / "hsr_wiki_scraper" / "output" / "structured_data"
    debug_dir = project_root / "hsr_wiki_scraper" / "output" / "debug"

    # 确保输出目录存在
    output_base_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)

    # --- 2. 发现链接文件 ---
    link_files = sorted(link_dir.glob("*.json"))
    if not link_files:
        print(f"错误: 在 '{link_dir}' 中未找到 .json 文件。")
        return

    # 过滤只保留指定ID的文件
    filtered_files = []
    for file_path in link_files:
        file_stem = file_path.stem  # 获取不带扩展名的文件名
        try:
            # 提取文件名开头的数字ID
            parser_id = int(file_stem.split('_')[0])
            if parser_id in allowed_parser_ids:
                filtered_files.append(file_path)
                print(f"包含文件: {file_path.name} (ID: {parser_id})")
            else:
                print(f"跳过文件: {file_path.name} (ID: {parser_id} 不在允许列表中)")
        except (ValueError, IndexError):
            # 如果文件名格式不符合预期，跳过
            print(f"跳过文件: {file_path.name} (文件名格式不符合预期)")
            continue

    link_files = filtered_files

    if not link_files:
        print(f"错误: 没有找到符合条件的链接文件。允许的 parser ID: {allowed_parser_ids}")
        return

    print(f"过滤后找到 {len(link_files)} 个链接文件待处理。")

    # --- 3. 启动共享浏览器 ---
    print("正在启动共享浏览器...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        print("共享浏览器启动成功。")

        try:
            # --- 4. 初始化协调器（传入共享浏览器）---
            coordinator = WikiPageCoordinator(shared_browser=browser)

            # --- 5. 初始化统计 ---
            total_entries = 0
            processed_entries = 0
            skipped_entries = 0

            # --- 6. 处理每个链接文件 ---
            for link_file_path in link_files:
                try:
                    print(f"\n--- 正在处理链接文件: {link_file_path.name} ---")

                    # --- a. 加载链接文件 ---
                    with open(link_file_path, 'r', encoding='utf-8') as f:
                        link_data = json.load(f)

                    # --- b. 检查空文件 ---
                    if not link_data:
                        print(f"  -> 警告: '{link_file_path.name}' 为空。跳过。")
                        continue

                    print(f"  -> 找到 {len(link_data)} 个条目待处理。")

                    # --- c. 配置解析器 ID ---
                    # HSR 的文件名就是 parser_id (例如, "18_角色.json")
                    parser_id = link_file_path.stem

                    if parser_id not in coordinator.registered_parsers:
                        print(f"  -> 错误: 未找到解析器 '{parser_id}'。可用解析器: {list(coordinator.registered_parsers.keys())}")
                        continue # 跳过此文件

                    # 使用原始文件名词干作为输出目录
                    output_dir = output_base_dir / parser_id

                    # 确保特定解析器的输出目录存在
                    output_dir.mkdir(parents=True, exist_ok=True)

                    # --- d. 初始化智能增量更新标志 ---
                    found_duplicate = False
                    updated_count = 0
                    skipped_by_duplicate = 0

                    # --- e. 处理每个条目 ---
                    # 新的 JSON 格式是数组: [{"id": "xxx", "name": "xxx", "url": "xxx", "tags": {}}]
                    for item in link_data:
                        total_entries += 1
                        entry_id = item["id"]
                        entry_name = item["name"]
                        url = item["url"]

                        # 检查输出文件是否已存在
                        output_file = output_dir / f"{entry_id}.json"

                        # 智能增量更新逻辑
                        if found_duplicate and output_file.exists():
                            # 已发现重复内容，只处理不存在的文件
                            print(f"  -> 跳过条目 {entry_id}: 文件已存在（重复后模式）")
                            skipped_entries += 1
                            skipped_by_duplicate += 1
                            continue

                        # 无论是否存在，都要先抽取内容（在found_duplicate=False时）

                        mode_text = "重复后模式" if found_duplicate else "更新模式"
                        print(f"  -> 正在处理条目 {entry_id} ({entry_name}) [{mode_text}]")
                        print(f"    -> 输出文件路径: {output_file}")

                        try:
                            # --- e. 爬取、预处理和解析 ---
                            print(f"    -> 使用解析器 ID 调用协调器: {parser_id}")
                            # 设置30秒超时
                            json_result = await coordinator.scrape_and_parse(url, parser_id, timeout=30)

                            # --- f. 检查结果是否包含错误信息 ---
                            if isinstance(json_result, dict) and "error" in json_result:
                                print(f"    -> 跳过保存: 解析结果包含错误信息: {json_result.get('error', '未知错误')}")
                                continue

                            # --- g. 检查结果是否为空或无效 ---
                            if not json_result or (isinstance(json_result, dict) and not json_result):
                                print(f"    -> 跳过保存: 解析结果为空")
                                continue

                            # --- h. 添加源URL到结果中 ---
                            if isinstance(json_result, dict):
                                json_result["source_url"] = url

                            # --- i. 检查是否与现有内容相同 ---
                            new_json_str = json.dumps(json_result, ensure_ascii=False, sort_keys=True)

                            if not found_duplicate and output_file.exists():
                                # 读取现有文件内容进行比较
                                try:
                                    with open(output_file, 'r', encoding='utf-8') as f:
                                        existing_data = json.load(f)
                                    existing_json_str = json.dumps(existing_data, ensure_ascii=False, sort_keys=True)

                                    if compare_json_similarity(new_json_str, existing_json_str):
                                        print(f"    -> 发现相同内容！切换到重复后模式")
                                        found_duplicate = True
                                        # 仍然更新这个文件，但下次循环就会跳过已存在的
                                except Exception as e:
                                    print(f"    -> 警告: 读取现有文件时出错: {e}，继续更新")

                            # --- j. 保存结果 ---
                            with open(output_file, 'w', encoding='utf-8') as f:
                                json.dump(json_result, f, indent=4, ensure_ascii=False)

                            print(f"    -> 成功! 输出已保存到: {output_file}")
                            processed_entries += 1
                            updated_count += 1

                        except asyncio.TimeoutError:
                            print(f"    -> 跳过条目 {entry_id}: 处理超时")
                            # 继续处理下一个条目
                        except Exception as e:
                            print(f"    -> 跳过条目 {entry_id}: 处理时发生错误: {e}")
                            # 继续处理下一个条目

                    # --- f. 输出分类处理统计 ---
                    print(f"  -> 分类 '{link_file_path.name}' 处理完成:")
                    print(f"    -> 总条目数: {len(link_data)}")
                    print(f"    -> 更新条目数: {updated_count}")
                    print(f"    -> 跳过条目数 (重复后模式): {skipped_by_duplicate}")
                    if found_duplicate:
                        print(f"    -> 已切换到重复后模式，后续只处理缺失文件")

                except FileNotFoundError:
                    print(f"  -> 错误: 在 {link_file_path} 未找到链接文件")
                except KeyError as e:
                    print(f"  -> 错误: 链接文件条目或文件名中缺少预期的键 {e}。")
                except Exception as e:
                    print(f"  -> 处理 '{link_file_path.name}' 时发生意外错误: {e}")
                    import traceback
                    traceback.print_exc()

            # --- 7. 输出统计信息 ---
            print(f"\n--- 处理完成 ---")
            print(f"总条目数: {total_entries}")
            print(f"处理条目数: {processed_entries}")
            print(f"跳过条目数: {skipped_entries}")

        finally:
            # --- 8. 关闭共享浏览器 ---
            print("正在关闭共享浏览器...")
            await browser.close()
            print("共享浏览器已关闭。")


if __name__ == "__main__":
    # 这允许脚本作为模块运行。
    asyncio.run(run_all_parsers_incremental())