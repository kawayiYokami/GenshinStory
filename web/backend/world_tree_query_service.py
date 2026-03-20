"""世界树图谱查询服务：基于独立图谱库记录构建轻量图谱视图。"""

from __future__ import annotations

import re
from collections import defaultdict, deque
from itertools import combinations
from typing import Any, Dict, List, Optional, Set, Tuple

from world_tree_graph_service import world_tree_graph_service


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_name(value: Any) -> str:
    text = _safe_text(value).lower()
    text = re.sub(r"\s+", "", text)
    return text


def _entity_id_from_name(name: str) -> str:
    normalized = _normalize_name(name)
    if not normalized:
        return ""
    return f"ent_{normalized}"


def _extract_source_ref(record: dict) -> dict:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    file_path = (
        _safe_text(metadata.get("file_path"))
        or _safe_text(metadata.get("filePath"))
        or _safe_text(metadata.get("path"))
        or _safe_text(metadata.get("source_file"))
    )
    chunk_id = (
        _safe_text(metadata.get("chunk_id"))
        or _safe_text(metadata.get("chunkId"))
        or _safe_text(metadata.get("line_range"))
        or _safe_text(record.get("id"))
    )
    quote = _safe_text(metadata.get("quote")) or _safe_text(record.get("judgment"))
    return {
        "file_path": file_path or "",
        "chunk_id": chunk_id or str(record.get("id") or ""),
        "score": 0.8,
        "quote": quote[:280],
    }


