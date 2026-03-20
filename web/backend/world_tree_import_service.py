"""世界树图谱导入服务：图谱导入、校验与结构化错误反馈。"""

from __future__ import annotations

import hashlib
from pydantic import BaseModel, Field, ValidationError
from typing import Any, Dict, List

from world_tree_graph_service import world_tree_graph_service


class GraphEntityPayload(BaseModel):
    name: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    aliases: list[str] = Field(default_factory=list)
    summary: str | None = None


class GraphEvidencePayload(BaseModel):
    file_path: str = Field(..., min_length=1)
    chunk_id: str = Field(..., min_length=1)
    quote: str | None = None


class GraphRelationPayload(BaseModel):
    subject: str = Field(..., min_length=1)
    predicate: str = Field(..., min_length=1)
    object: str = Field(..., min_length=1)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    reason: str | None = None
    evidence: GraphEvidencePayload


class GraphEventPayload(BaseModel):
    name: str = Field(..., min_length=1)
    type: str = Field(default="event", min_length=1)
    summary: str | None = None
    participants: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    evidence: GraphEvidencePayload


class WorldTreeGraphItemRequest(BaseModel):
    id: str | None = None
    domain: str = Field(default="gi")
    file_path: str = Field(..., min_length=1)
    chunk_id: str = Field(..., min_length=1)
    title: str | None = None
    judgment: str | None = None
    reasoning: str | None = None
    entities: list[GraphEntityPayload] = Field(default_factory=list)
    relations: list[GraphRelationPayload] = Field(default_factory=list)
    events: list[GraphEventPayload] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def format_pydantic_errors(exc: ValidationError) -> list[dict]:
    formatted: list[dict] = []
    for item in exc.errors():
        loc = item.get("loc") or ()
        field = ".".join(str(part) for part in loc) if loc else "unknown"
        err_type = str(item.get("type") or "validation_error")
        message = str(item.get("msg") or "字段校验失败")

        suggestion = "请根据字段要求修正后重试。"
        if "missing" in err_type:
            suggestion = f"请补充必填字段 {field}。"
        elif "string_type" in err_type:
            suggestion = f"请把 {field} 改为字符串。"
        elif "list_type" in err_type:
            suggestion = f"请把 {field} 改为数组。"
        elif "float" in err_type or "number" in err_type:
            suggestion = f"请把 {field} 改为数字。"
        elif "less_than_equal" in err_type or "greater_than_equal" in err_type:
            suggestion = f"请把 {field} 调整到允许范围内。"

        formatted.append({
            "field": field,
            "code": err_type.upper(),
            "message": message,
            "suggestion": suggestion,
        })
    return formatted


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _unique_preserve_order(values: List[str]) -> List[str]:
    seen = set()
    output: List[str] = []
    for value in values:
      normalized = _safe_text(value)
      if not normalized or normalized in seen:
          continue
      seen.add(normalized)
      output.append(normalized)
    return output


def _build_record_id(domain: str, file_path: str, chunk_id: str) -> str:
    seed = f"{domain}:{file_path}:{chunk_id}".encode("utf-8")
    return f"graph_{hashlib.sha1(seed).hexdigest()[:16]}"


def _build_judgment(item: dict) -> str:
    relations = item.get("relations") if isinstance(item.get("relations"), list) else []
    events = item.get("events") if isinstance(item.get("events"), list) else []
    entities = item.get("entities") if isinstance(item.get("entities"), list) else []

    if relations:
        first = relations[0] if isinstance(relations[0], dict) else {}
        subject = _safe_text(first.get("subject"))
        predicate = _safe_text(first.get("predicate"))
        obj = _safe_text(first.get("object"))
        if subject and predicate and obj:
            return f"{subject} {predicate} {obj}"

    if events:
        first = events[0] if isinstance(events[0], dict) else {}
        name = _safe_text(first.get("name"))
        summary = _safe_text(first.get("summary"))
        if name and summary:
            return f"{name}: {summary}"
        if name:
            return f"事件: {name}"

    names = []
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        name = _safe_text(entity.get("name"))
        if name:
            names.append(name)
    names = _unique_preserve_order(names)
    if names:
        return f"图谱片段: {' / '.join(names[:6])}"

    return "图谱片段记录"


