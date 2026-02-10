#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
一键生成所有内容
依次运行：
1. giwiki_generate_markdown.py
2. hsrwiki_generate_markdown.py
3. zzz_generate_markdown.py
4. generate_all_catalog_trees.py
"""

import subprocess
import sys
import logging
from pathlib import Path

# --- 配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 脚本列表
SCRIPTS = [
    ("giwiki_generate_markdown.py", "生成 GI Wiki Markdown 文件"),
    ("hsrwiki_generate_markdown.py", "生成 HSR Wiki Markdown 文件"),
    ("zzz_generate_markdown.py", "生成 ZZZ Wiki Markdown 文件"),
    ("generate_all_catalog_trees.py", "生成所有目录树和搜索索引"),
]


def run_script(script_name: str, description: str) -> bool:
    """
    运行指定的 Python 脚本

    Args:
        script_name: 脚本文件名
        description: 脚本描述

    Returns:
        是否成功
    """
    script_path = Path(__file__).parent / script_name

    if not script_path.exists():
        logging.error(f"脚本不存在: {script_path}")
        return False

    logging.info(f"\n{'='*60}")
    logging.info(f"开始执行: {description}")
    logging.info(f"脚本: {script_name}")
    logging.info(f"{'='*60}")

    try:
        # 使用 python 命令运行脚本
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            check=True,
            capture_output=False,
            text=True
        )
        logging.info(f"✓ {description} 完成")
        return True

    except subprocess.CalledProcessError as e:
        logging.error(f"✗ {description} 失败")
        logging.error(f"返回码: {e.returncode}")
        if e.stdout:
            logging.error(f"标准输出:\n{e.stdout}")
        if e.stderr:
            logging.error(f"标准错误:\n{e.stderr}")
        return False

    except Exception as e:
        logging.error(f"✗ {description} 执行时出错: {e}")
        return False


def main():
    """主函数"""
    logging.info("开始一键生成所有内容...")
    logging.info(f"项目根目录: {project_root}")

    success_count = 0
    failed_scripts = []

    # 依次运行所有脚本
    for script_name, description in SCRIPTS:
        if run_script(script_name, description):
            success_count += 1
        else:
            failed_scripts.append(script_name)

    # 总结
    logging.info(f"\n{'='*60}")
    logging.info("执行完成！")
    logging.info(f"{'='*60}")
    logging.info(f"成功: {success_count}/{len(SCRIPTS)}")

    if failed_scripts:
        logging.warning(f"失败的脚本: {', '.join(failed_scripts)}")
        sys.exit(1)
    else:
        logging.info("✓ 所有任务成功完成！")
        logging.info("\n生成的文件:")
        logging.info("  - Markdown 文件: web/docs-site/public/domains/*/docs/")
        logging.info("  - 目录索引: web/docs-site/public/domains/*/metadata/index.json")
        logging.info("  - 目录树: web/docs-site/public/domains/*/metadata/catalog.json")
        logging.info("  - 搜索索引: web/docs-site/public/domains/*/metadata/search/")
        sys.exit(0)


if __name__ == "__main__":
    main()