import json
from pathlib import Path
import logging
import sys

# --- 配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

JSON_INPUT_PATH = project_root / "web/docs-site/public/domains/zzz/metadata/index.json"
JSON_OUTPUT_PATH = project_root / "web/docs-site/public/domains/zzz/metadata/catalog.json"
MD_ROOT_PREFIX = "/domains/zzz/docs"

def get_physical_path(item):
    """从索引条目动态构建物理路径"""
    frontend_path = item.get("path", "")
    domain_name = "zzz" # Hardcoded for ZZZ script

    # Example frontendPath: /domain/zzz/category/characters/三月七-1001
    parts = frontend_path.split('/')
    if len(parts) < 5: return None

    # parts[0] is empty, [1] is 'domain', [2] is 'zzz', [3] is 'category'
    relative_path = "/".join(parts[4:])
    return f"/domains/{domain_name}/docs/{relative_path}.md"

def create_catalog_tree():
    """
    从主索引文件 (index_zzz.json) 创建一个层级的、类似文件系统的目录树。
    """
    logging.info(f"正在从 {JSON_INPUT_PATH} 读取主索引...")
    if not JSON_INPUT_PATH.exists():
        logging.error(f"错误：主索引文件不存在于 {JSON_INPUT_PATH}。")
        sys.exit(1)

    with open(JSON_INPUT_PATH, 'r', encoding='utf-8') as f:
        index_data = json.load(f)

    logging.info(f"成功加载 {len(index_data)} 条索引条目，开始构建目录树...")

    catalog_tree = {}
    for item in index_data:
        physical_path = get_physical_path(item)
        if not physical_path:
            continue

        # Remove the root prefix and the leading slash
        path_parts = physical_path.replace(MD_ROOT_PREFIX, "", 1).strip("/").split("/")

        current_level = catalog_tree
        for i, part in enumerate(path_parts):
            if i == len(path_parts) - 1:
                # It's a file
                current_level[part] = None
            else:
                # It's a directory
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]

    logging.info(f"正在将生成的目录树写入 {JSON_OUTPUT_PATH}...")
    try:
        JSON_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(catalog_tree, f, ensure_ascii=False, indent=2)
        logging.info("目录树生成成功！")
    except Exception as e:
        logging.error(f"写入目录树时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_catalog_tree()