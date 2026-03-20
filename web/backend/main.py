#!/usr/bin/env python3
"""FastAPI 后端入口：提供搜索和文档服务 API"""

import json
import logging
import asyncio
import os
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager, suppress
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from config import (
    CORS_ORIGINS,
    SUPPORTED_DOMAINS,
    SUPPORTED_LINK_DOMAINS,
    get_metadata_dir,
    get_index_dir,
    get_docs_dir,
)
from search_service import search_catalog, search_docs, invalidate_index
from doc_service import read_doc, read_raw_markdown
from indexer import build_index_for_domain
from model_metadata_service import model_metadata_cache
from world_tree_service import world_tree_memory_service
from world_tree_graph_service import world_tree_graph_service
from world_tree_query_service import world_tree_query_service
from world_tree_import_service import process_import_payload
from link_service import resolve_best_link

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "UTC")
APP_TZ = timezone.utc


def _ensure_indexes() -> None:
    """检查并自动构建缺失的 Tantivy 索引"""
    for domain in SUPPORTED_DOMAINS:
        index_dir = get_index_dir(domain)
        docs_dir = get_docs_dir(domain)

        if not docs_dir.exists():
            logger.info(f"[{domain.upper()}] 文档目录不存在，跳过索引构建")
            continue

        # 索引目录不存在或为空则构建
        needs_build = not index_dir.exists() or not any(index_dir.iterdir())
        if needs_build:
            logger.info(f"[{domain.upper()}] 索引不存在，开始自动构建...")
            build_index_for_domain(domain)
        else:
            logger.info(f"[{domain.upper()}] 索引已存在，跳过构建")


def _seconds_until_next_4am() -> float:
    now = datetime.now(APP_TZ)
    next_run = now.replace(hour=4, minute=0, second=0, microsecond=0)
    if now >= next_run:
        next_run = next_run + timedelta(days=1)
    return max(1.0, (next_run - now).total_seconds())


