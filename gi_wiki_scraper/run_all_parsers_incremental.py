"""
增量解析所有条目脚本。

该脚本会遍历 'link/' 目录中的所有链接文件，
对每个文件中所有条目执行爬取和解析操作。
如果对应条目的 JSON 文件已经存在，则跳过该条目。

生成的结构化 JSON 数据将保存到 'gi_wiki_scraper/output/structured_data/{parser_id}/'。

这提供了一个完整的增量更新系统，只处理缺失的文件。
"""

import asyncio
import json
from pathlib import Path

# 使用相对导入，因为此脚本旨在作为模块运行。
from .central_hub import WikiPageCoordinator
from playwright.async_api import async_playwright


async def run_all_parsers_incremental():
    """
    增量解析所有条目的主函数。
    只处理缺失的文件，已存在的文件会被跳过。
    """
    # --- 1. 定义路径 ---
    # 项目根目录是 'gi_wiki_scraper' 包目录的父目录。
    project_root = Path(__file__).parent.parent
    link_dir = project_root / "gi_wiki_scraper" / "output" / "link"
    output_base_dir = project_root / "gi_wiki_scraper" / "output" / "structured_data"
    debug_dir = project_root / "gi_wiki_scraper" / "output" / "debug"

    # 确保输出目录存在
    output_base_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)

    # --- 2. 发现链接文件 ---
    link_files = sorted(link_dir.glob("*.json"))
    if not link_files:
        print(f"错误: 在 '{link_dir}' 中未找到 .json 文件。")
        return

    print(f"找到 {len(link_files)} 个链接文件待处理。")

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

            # --- 6. 定义要处理的ID列表 ---
            allowed_ids = {5, 6, 13, 20, 21, 25, 43, 49, 54, 55, 68, 211, 218, 227, 251, 255, 261}

            # --- 7. 处理每个链接文件 ---
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

                    # --- c. 检查是否为允许的ID ---
                    # 链接文件名以数字开头 (例如, "105_活动.json")。
                    category_prefix = link_file_path.stem.split('_')[0]
                    try:
                        category_id = int(category_prefix)
                    except ValueError:
                        print(f"  -> 跳过: 无法解析文件名中的ID '{category_prefix}'")
                        continue

                    if category_id not in allowed_ids:
                        print(f"  -> 跳过: ID {category_id} 不在允许的ID列表中")
                        continue

                    # --- d. 配置解析器 ID ---
                    # 通过精确匹配数字前缀找到完整的 parser_id，避免部分匹配问题
                    # 例如：避免 "25" 匹配到 "251_xxx_parser"
                    matching_parser_ids = [pid for pid in coordinator.registered_parsers.keys()
                                         if pid.split('_')[0] == category_prefix]

                    if not matching_parser_ids:
                        print(f"  -> 错误: 未找到类别前缀 '{category_prefix}' 的解析器。可用解析器: {list(coordinator.registered_parsers.keys())}")
                        continue # 跳过此文件
                    elif len(matching_parser_ids) > 1:
                        print(f"  -> 警告: 找到类别前缀 '{category_prefix}' 的多个解析器: {matching_parser_ids}。使用第一个: {matching_parser_ids[0]}。")

                    parser_id = matching_parser_ids[0]
                    # 使用原始文件名词干作为输出目录
                    output_dir = output_base_dir / link_file_path.stem

                    # 确保特定解析器的输出目录存在
                    output_dir.mkdir(parents=True, exist_ok=True)

                    # --- e. 处理每个条目 ---
                    for entry in link_data:
                        total_entries += 1
                        entry_id = entry["id"]
                        entry_name = entry["name"]
                        url = entry["url"]

                        # 检查输出文件是否已存在
                        output_file = output_dir / f"{entry_id}.json"
                        if output_file.exists():
                            skipped_entries += 1
                            continue

                        print(f"  -> 正在处理条目 {entry_id} ({entry_name})")

                        # --- f. 重试机制 ---
                        max_retries = 3
                        retry_delay = 5  # 5秒延迟

                        for attempt in range(max_retries):
                            try:
                                # --- g. 爬取、预处理和解析 ---
                                if attempt > 0:
                                    print(f"    -> 重试第 {attempt} 次...")
                                    await asyncio.sleep(retry_delay)

                                print(f"    -> 使用解析器 ID 调用协调器: {parser_id}")
                                # 设置30秒超时
                                json_result = await coordinator.scrape_and_parse(url, parser_id, timeout=30)

                                # --- h. 检查结果是否包含错误信息 ---
                                if isinstance(json_result, dict) and "error" in json_result:
                                    if attempt < max_retries - 1:
                                        print(f"    -> 解析结果包含错误信息: {json_result.get('error', '未知错误')}，将重试...")
                                        continue
                                    else:
                                        print(f"    -> 跳过保存: 解析结果包含错误信息: {json_result.get('error', '未知错误')}")
                                        break

                                # --- i. 检查结果是否为空或无效 ---
                                if not json_result or (isinstance(json_result, dict) and not json_result):
                                    if attempt < max_retries - 1:
                                        print(f"    -> 解析结果为空，将重试...")
                                        continue
                                    else:
                                        print(f"    -> 跳过保存: 解析结果为空")
                                        break

                                # --- j. 保存结果 ---
                                with open(output_file, 'w', encoding='utf-8') as f:
                                    json.dump(json_result, f, indent=4, ensure_ascii=False)

                                print(f"    -> 成功! 输出已保存到: {output_file}")
                                processed_entries += 1
                                break  # 成功后跳出重试循环

                            except asyncio.TimeoutError:
                                if attempt < max_retries - 1:
                                    print(f"    -> 处理超时，将在 {retry_delay} 秒后重试...")
                                else:
                                    print(f"    -> 跳过条目 {entry_id}: 处理超时（已重试 {max_retries} 次）")
                            except Exception as e:
                                if attempt < max_retries - 1:
                                    print(f"    -> 处理时发生错误: {e}，将在 {retry_delay} 秒后重试...")
                                else:
                                    print(f"    -> 跳过条目 {entry_id}: 处理时发生错误: {e}（已重试 {max_retries} 次）")

                except FileNotFoundError:
                    print(f"  -> 错误: 在 {link_file_path} 未找到链接文件")
                except KeyError as e:
                    print(f"  -> 错误: 链接文件条目或文件名中缺少预期的键 {e}。")
                except Exception as e:
                    print(f"  -> 处理 '{link_file_path.name}' 时发生意外错误: {e}")
                    import traceback
                    traceback.print_exc()

            # --- 8. 输出统计信息 ---
            print(f"\n--- 处理完成 ---")
            print(f"总条目数: {total_entries}")
            print(f"处理条目数: {processed_entries}")
            print(f"跳过条目数: {skipped_entries}")

        finally:
            # --- 9. 关闭共享浏览器 ---
            print("正在关闭共享浏览器...")
            await browser.close()
            print("共享浏览器已关闭。")


if __name__ == "__main__":
    # 这允许脚本作为模块运行。
    asyncio.run(run_all_parsers_incremental())