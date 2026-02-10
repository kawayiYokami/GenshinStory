#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一的目录树和搜索索引生成脚本
一次性为 GI、HSR、ZZZ 三个游戏目录生成 catalog.json 和搜索索引
"""

import json
import re
import msgpack
from pathlib import Path
import logging
import sys
from typing import Dict, List, Any, Set
from collections import defaultdict

# --- 配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 游戏配置
GAME_CONFIGS = {
    "gi": {
        "domain": "gi",
        "md_root_dir": project_root / "web/docs-site/public/domains/gi/docs",
        "index_output_path": project_root / "web/docs-site/public/domains/gi/metadata/index.json",
        "output_path": project_root / "web/docs-site/public/domains/gi/metadata/catalog.json",
        "md_root_prefix": "/domains/gi/docs",
        "search_output_dir": project_root / "web/docs-site/public/domains/gi/metadata/search"
    },
    "hsr": {
        "domain": "hsr",
        "md_root_dir": project_root / "web/docs-site/public/domains/hsr/docs",
        "index_output_path": project_root / "web/docs-site/public/domains/hsr/metadata/index.json",
        "output_path": project_root / "web/docs-site/public/domains/hsr/metadata/catalog.json",
        "md_root_prefix": "/domains/hsr/docs",
        "search_output_dir": project_root / "web/docs-site/public/domains/hsr/metadata/search"
    },
    "zzz": {
        "domain": "zzz",
        "md_root_dir": project_root / "web/docs-site/public/domains/zzz/docs",
        "index_output_path": project_root / "web/docs-site/public/domains/zzz/metadata/index.json",
        "output_path": project_root / "web/docs-site/public/domains/zzz/metadata/catalog.json",
        "md_root_prefix": "/domains/zzz/docs",
        "search_output_dir": project_root / "web/docs-site/public/domains/zzz/metadata/search"
    }
}


# --- 辅助函数 ---

def delta_encode(sorted_ids):
    """差值编码：将排序ID转换为相邻差值"""
    if not sorted_ids or len(sorted_ids) == 0:
        return []

    deltas = [sorted_ids[0]]  # 第一个ID保持原值
    for i in range(1, len(sorted_ids)):
        deltas.append(sorted_ids[i] - sorted_ids[i-1])
    return deltas


def clean_text_for_search(text: str) -> str:
    """清洗文本，移除标点符号、特殊字符，并转换为小写"""
    if not text:
        return ""

    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 移除markdown标题
    text = re.sub(r'#+\s?', '', text)
    # 移除粗体标记
    text = re.sub(r'(\*\*|__)(.*?)(\*\*|__)', r'\2', text)
    # 移除斜体标记
    text = re.sub(r'(\*|_)(.*?)(\*|_)', r'\2', text)
    # 移除链接，保留文本
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # 只保留中文、日文、韩文、英文、数字和空格
    text = re.sub(r'[^\u4e00-\u9fa5\u3040-\u30ff\uac00-\ud7a3a-zA-Z0-9\s]', '', text)
    # 移除所有空格
    text = re.sub(r'\s+', '', text)
    return text.lower()


def generate_ngrams(text: str, n: int = 2) -> Set[str]:
    """为给定的文本生成二元词条集合"""
    if len(text) < n:
        return set()
    return {text[i:i+n] for i in range(len(text)-n+1)}


def get_physical_path(item: Dict[str, Any], md_root_prefix: str, domain: str) -> str:
    """从索引条目动态构建物理路径"""
    frontend_path = item.get("path", "")
    parts = frontend_path.split('/')

    # 兼容不同的路径格式
    # GI/ZZZ: /v2/{domain}/category/...
    # HSR: /v2/{domain}/category/...
    if len(parts) < 5:
        return None

    # parts[0] is empty, [1] is 'v2', [2] is domain, [3] is 'category'
    relative_path = "/".join(parts[4:])
    # 添加 web/docs-site/public 前缀
    return f"web/docs-site/public{md_root_prefix}/{relative_path}.md"


def create_catalog_tree(index_data: List[Dict[str, Any]], output_path: Path, md_root_prefix: str, domain: str):
    """
    从主索引数据创建目录树

    Args:
        index_data: 目录索引数据
        output_path: 输出文件路径
        md_root_prefix: Markdown 根目录前缀
        domain: 游戏域名
    """
    logging.info(f"开始构建 {domain} 目录树，共 {len(index_data)} 条索引条目...")

    catalog_tree = {}
    for item in index_data:
        physical_path = get_physical_path(item, md_root_prefix, domain)
        if not physical_path:
            continue

        path_parts = physical_path.replace(md_root_prefix, "", 1).strip("/").split("/")

        current_level = catalog_tree
        for i, part in enumerate(path_parts):
            if i == len(path_parts) - 1:
                current_level[part] = None  # File
            else:
                if part not in current_level:
                    current_level[part] = {}  # Directory
                current_level = current_level[part]

    logging.info(f"正在将生成的目录树写入 {output_path}...")
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(catalog_tree, f, ensure_ascii=False, indent=2)
        logging.info(f"{domain} 目录树生成成功！")
    except Exception as e:
        logging.error(f"写入目录树时出错: {e}")
        sys.exit(1)


def scan_markdown_files(md_root_dir: Path, domain: str) -> List[Dict[str, Any]]:
    """
    扫描所有 Markdown 文件，提取元数据生成索引

    Args:
        md_root_dir: Markdown 根目录
        domain: 游戏域名

    Returns:
        索引数据列表
    """
    logging.info(f"开始扫描 {domain} 的 Markdown 文件...")
    index_data = []

    # 遍历所有 Markdown 文件
    for md_file in md_root_dir.rglob("*.md"):
        try:
            # 读取文件内容
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取元数据（从文件名和路径）
            relative_path = md_file.relative_to(md_root_dir)
            path_parts = list(relative_path.parts)

            # 解析路径：category/subcategory/filename.md 或 category/filename.md
            if len(path_parts) >= 2:
                category = path_parts[0]
                filename = path_parts[-1]
                
                # 提取 ID 和名称
                # 文件名格式：name-id.md 或 name.md
                stem = filename[:-3]  # 去掉 .md
                
                # 尝试提取 ID（文件名末尾的数字）
                import re
                id_match = re.search(r'-(\d+)$', stem)
                if id_match:
                    item_id = int(id_match.group(1))
                    item_name = stem[:id_match.start()]
                else:
                    # 如果没有 ID，使用文件名作为 ID（转换为数字哈希）
                    item_id = hash(stem) % (10 ** 9)
                    item_name = stem

                # 确定子分类（如果有）
                # 只有当路径是 category/subcategory/name-id.md 时才有子分类
                # 如果是 category/name-id.md，则使用 "未分类" 作为默认子分类
                if len(path_parts) >= 3:
                    sub_category = path_parts[1]
                else:
                    sub_category = "未分类"

                # 构建 URL 路径（去掉 .md 后缀）
                # 有子分类：/v2/{domain}/category/{category}/{subcategory}/{name-id}
                # 无子分类：/v2/{domain}/category/{category}/{name-id}
                if len(path_parts) >= 3:
                    url_path = f"/v2/{domain}/category/{category}/{sub_category}/{stem}"
                    key = f"{category}-{sub_category}-{item_id}"
                else:
                    url_path = f"/v2/{domain}/category/{category}/{stem}"
                    key = f"{category}-{item_id}"

                # 添加到索引
                index_item = {
                    "id": item_id,
                    "name": item_name,  # 保持原样，不替换 -
                    "type": category.capitalize(),  # 首字母大写
                    "category": sub_category,  # 所有文件都有 category 字段
                    "path": url_path,
                    "key": key
                }
                
                index_data.append(index_item)

        except Exception as e:
            logging.error(f"处理文件 {md_file} 时出错: {e}")
            continue

    logging.info(f"扫描完成，共找到 {len(index_data)} 个 Markdown 文件")
    return index_data


def generate_search_index(index_data: List[Dict[str, Any]], search_output_dir: Path, md_root_prefix: str, domain: str):
    """
    从 Markdown 文件生成搜索索引

    Args:
        index_data: 目录索引数据，包含所有条目的元数据
        search_output_dir: 搜索索引输出目录
        md_root_prefix: Markdown 根目录前缀
        domain: 游戏域名
    """
    logging.info(f"开始为 {domain} 生成搜索索引...")

    # 初始化搜索索引
    search_index: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    # 遍历所有索引条目
    for item in index_data:
        item_id = item.get("id")
        item_name = item.get("name")
        item_type = item.get("type")

        if not item_id or not item_name:
            continue

        # 构建物理文件路径
        physical_path = get_physical_path(item, md_root_prefix, domain)
        if not physical_path:
            continue

        md_file_path = project_root / physical_path.lstrip("/")

        # 读取 Markdown 文件内容
        try:
            if not md_file_path.exists():
                logging.warning(f"Markdown 文件不存在: {md_file_path}")
                continue

            with open(md_file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

        except Exception as e:
            logging.error(f"读取文件 {md_file_path} 时出错: {e}")
            continue

        # 清洗内容
        cleaned_content = clean_text_for_search(markdown_content)
        if not cleaned_content:
            continue

        # 索引名称
        cleaned_name = clean_text_for_search(item_name)
        if cleaned_name:
            for token in generate_ngrams(cleaned_name):
                context = {'id': item_id, 'name': item_name, 'type': item_type}
                if context not in search_index[token]:
                    search_index[token].append(context)
            # 短名称也作为整体索引
            if len(cleaned_name) <= 5:
                context = {'id': item_id, 'name': item_name, 'type': item_type}
                if context not in search_index[cleaned_name]:
                    search_index[cleaned_name].append(context)

        # 索引内容
        for token in generate_ngrams(cleaned_content):
            context = {'id': item_id, 'name': item_name, 'type': item_type}
            if context not in search_index[token]:
                search_index[token].append(context)

    logging.info(f"{domain} 搜索索引构建完成，共 {len(search_index)} 个词条")

    # 导出优化索引（差值编码 + MessagePack）
    if not search_index:
        logging.error(f"{domain} 搜索索引为空，无法导出")
        return

    # 处理搜索索引，按第一个字符分组并差值编码
    chunked_index = {}
    for keyword, results in search_index.items():
        if not keyword:
            continue
        first_char = keyword[0]
        if first_char not in chunked_index:
            chunked_index[first_char] = {}

        # 提取ID、排序并差值编码
        sorted_ids = sorted(set(int(item['id']) for item in results))
        chunked_index[first_char][keyword] = delta_encode(sorted_ids)

    # 生成MessagePack文件
    if search_output_dir.exists():
        import shutil
        shutil.rmtree(search_output_dir)
        logging.info(f"已清理旧的索引目录: {search_output_dir}")
    search_output_dir.mkdir(parents=True, exist_ok=True)

    # 完整索引文件
    index_data_msg = msgpack.packb(chunked_index, use_bin_type=True)
    with open(search_output_dir / "index.msg", "wb") as f:
        f.write(index_data_msg)

    # 元数据文件
    metadata = {
        "version": "2.0",
        "format": "delta+msgpack",
        "keywords": len(chunked_index),
        "total_ids": sum(len(chunk) for chunk in chunked_index.values()),
        "chunks": len(chunked_index)
    }

    metadata_data = msgpack.packb(metadata, use_bin_type=True)
    with open(search_output_dir / "metadata.msg", "wb") as f:
        f.write(metadata_data)

    size_mb = len(index_data_msg) / (1024 * 1024)
    logging.info(f"{domain} 优化索引已生成: {size_mb:.1f}MB")
    logging.info(f"  索引文件: {search_output_dir / 'index.msg'}")
    logging.info(f"  元数据文件: {search_output_dir / 'metadata.msg'}")
    logging.info(f"  分片数量: {len(chunked_index)}")
    logging.info(f"  词条总数: {sum(len(chunk) for chunk in chunked_index.values())}")


def process_domain(domain: str, config: Dict[str, Any]):
    """
    处理单个游戏域的目录树和搜索索引生成

    Args:
        domain: 游戏域名
        config: 游戏配置
    """
    logging.info(f"\n{'='*60}")
    logging.info(f"开始处理游戏域: {domain.upper()}")
    logging.info(f"{'='*60}")

    md_root_dir = config["md_root_dir"]
    output_path = config["output_path"]
    md_root_prefix = config["md_root_prefix"]
    search_output_dir = config["search_output_dir"]
    index_output_path = config["index_output_path"]

    # 检查 Markdown 目录是否存在
    if not md_root_dir.exists():
        logging.error(f"错误：Markdown 目录不存在于 {md_root_dir}。请先运行对应的 generate_markdown 脚本。")
        return False

    # 扫描 Markdown 文件生成索引数据
    try:
        index_data = scan_markdown_files(md_root_dir, domain)
        logging.info(f"成功扫描 {len(index_data)} 个 Markdown 文件")
    except Exception as e:
        logging.error(f"扫描 Markdown 文件失败: {e}")
        return False

    # 保存 index.json
    try:
        index_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(index_output_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        logging.info(f"索引文件已保存: {index_output_path}")
    except Exception as e:
        logging.error(f"保存索引文件失败: {e}")
        return False

    # 生成目录树
    try:
        create_catalog_tree(index_data, output_path, md_root_prefix, domain)
    except Exception as e:
        logging.error(f"生成目录树失败: {e}")
        return False

    # 生成搜索索引
    try:
        generate_search_index(index_data, search_output_dir, md_root_prefix, domain)
    except Exception as e:
        logging.error(f"生成搜索索引失败: {e}")
        return False

    logging.info(f"{domain.upper()} 处理完成！")
    return True


def main():
    """主函数"""
    logging.info("开始统一生成所有游戏域的目录树和搜索索引...")

    # 支持命令行参数指定要处理的游戏域
    domains_to_process = []
    if len(sys.argv) > 1:
        # 从命令行参数获取
        for arg in sys.argv[1:]:
            if arg.lower() in GAME_CONFIGS:
                domains_to_process.append(arg.lower())
    else:
        # 默认处理所有游戏域
        domains_to_process = list(GAME_CONFIGS.keys())

    if not domains_to_process:
        logging.error("没有指定要处理的游戏域")
        logging.info(f"可用的游戏域: {', '.join(GAME_CONFIGS.keys())}")
        logging.info("用法: python generate_all_catalog_trees.py [gi|hsr|zzz] [gi|hsr|zzz] ...")
        sys.exit(1)

    logging.info(f"将处理以下游戏域: {', '.join([d.upper() for d in domains_to_process])}")

    # 处理每个游戏域
    success_count = 0
    for domain in domains_to_process:
        config = GAME_CONFIGS[domain]
        if process_domain(domain, config):
            success_count += 1

    # 总结
    logging.info(f"\n{'='*60}")
    logging.info(f"处理完成！成功: {success_count}/{len(domains_to_process)}")
    logging.info(f"{'='*60}")

    if success_count == len(domains_to_process):
        logging.info("所有任务成功完成！")
    else:
        logging.warning("部分游戏域处理失败，请检查日志")


if __name__ == "__main__":
    main()