def _rebuild_all_domain_indexes() -> None:
    for domain in SUPPORTED_DOMAINS:
        try:
            logger.info(f"[SCHEDULED] 开始重建 {domain.upper()} 索引...")
            build_index_for_domain(domain)
            invalidate_index(domain)
            logger.info(f"[SCHEDULED] {domain.upper()} 索引重建完成。")
        except Exception as exc:
            logger.error(f"[SCHEDULED] {domain.upper()} 索引重建失败: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时自动构建索引
    _ensure_indexes()
    world_tree_memory_service.rebuild_index()
    world_tree_graph_service.rebuild_index()

    stop_event = asyncio.Event()

    async def world_tree_memory_rebuild_loop() -> None:
        while not stop_event.is_set():
            try:
                await asyncio.sleep(60 * 60)
                world_tree_memory_service.rebuild_index()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("世界树记忆索引定时重建失败: %s", exc)

    async def world_tree_graph_rebuild_loop() -> None:
        while not stop_event.is_set():
            try:
                await asyncio.sleep(60 * 60)
                world_tree_graph_service.rebuild_index()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("世界树图谱索引定时重建失败: %s", exc)

    async def docs_rebuild_loop() -> None:
        while not stop_event.is_set():
            try:
                wait_seconds = _seconds_until_next_4am()
                await asyncio.sleep(wait_seconds)
                _rebuild_all_domain_indexes()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("文档索引定时重建失败: %s", exc)

    world_tree_memory_task = asyncio.create_task(world_tree_memory_rebuild_loop())
    world_tree_graph_task = asyncio.create_task(world_tree_graph_rebuild_loop())
    docs_task = asyncio.create_task(docs_rebuild_loop())

    try:
        yield
    finally:
        stop_event.set()
        world_tree_memory_task.cancel()
        world_tree_graph_task.cancel()
        docs_task.cancel()
        with suppress(asyncio.CancelledError):
            await world_tree_memory_task
        with suppress(asyncio.CancelledError):
            await world_tree_graph_task
        with suppress(asyncio.CancelledError):
            await docs_task


app = FastAPI(title="Story Search API", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validate_domain(domain: str) -> None:
    if domain not in SUPPORTED_DOMAINS:
        raise HTTPException(status_code=404, detail=f"不支持的域: {domain}")


def _require_localhost(request: Request) -> None:
    client_host = request.client.host if request.client else None
    if client_host not in {"127.0.0.1", "::1"}:
        raise HTTPException(status_code=403, detail="调试命令仅允许本机访问")


class LocalDebugCommand(BaseModel):
    action: str = Field(..., description="search_catalog|search_docs|rebuild_index|invalidate_index|resolve_link")
    domain: str = Field(..., description="gi|hsr|zzz")
    query: Optional[str] = None
    path: Optional[str] = None
    maxResults: int = Field(default=50, ge=1, le=200)
    generateSummary: bool = False
    topK: int = Field(default=3, ge=1, le=20)
    minScore: float = Field(default=100.0, ge=0.0, le=1000.0)


@app.get("/api/{domain}/index")
async def get_index(domain: str):
    """获取目录索引"""
    _validate_domain(domain)

    index_path = get_metadata_dir(domain) / "index.json"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="索引文件不存在")

    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@app.get("/api/{domain}/search")
async def api_search(
    domain: str,
    query: str = Query(..., min_length=1),
    path: Optional[str] = Query(None),
    maxResults: int = Query(50, ge=1, le=200),
    generateSummary: bool = Query(True),
    mode: str = Query("catalog", pattern="^(catalog|docs)$"),
):
    """搜索文档

    mode=catalog: 快速目录搜索（用于 SearchView UI）
    mode=docs: 深度文档搜索（用于 Agent search_docs 工具）
    """
    _validate_domain(domain)

    if mode == "catalog":
        results = search_catalog(domain, query, max_results=maxResults)
        return {"results": results, "total": len(results), "query": query}
    else:
        result = search_docs(
            domain,
            query,
            doc_path=path,
            max_results=maxResults,
            generate_summary=generateSummary,
        )
        return result


@app.get("/api/{domain}/doc")
async def api_read_doc(
    domain: str,
    path: str = Query(...),
    line_range: list[str] = Query(default=[]),
    preserve_markdown: bool = Query(False),
):
    """读取文档内容"""
    _validate_domain(domain)

    line_ranges = line_range
    result = read_doc(domain, path, line_ranges=line_ranges, preserve_markdown=preserve_markdown)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@app.get("/api/{domain}/doc/raw")
async def api_read_raw_doc(
    domain: str,
    path: str = Query(...),
):
    """读取原始 Markdown 内容"""
    _validate_domain(domain)

    try:
        content = read_raw_markdown(domain, path)
        return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/debug/local-command")
async def local_debug_command(request: Request, cmd: LocalDebugCommand):
    """仅本机可调用的后端调试命令。"""
    _require_localhost(request)
    _validate_domain(cmd.domain)

    action = (cmd.action or "").strip().lower()

    if action == "search_catalog":
        if not cmd.query:
            raise HTTPException(status_code=400, detail="search_catalog 需要 query")
        results = search_catalog(
            cmd.domain,
            cmd.query,
            max_results=cmd.maxResults,
        )
        return {"ok": True, "action": action, "total": len(results), "results": results}

    if action == "search_docs":
        if not cmd.query:
            raise HTTPException(status_code=400, detail="search_docs 需要 query")
        result = search_docs(
            cmd.domain,
            cmd.query,
            doc_path=cmd.path,
            max_results=cmd.maxResults,
            generate_summary=cmd.generateSummary,
        )
        return {"ok": True, "action": action, "result": result}

    if action == "rebuild_index":
        build_index_for_domain(cmd.domain)
        invalidate_index(cmd.domain)
        return {"ok": True, "action": action, "message": f"{cmd.domain} 索引已重建并刷新缓存"}

    if action == "invalidate_index":
        invalidate_index(cmd.domain)
        return {"ok": True, "action": action, "message": f"{cmd.domain} 缓存已失效"}

    if action == "resolve_link":
        if not cmd.query:
            raise HTTPException(status_code=400, detail="resolve_link 需要 query（文件标题）")
        if cmd.domain not in SUPPORTED_LINK_DOMAINS:
            raise HTTPException(status_code=400, detail=f"resolve_link 仅支持 {', '.join(SUPPORTED_LINK_DOMAINS)}")
        result = resolve_best_link(
            cmd.domain,
            cmd.query,
            top_k=cmd.topK,
            min_score=cmd.minScore,
        )
        return {"ok": True, "action": action, "result": result}

    raise HTTPException(status_code=400, detail=f"不支持的调试 action: {cmd.action}")


@app.get("/api/{domain}/resolve-link")
async def api_resolve_link(
    domain: str,
    title: str = Query(..., min_length=1, description="可包含路径和后缀的文件名"),
    k: int = Query(3, ge=1, le=20, description="返回的高分候选数量"),
    minScore: float = Query(100.0, ge=0.0, le=1000.0, description="最小分数阈值"),
):
    if domain not in SUPPORTED_LINK_DOMAINS:
        raise HTTPException(status_code=404, detail=f"链接解析仅支持 {', '.join(SUPPORTED_LINK_DOMAINS)}")
    return resolve_best_link(domain, title, top_k=k, min_score=minScore)


class ModelMetadataRequest(BaseModel):
    model_name: str = Field(..., description="模型名称")


class WorldTreeMemoryRecord(BaseModel):
    id: str
    judgment: str
    keywords: list[str] = Field(default_factory=list)
    memoryType: str = "world_tree"
    reasoning: str = ""
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class WorldTreeQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    intent: Optional[str] = Field(default="analysis")
    entities: list[str] = Field(default_factory=list)
    domain: Optional[str] = Field(default="gi")
    max_entities: int = Field(default=8, ge=1, le=50)
    max_relations: int = Field(default=12, ge=1, le=100)
    max_events: int = Field(default=6, ge=0, le=50)
    max_files: int = Field(default=8, ge=1, le=30)
    max_chunks_per_file: int = Field(default=3, ge=1, le=10)
    include_quotes: bool = Field(default=True)


class WorldTreeExpandRequest(BaseModel):
    entity_id: str = Field(..., min_length=1)
    relation_types: list[str] = Field(default_factory=list)
    depth: int = Field(default=1, ge=1, le=3)
    max_nodes: int = Field(default=20, ge=1, le=200)
    max_edges: int = Field(default=30, ge=1, le=300)
    include_related_files: bool = Field(default=True)
    domain: Optional[str] = Field(default="gi")


class WorldTreePathsRequest(BaseModel):
    from_entity_id: str = Field(..., min_length=1)
    to_entity_id: str = Field(..., min_length=1)
    max_depth: int = Field(default=3, ge=1, le=5)
    max_paths: int = Field(default=5, ge=1, le=20)
    domain: Optional[str] = Field(default="gi")


@app.post("/api/models/metadata")
async def get_model_metadata(request: ModelMetadataRequest):
    """获取模型元数据（上下文窗口等）- 从 models.dev 远程数据库获取"""
    metadata = await model_metadata_cache.get_model_metadata(request.model_name)

    if not metadata:
        return {
            "found": False,
            "model_name": request.model_name
        }

    return {
        "found": True,
        "model_name": metadata.name,
        "context_window": metadata.context_window,
        "max_output_tokens": metadata.max_output_tokens,
        "provider": metadata.provider,
        "enable_image": metadata.enable_image,
        "enable_audio": metadata.enable_audio,
        "enable_tools": metadata.enable_tools,
        "last_updated": metadata.last_updated
    }


@app.get("/api/world-tree/recall")
async def world_tree_recall(
    query: str = Query(..., min_length=1),
    topK: int = Query(5, ge=1, le=50),
):
    records = world_tree_memory_service.recall(query, topK)
    return {
        "query": query,
        "total": len(records),
        "records": records,
    }


@app.post("/api/world-tree/memory")
async def world_tree_upsert(record: WorldTreeMemoryRecord):
    payload = record.model_dump()
    payload["memoryType"] = "world_tree"
    saved = world_tree_memory_service.upsert(payload)
    return {"ok": True, "record": saved}


@app.delete("/api/world-tree/memory/{record_id}")
async def world_tree_delete(record_id: str):
    removed = world_tree_memory_service.remove(record_id)
    return {"ok": True, "removed": removed, "id": record_id}


@app.get("/api/world-tree/tags")
async def world_tree_tags():
    tags = world_tree_memory_service.list_tags()
    return {
        "total": len(tags),
        "tags": tags,
    }


@app.post("/api/world-tree/query")
async def world_tree_query(request: WorldTreeQueryRequest):
    payload = request.model_dump()
    return world_tree_query_service.query(payload)


@app.post("/api/world-tree/expand")
async def world_tree_expand(request: WorldTreeExpandRequest):
    payload = request.model_dump()
    return world_tree_query_service.expand(payload)


@app.post("/api/world-tree/paths")
async def world_tree_paths(request: WorldTreePathsRequest):
    payload = request.model_dump()
    return world_tree_query_service.paths(payload)


@app.get("/api/world-tree/entity/{entity_id}")
async def world_tree_entity(entity_id: str):
    entity = world_tree_query_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@app.post("/api/world-tree/import-graph")
async def world_tree_import_graph(request: Request, payload: dict):
    _require_localhost(request)
    return process_import_payload(payload)


@app.get("/api/world-tree/graph/stats")
async def world_tree_graph_stats(request: Request):
    _require_localhost(request)
    return world_tree_graph_service.stats()


@app.get("/api/world-tree/graph/recent")
async def world_tree_graph_recent(
    request: Request,
    limit: int = Query(20, ge=1, le=200),
):
    _require_localhost(request)
    rows = world_tree_graph_service.recent(limit=limit)
    return {
        "total": len(rows),
        "records": rows,
    }
