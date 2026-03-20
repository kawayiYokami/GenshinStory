"""后端配置模块"""
import os
from pathlib import Path

# 项目根目录 (web/backend -> web -> story)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 文档数据根目录
DOCS_ROOT = PROJECT_ROOT / "web" / "docs-site" / "public" / "domains"

# Tantivy 索引存储路径
INDEX_ROOT = Path(__file__).parent / "tantivy_index"

# 支持的游戏域
SUPPORTED_DOMAINS = ["gi", "hsr", "zzz"]
SUPPORTED_LINK_DOMAINS = ["gi", "hsr"]

# API 配置
CORS_ORIGINS = [
    "http://localhost:5713",
    "http://127.0.0.1:5713",
    "https://agent.zlb.ink",
]

# 通过环境变量扩展 CORS 白名单（逗号分隔）
_extra_cors = os.getenv("CORS_ORIGINS", "").strip()
if _extra_cors:
    CORS_ORIGINS.extend([item.strip() for item in _extra_cors.split(",") if item.strip()])


def get_docs_dir(domain: str) -> Path:
    """获取指定域的文档目录"""
    return DOCS_ROOT / domain / "docs"


def get_metadata_dir(domain: str) -> Path:
    """获取指定域的元数据目录"""
    return DOCS_ROOT / domain / "metadata"


def get_index_dir(domain: str) -> Path:
    """获取指定域的 Tantivy 索引目录"""
    return INDEX_ROOT / domain


def get_link_dir(domain: str) -> Path:
    """获取指定域的链接数据库目录"""
    if domain == "gi":
        return PROJECT_ROOT / "gi_wiki_scraper" / "output" / "link"
    if domain == "hsr":
        return PROJECT_ROOT / "hsr_wiki_scraper" / "output" / "link"
    raise ValueError(f"不支持的链接域: {domain}")