def _build_keywords(item: dict) -> List[str]:
    keywords: List[str] = []

    for entity in item.get("entities") or []:
        if not isinstance(entity, dict):
            continue
        keywords.append(_safe_text(entity.get("name")))
        aliases = entity.get("aliases") if isinstance(entity.get("aliases"), list) else []
        keywords.extend([_safe_text(alias) for alias in aliases])

    for relation in item.get("relations") or []:
        if not isinstance(relation, dict):
            continue
        keywords.append(_safe_text(relation.get("subject")))
        keywords.append(_safe_text(relation.get("object")))
        keywords.append(_safe_text(relation.get("predicate")))

    for event in item.get("events") or []:
        if not isinstance(event, dict):
            continue
        keywords.append(_safe_text(event.get("name")))
        participants = event.get("participants") if isinstance(event.get("participants"), list) else []
        keywords.extend([_safe_text(participant) for participant in participants])

    return _unique_preserve_order(keywords)


def _dedupe_entities(entities: list[dict]) -> list[dict]:
    seen = set()
    output: list[dict] = []
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        key = (_safe_text(entity.get("name")), _safe_text(entity.get("type")))
        if not key[0] or key in seen:
            continue
        seen.add(key)
        output.append(entity)
    return output


def _dedupe_relations(relations: list[dict]) -> list[dict]:
    seen = set()
    output: list[dict] = []
    for relation in relations:
        if not isinstance(relation, dict):
            continue
        evidence = relation.get("evidence") if isinstance(relation.get("evidence"), dict) else {}
        key = (
            _safe_text(relation.get("subject")),
            _safe_text(relation.get("predicate")),
            _safe_text(relation.get("object")),
            _safe_text(evidence.get("file_path")),
            _safe_text(evidence.get("chunk_id")),
        )
        if not key[0] or not key[1] or not key[2] or key in seen:
            continue
        seen.add(key)
        output.append(relation)
    return output


def _dedupe_events(events: list[dict]) -> list[dict]:
    seen = set()
    output: list[dict] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        evidence = event.get("evidence") if isinstance(event.get("evidence"), dict) else {}
        key = (
            _safe_text(event.get("name")),
            _safe_text(evidence.get("file_path")),
            _safe_text(evidence.get("chunk_id")),
        )
        if not key[0] or key in seen:
            continue
        seen.add(key)
        output.append(event)
    return output


def _semantic_errors(item: dict) -> list[dict]:
    errors: list[dict] = []
    file_path = _safe_text(item.get("file_path"))
    chunk_id = _safe_text(item.get("chunk_id"))

    entities = item.get("entities") if isinstance(item.get("entities"), list) else []
    relations = item.get("relations") if isinstance(item.get("relations"), list) else []
    events = item.get("events") if isinstance(item.get("events"), list) else []

    if len(entities) == 0 and len(relations) == 0 and len(events) == 0:
        errors.append({
            "field": "item",
            "code": "EMPTY_GRAPH_ITEM",
            "message": "当前 item 没有任何 entities、relations 或 events。",
            "suggestion": "请至少导入一类结构化结果，或跳过该片段。",
        })

    for idx, relation in enumerate(relations):
        if not isinstance(relation, dict):
            continue
        evidence = relation.get("evidence") if isinstance(relation.get("evidence"), dict) else {}
        if _safe_text(evidence.get("file_path")) and _safe_text(evidence.get("file_path")) != file_path:
            errors.append({
                "field": f"relations.{idx}.evidence.file_path",
                "code": "EVIDENCE_FILE_MISMATCH",
                "message": "relation 的 evidence.file_path 与 item.file_path 不一致。",
                "suggestion": f"请把 relations.{idx}.evidence.file_path 改为当前 item 的 file_path：{file_path}。",
            })
        if _safe_text(evidence.get("chunk_id")) and _safe_text(evidence.get("chunk_id")) != chunk_id:
            errors.append({
                "field": f"relations.{idx}.evidence.chunk_id",
                "code": "EVIDENCE_CHUNK_MISMATCH",
                "message": "relation 的 evidence.chunk_id 与 item.chunk_id 不一致。",
                "suggestion": f"请把 relations.{idx}.evidence.chunk_id 改为当前 item 的 chunk_id：{chunk_id}。",
            })

    for idx, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        evidence = event.get("evidence") if isinstance(event.get("evidence"), dict) else {}
        if _safe_text(evidence.get("file_path")) and _safe_text(evidence.get("file_path")) != file_path:
            errors.append({
                "field": f"events.{idx}.evidence.file_path",
                "code": "EVIDENCE_FILE_MISMATCH",
                "message": "event 的 evidence.file_path 与 item.file_path 不一致。",
                "suggestion": f"请把 events.{idx}.evidence.file_path 改为当前 item 的 file_path：{file_path}。",
            })
        if _safe_text(evidence.get("chunk_id")) and _safe_text(evidence.get("chunk_id")) != chunk_id:
            errors.append({
                "field": f"events.{idx}.evidence.chunk_id",
                "code": "EVIDENCE_CHUNK_MISMATCH",
                "message": "event 的 evidence.chunk_id 与 item.chunk_id 不一致。",
                "suggestion": f"请把 events.{idx}.evidence.chunk_id 改为当前 item 的 chunk_id：{chunk_id}。",
            })

    return errors