class WorldTreeQueryService:
    """把 world_tree_graph 记录转换为可查询的实体-关系图。"""

    def _build_graph(self) -> Tuple[Dict[str, dict], List[dict], Dict[str, List[dict]]]:
        records = world_tree_graph_service.list_records()

        entities: Dict[str, dict] = {}
        relations: List[dict] = []
        adjacency: Dict[str, List[dict]] = defaultdict(list)

        def ensure_entity(name: str, entity_type: str = "concept", aliases: Optional[List[str]] = None) -> Optional[dict]:
            display_name = _safe_text(name)
            if not display_name:
                return None
            entity_id = _entity_id_from_name(display_name)
            if not entity_id:
                return None
            existing = entities.get(entity_id)
            if existing:
                if aliases:
                    merged = set(existing.get("aliases") or [])
                    merged.update([_safe_text(a) for a in aliases if _safe_text(a)])
                    existing["aliases"] = sorted(list(merged))
                return existing

            entities[entity_id] = {
                "id": entity_id,
                "name": display_name,
                "type": entity_type or "concept",
                "aliases": sorted(list(set([display_name] + [_safe_text(a) for a in (aliases or []) if _safe_text(a)]))),
            }
            return entities[entity_id]

        for record in records:
            metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
            source_ref = _extract_source_ref(record)
            keywords = [k for k in (record.get("keywords") or []) if _safe_text(k)]

            metadata_entities = metadata.get("entities") if isinstance(metadata.get("entities"), list) else []
            if metadata_entities:
                for item in metadata_entities:
                    if not isinstance(item, dict):
                        continue
                    ensure_entity(
                        _safe_text(item.get("name")),
                        _safe_text(item.get("type")) or "concept",
                        item.get("aliases") if isinstance(item.get("aliases"), list) else None,
                    )
            else:
                for keyword in keywords:
                    ensure_entity(keyword, "concept", None)

            metadata_relations = metadata.get("relations") if isinstance(metadata.get("relations"), list) else []
            if metadata_relations:
                for rel in metadata_relations:
                    if not isinstance(rel, dict):
                        continue
                    subject_name = _safe_text(rel.get("subject")) or _safe_text(rel.get("from"))
                    object_name = _safe_text(rel.get("object")) or _safe_text(rel.get("to"))
                    predicate = _safe_text(rel.get("predicate")) or "related_to"
                    if not subject_name or not object_name:
                        continue
                    subject = ensure_entity(subject_name, "concept")
                    obj = ensure_entity(object_name, "concept")
                    if not subject or not obj:
                        continue

                    relation_id = f"rel_{record.get('id')}_{len(relations)}"
                    score = float(rel.get("score") or rel.get("confidence") or 0.8)
                    item = {
                        "id": relation_id,
                        "subject_id": subject["id"],
                        "predicate": predicate,
                        "object_id": obj["id"],
                        "score": max(0.1, min(1.0, score)),
                        "evidence_count": 1,
                        "reason": _safe_text(rel.get("reason")) or "来自世界树图谱关系抽取",
                        "source_refs": [source_ref],
                    }
                    relations.append(item)
                    adjacency[subject["id"]].append(item)
                    adjacency[obj["id"]].append(item)
            else:
                # 兜底：关键词共现关系
                unique_keywords = sorted(list(set([_safe_text(k) for k in keywords if _safe_text(k)])))
                for left, right in combinations(unique_keywords, 2):
                    left_entity = ensure_entity(left, "concept")
                    right_entity = ensure_entity(right, "concept")
                    if not left_entity or not right_entity:
                        continue
                    relation_id = f"rel_{record.get('id')}_{left_entity['id']}_{right_entity['id']}"
                    item = {
                        "id": relation_id,
                        "subject_id": left_entity["id"],
                        "predicate": "co_appears_with",
                        "object_id": right_entity["id"],
                        "score": 0.65,
                        "evidence_count": 1,
                        "reason": "来自同一条世界树图谱关键词共现",
                        "source_refs": [source_ref],
                    }
                    relations.append(item)
                    adjacency[left_entity["id"]].append(item)
                    adjacency[right_entity["id"]].append(item)

        return entities, relations, adjacency

    def _match_entities(self, entities: Dict[str, dict], query: str, requested_entities: Optional[List[str]]) -> List[dict]:
        candidates = [_safe_text(x) for x in (requested_entities or []) if _safe_text(x)]
        query_norm = _normalize_name(query)
        if not candidates and query_norm:
            # 粗粒度提取：按中文/英文连续块切词
            rough_tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9_]{2,}", query)
            candidates = [_safe_text(t) for t in rough_tokens if _safe_text(t)]

        matched: List[dict] = []
        seen: Set[str] = set()

        for entity in entities.values():
            names = [_normalize_name(entity.get("name"))]
            names.extend([_normalize_name(a) for a in (entity.get("aliases") or [])])
            names = [n for n in names if n]
            if not names:
                continue

            best_score = 0.0
            for candidate in candidates:
                c = _normalize_name(candidate)
                if not c:
                    continue
                for name in names:
                    if c == name:
                        best_score = max(best_score, 0.99)
                    elif c in name or name in c:
                        best_score = max(best_score, 0.78)

            if not candidates and query_norm:
                for name in names:
                    if name and (name in query_norm or query_norm in name):
                        best_score = max(best_score, 0.75)

            if best_score <= 0:
                continue
            if entity["id"] in seen:
                continue
            seen.add(entity["id"])
            matched.append({
                **entity,
                "score": round(best_score, 4),
            })

        matched.sort(key=lambda x: (-float(x.get("score", 0)), x.get("name", "")))
        return matched

    def _collect_related_files(self, source_refs: List[dict], max_files: int, max_chunks_per_file: int) -> List[dict]:
        by_file: Dict[str, dict] = {}
        for ref in source_refs:
            file_path = _safe_text(ref.get("file_path"))
            if not file_path:
                continue
            bucket = by_file.setdefault(
                file_path,
                {
                    "file_path": file_path,
                    "score": 0.0,
                    "reasons": set(),
                    "chunks": [],
                },
            )
            bucket["score"] = max(bucket["score"], float(ref.get("score") or 0.6))
            chunk_id = _safe_text(ref.get("chunk_id"))
            if chunk_id:
                bucket["chunks"].append(
                    {
                        "chunk_id": chunk_id,
                        "score": float(ref.get("score") or 0.6),
                        "reason": "来自世界树证据片段",
                    }
                )
            quote = _safe_text(ref.get("quote"))
            if quote:
                bucket["reasons"].add("命中世界树证据记录")

        rows = []
        for item in by_file.values():
            chunks = sorted(item["chunks"], key=lambda x: -float(x.get("score", 0)))[: max(1, int(max_chunks_per_file))]
            rows.append(
                {
                    "file_path": item["file_path"],
                    "score": round(float(item["score"]), 4),
                    "reasons": list(item["reasons"]) or ["世界树关联文件"],
                    "chunks": chunks,
                }
            )
        rows.sort(key=lambda x: -float(x.get("score", 0)))
        return rows[: max(1, int(max_files))]

    def query(self, payload: dict) -> dict:
        entities, relations, adjacency = self._build_graph()
        query = _safe_text(payload.get("query"))
        intent = _safe_text(payload.get("intent")) or "analysis"
        requested_entities = payload.get("entities") if isinstance(payload.get("entities"), list) else []

        max_entities = max(1, int(payload.get("max_entities") or 8))
        max_relations = max(1, int(payload.get("max_relations") or 12))
        max_events = max(0, int(payload.get("max_events") or 6))
        max_files = max(1, int(payload.get("max_files") or 8))
        max_chunks_per_file = max(1, int(payload.get("max_chunks_per_file") or 3))
        include_quotes = bool(payload.get("include_quotes", True))

        resolved_entities = self._match_entities(entities, query, requested_entities)[:max_entities]
        resolved_ids = {item["id"] for item in resolved_entities}

        candidate_relations: List[dict] = []
        source_refs: List[dict] = []
        seen_rel_ids: Set[str] = set()

        for entity_id in resolved_ids:
            for rel in adjacency.get(entity_id, []):
                rel_id = str(rel.get("id"))
                if rel_id in seen_rel_ids:
                    continue
                seen_rel_ids.add(rel_id)
                candidate_relations.append(rel)
                source_refs.extend(rel.get("source_refs") or [])

        candidate_relations.sort(key=lambda r: -float(r.get("score") or 0))
        candidate_relations = candidate_relations[:max_relations]

        if not include_quotes:
            for rel in candidate_relations:
                refs = rel.get("source_refs") or []
                rel["source_refs"] = [{k: v for k, v in ref.items() if k != "quote"} for ref in refs]

        # 事件字段：先读 metadata 事件，不足时降级为空
        events: List[dict] = []
        if max_events > 0:
            seen_event_ids: Set[str] = set()
            for record in world_tree_graph_service.list_records():
                metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
                meta_events = metadata.get("events") if isinstance(metadata.get("events"), list) else []
                for evt in meta_events:
                    if not isinstance(evt, dict):
                        continue
                    name = _safe_text(evt.get("name"))
                    if not name:
                        continue
                    event_id = _entity_id_from_name(name)
                    if not event_id or event_id in seen_event_ids:
                        continue
                    seen_event_ids.add(event_id)
                    events.append(
                        {
                            "id": event_id,
                            "name": name,
                            "type": _safe_text(evt.get("type")) or "event",
                            "score": float(evt.get("score") or 0.7),
                            "reason": _safe_text(evt.get("reason")) or "来自世界树事件元数据",
                        }
                    )
            events.sort(key=lambda x: -float(x.get("score", 0)))
            events = events[:max_events]

        related_files = self._collect_related_files(source_refs, max_files=max_files, max_chunks_per_file=max_chunks_per_file)
        hints = [
            "优先阅读 related_files 中高分 chunk，再做结论。",
            "涉及事实判断时，使用 read_doc 二次验证。",
        ]
        if intent in {"relationship", "timeline"}:
            hints.append("若关系链路不清晰，继续调用 world_tree_paths。")

        return {
            "query_id": f"wt_q_{abs(hash(query))}",
            "resolved_entities": resolved_entities,
            "relations": candidate_relations,
            "events": events,
            "related_files": related_files,
            "reasoning_hints": hints,
        }

    def expand(self, payload: dict) -> dict:
        entities, relations, adjacency = self._build_graph()
        entity_id = _safe_text(payload.get("entity_id"))
        relation_types = payload.get("relation_types") if isinstance(payload.get("relation_types"), list) else None
        depth = max(1, min(3, int(payload.get("depth") or 1)))
        max_nodes = max(1, int(payload.get("max_nodes") or 20))
        max_edges = max(1, int(payload.get("max_edges") or 30))
        include_related_files = bool(payload.get("include_related_files", True))

        center = entities.get(entity_id)
        if not center:
            return {
                "center_entity": {"id": entity_id, "name": "", "type": "unknown"},
                "nodes": [],
                "edges": [],
                "related_files": [],
            }

        visited_nodes: Set[str] = {entity_id}
        q = deque([(entity_id, 0)])
        edges: List[dict] = []
        seen_edges: Set[str] = set()
        source_refs: List[dict] = []

        while q:
            current, level = q.popleft()
            if level >= depth:
                continue
            for rel in adjacency.get(current, []):
                predicate = _safe_text(rel.get("predicate"))
                if relation_types and predicate not in set([_safe_text(t) for t in relation_types]):
                    continue
                rel_id = _safe_text(rel.get("id"))
                if rel_id in seen_edges:
                    continue
                seen_edges.add(rel_id)
                edges.append(rel)
                source_refs.extend(rel.get("source_refs") or [])

                next_id = rel.get("object_id") if rel.get("subject_id") == current else rel.get("subject_id")
                next_id = _safe_text(next_id)
                if next_id and next_id not in visited_nodes and len(visited_nodes) < max_nodes:
                    visited_nodes.add(next_id)
                    q.append((next_id, level + 1))
            if len(edges) >= max_edges:
                break

        node_rows = [entities[nid] for nid in visited_nodes if nid in entities][:max_nodes]
        edge_rows = sorted(edges, key=lambda x: -float(x.get("score") or 0))[:max_edges]
        related_files = self._collect_related_files(source_refs, max_files=8, max_chunks_per_file=3) if include_related_files else []

        return {
            "center_entity": center,
            "nodes": node_rows,
            "edges": edge_rows,
            "related_files": related_files,
        }

    def paths(self, payload: dict) -> dict:
        entities, _, adjacency = self._build_graph()
        from_entity_id = _safe_text(payload.get("from_entity_id"))
        to_entity_id = _safe_text(payload.get("to_entity_id"))
        max_depth = max(1, min(5, int(payload.get("max_depth") or 3)))
        max_paths = max(1, min(10, int(payload.get("max_paths") or 5)))

        if from_entity_id not in entities or to_entity_id not in entities:
            return {"paths": []}

        q = deque([(from_entity_id, [], {from_entity_id})])
        found_paths: List[dict] = []

        while q and len(found_paths) < max_paths:
            node_id, steps, visited = q.popleft()
            if len(steps) > max_depth:
                continue
            if node_id == to_entity_id and steps:
                source_refs = []
                for step in steps:
                    source_refs.extend(step.get("source_refs") or [])
                found_paths.append(
                    {
                        "score": round(sum(float(s.get("score") or 0.5) for s in steps) / len(steps), 4),
                        "steps": [
                            {
                                "from": s.get("subject_id"),
                                "predicate": s.get("predicate"),
                                "to": s.get("object_id"),
                            }
                            for s in steps
                        ],
                        "source_refs": source_refs[:5],
                    }
                )
                continue

            if len(steps) >= max_depth:
                continue

            for rel in adjacency.get(node_id, []):
                left = _safe_text(rel.get("subject_id"))
                right = _safe_text(rel.get("object_id"))
                next_id = right if left == node_id else left
                if not next_id or next_id in visited:
                    continue
                q.append((next_id, steps + [rel], set(list(visited) + [next_id])))

        found_paths.sort(key=lambda x: -float(x.get("score", 0)))
        return {"paths": found_paths[:max_paths]}

    def get_entity(self, entity_id: str) -> Optional[dict]:
        entities, _, _ = self._build_graph()
        return entities.get(_safe_text(entity_id))


world_tree_query_service = WorldTreeQueryService()
