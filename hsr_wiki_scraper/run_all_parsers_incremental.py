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

# 使用相对导入，因为此脚本旨在作为模块运行。
from .central_hub import WikiPageCoordinator
from playwright.async_api import async_playwright


async def run_all_parsers_incremental():
    """
    增量解析所有条目的主函数。
    只处理缺失的文件，已存在的文件会被跳过。
    只处理指定的 parser ID：18, 30, 31, 20, 53, 54, 55, 25, 157, 103
    """
    # 定义允许处理的 parser ID 列表
    allowed_parser_ids = [18, 30, 31, 20, 53, 54, 55, 25, 157, 103]
    
    # --- 1. 定义路径 ---
    # 当作为模块运行时，__file__ 指向包内的文件
    # 项目根目录是当前包目录的父目录
    project_root = Path(__file__).parent.parent
    link_dir = project_root / "hsr_wiki_scraper" / "output" / "links"
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

                    # --- d. 处理每个条目 ---
                    # HSR 的 JSON 格式是 {"entry_id": "url", ...}
                    for entry_id, url in link_data.items():
                        total_entries += 1
                        entry_name = entry_id  # HSR 中使用 entry_id 作为名称

                        # 检查输出文件是否已存在
                        output_file = output_dir / f"{entry_id}.json"
                        if output_file.exists():
                            print(f"  -> 跳过条目 {entry_id}: 文件已存在 {output_file}")
                            skipped_entries += 1
                            continue

                        print(f"  -> 正在处理条目 {entry_id} ({entry_name})")
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

                            # --- i. 保存结果 ---
                            with open(output_file, 'w', encoding='utf-8') as f:
                                json.dump(json_result, f, indent=4, ensure_ascii=False)

                            print(f"    -> 成功! 输出已保存到: {output_file}")
                            processed_entries += 1

                        except asyncio.TimeoutError:
                            print(f"    -> 跳过条目 {entry_id}: 处理超时")
                            # 继续处理下一个条目
                        except Exception as e:
                            print(f"    -> 跳过条目 {entry_id}: 处理时发生错误: {e}")
                            # 继续处理下一个条目

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