def build_memory_record_from_graph_item(item: dict) -> dict:
    domain = _safe_text(item.get("domain")) or "gi"
    file_path = _safe_text(item.get("file_path"))
    chunk_id = _safe_text(item.get("chunk_id"))
    if not file_path or not chunk_id:
        raise ValueError("file_path 和 chunk_id 为必填字段")

    record_id = _safe_text(item.get("id")) or _build_record_id(domain, file_path, chunk_id)
    judgment = _safe_text(item.get("judgment")) or _build_judgment(item)
    normalized_entities = _dedupe_entities(item.get("entities") if isinstance(item.get("entities"), list) else [])
    normalized_relations = _dedupe_relations(item.get("relations") if isinstance(item.get("relations"), list) else [])
    normalized_events = _dedupe_events(item.get("events") if isinstance(item.get("events"), list) else [])

    item = {
        **item,
        "entities": normalized_entities,
        "relations": normalized_relations,
        "events": normalized_events,
    }

    keywords = _build_keywords(item)

    metadata = {
        "domain": domain,
        "title": _safe_text(item.get("title")),
        "file_path": file_path,
        "chunk_id": chunk_id,
        "entities": normalized_entities,
        "relations": normalized_relations,
        "events": normalized_events,
        "notes": item.get("notes") if isinstance(item.get("notes"), list) else [],
        "source": "graph_import",
    }

    return {
        "id": record_id,
        "judgment": judgment,
        "keywords": keywords,
        "memoryType": "world_tree_graph",
        "reasoning": _safe_text(item.get("reasoning")) or "来自图谱抽取导入",
        "metadata": metadata,
    }


def import_graph_items(items: List[dict], dry_run: bool = False) -> List[dict]:
    outputs: List[dict] = []
    for item in items:
        record = build_memory_record_from_graph_item(item)
        if dry_run:
            outputs.append(record)
            continue
        saved = world_tree_graph_service.upsert(record)
        outputs.append(saved)
    return outputs


def process_import_payload(payload: dict) -> dict:
    dry_run = bool(payload.get("dry_run", False))
    items_raw = payload.get("items")
    if not isinstance(items_raw, list) or len(items_raw) == 0:
        return {
            "ok": False,
            "dry_run": dry_run,
            "total": 0,
            "valid_count": 0,
            "invalid_count": 1,
            "imported_count": 0,
            "records": [],
            "errors": [
                {
                    "item_index": None,
                    "code": "EMPTY_ITEMS",
                    "message": "items 不能为空，且必须是数组。",
                    "suggestion": "请传入 items: [...]，至少包含一个对象。",
                }
            ],
        }

    records: list[dict] = []
    errors: list[dict] = []

    for index, raw_item in enumerate(items_raw):
        if not isinstance(raw_item, dict):
            errors.append({
                "item_index": index,
                "code": "INVALID_GRAPH_ITEM",
                "message": "每个 item 都必须是对象。",
                "suggestion": "请把 items 中的每一项都改成 JSON 对象。",
            })
            continue

        try:
            validated = WorldTreeGraphItemRequest.model_validate(raw_item)
        except ValidationError as exc:
            errors.append({
                "item_index": index,
                "code": "INVALID_GRAPH_ITEM",
                "message": "item 结构校验失败。",
                "details": format_pydantic_errors(exc),
            })
            continue

        semantic_errors = _semantic_errors(validated.model_dump())
        if semantic_errors:
            errors.append({
                "item_index": index,
                "code": "INVALID_GRAPH_SEMANTICS",
                "message": "item 语义校验失败。",
                "details": semantic_errors,
            })
            continue

        try:
            imported = import_graph_items([validated.model_dump()], dry_run=dry_run)
            if imported:
                records.append(imported[0])
        except ValueError as exc:
            errors.append({
                "item_index": index,
                "code": "INVALID_GRAPH_ITEM",
                "message": str(exc),
                "suggestion": "请检查 file_path、chunk_id、entities、relations、events 等字段是否完整。",
            })
        except Exception as exc:
            errors.append({
                "item_index": index,
                "code": "IMPORT_FAILED",
                "message": f"导入失败: {exc}",
                "suggestion": "请保留当前 item，稍后重试；若持续失败，请检查后端日志。",
            })

    total = len(items_raw)
    valid_count = len(records)
    invalid_count = len(errors)

    return {
        "ok": invalid_count == 0,
        "dry_run": dry_run,
        "total": total,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "imported_count": 0 if dry_run else valid_count,
        "records": records,
        "errors": errors,
    }
