"""世界树图谱服务：独立 SQLite 图谱库 + 标签索引。"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

WORLD_TREE_GRAPH_DB = Path(__file__).parent / "world_tree_graph.db"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_text(value: object) -> str:
    return str(value or "").strip()


def _normalize_keyword(value: object) -> str:
    text = _safe_text(value)
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def _atomicize_keywords(raw_keywords: object) -> List[str]:
    if not isinstance(raw_keywords, list):
        return []

    result: List[str] = []
    seen: Set[str] = set()
    for item in raw_keywords:
        text = _safe_text(item)
        if not text:
            continue
        first = [part.strip() for part in re.split(r"[，,|、;\n\t]+", text) if part.strip()]
        for part in first:
            second = [token.strip() for token in re.split(r"\s+", part) if token.strip()]
            for token in second:
                if re.search(r"[\u4e00-\u9fff]", token) and "的" in token:
                    pieces = [x.strip() for x in token.split("的") if x.strip()]
                    if len(pieces) > 1:
                        for p in pieces:
                            normalized_piece = _normalize_keyword(p)
                            if normalized_piece and normalized_piece not in seen:
                                seen.add(normalized_piece)
                                result.append(normalized_piece)
                        continue
                normalized_token = _normalize_keyword(token)
                if normalized_token and normalized_token not in seen:
                    seen.add(normalized_token)
                    result.append(normalized_token)
    return result


def _fallback_split(text: str) -> List[str]:
    return [token for token in re.split(r"[^\w\u4e00-\u9fff]+", text.lower()) if token]


def _cjk_bigrams(token: str) -> List[str]:
    if len(token) <= 1:
        return [token]
    return [token[i:i + 2] for i in range(len(token) - 1)]


class WorldTreeGraphService:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._inverted_index: Dict[str, Set[str]] = {}
        self._index_dirty = False
        self._ensure_db()
        self.rebuild_index()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(WORLD_TREE_GRAPH_DB))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _ensure_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS world_tree_graph (
                    id TEXT PRIMARY KEY,
                    judgment TEXT NOT NULL,
                    graph_type TEXT NOT NULL DEFAULT 'graph',
                    reasoning TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS world_tree_graph_tag (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS world_tree_graph_tag_map (
                    graph_id TEXT NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (graph_id, tag_id),
                    FOREIGN KEY (graph_id) REFERENCES world_tree_graph(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES world_tree_graph_tag(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_world_tree_graph_updated_at ON world_tree_graph(updated_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_world_tree_graph_tag_map_graph_id ON world_tree_graph_tag_map(graph_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_world_tree_graph_tag_map_tag_id ON world_tree_graph_tag_map(tag_id)")
            conn.commit()

    def _tokenize(self, text: str) -> List[str]:
        normalized = _safe_text(text)
        if not normalized:
            return []
        base_tokens = _fallback_split(normalized)
        if not base_tokens:
            return []

        out: List[str] = []
        seen: Set[str] = set()
        for token in base_tokens:
            if token not in seen:
                seen.add(token)
                out.append(token)
            if re.search(r"[\u4e00-\u9fff]", token):
                for bg in _cjk_bigrams(token):
                    if bg and bg not in seen:
                        seen.add(bg)
                        out.append(bg)
        return out

    def _normalize_record(self, record: dict) -> dict:
        now = _utc_now_iso()
        record_id = _safe_text(record.get("id"))
        judgment = _safe_text(record.get("judgment") or record.get("content"))
        if not record_id or not judgment:
            raise ValueError("世界树图谱缺少 id 或 judgment")

        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        return {
            "id": record_id,
            "judgment": judgment,
            "keywords": _atomicize_keywords(record.get("keywords")),
            "graphType": "graph",
            "reasoning": _safe_text(record.get("reasoning") or record.get("reason")),
            "createdAt": _safe_text(record.get("createdAt")) or now,
            "updatedAt": _safe_text(record.get("updatedAt")) or now,
            "metadata": metadata,
        }

    def _cleanup_orphan_tags(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            DELETE FROM world_tree_graph_tag
            WHERE id NOT IN (SELECT DISTINCT tag_id FROM world_tree_graph_tag_map)
            """
        )

    def _upsert_tags(self, conn: sqlite3.Connection, graph_id: str, keywords: List[str]) -> None:
        conn.execute("DELETE FROM world_tree_graph_tag_map WHERE graph_id = ?", (graph_id,))
        for keyword in keywords:
            name = _normalize_keyword(keyword)
            if not name:
                continue
            conn.execute("INSERT OR IGNORE INTO world_tree_graph_tag(name) VALUES (?)", (name,))
            tag_row = conn.execute("SELECT id FROM world_tree_graph_tag WHERE name = ?", (name,)).fetchone()
            if not tag_row:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO world_tree_graph_tag_map(graph_id, tag_id) VALUES (?, ?)",
                (graph_id, int(tag_row["id"])),
            )
        self._cleanup_orphan_tags(conn)

    def _get_keywords_map(self, conn: sqlite3.Connection) -> Dict[str, List[str]]:
        rows = conn.execute(
            """
            SELECT m.graph_id AS graph_id, t.name AS tag_name
            FROM world_tree_graph_tag_map m
            JOIN world_tree_graph_tag t ON t.id = m.tag_id
            ORDER BY m.graph_id ASC, t.name ASC
            """
        ).fetchall()
        mapping: Dict[str, List[str]] = {}
        for row in rows:
            graph_id = str(row["graph_id"])
            tag_name = str(row["tag_name"])
            mapping.setdefault(graph_id, []).append(tag_name)
        return mapping

    def _update_index_for_record(self, record: dict) -> None:
        record_id = str(record.get("id", ""))
        if not record_id:
            return
        for token, id_set in list(self._inverted_index.items()):
            id_set.discard(record_id)
            if not id_set:
                del self._inverted_index[token]

        raw_text = f"{record.get('judgment', '').strip()} {' '.join(record.get('keywords', []))}".strip()
        tokens = self._tokenize(raw_text)
        for token in tokens:
            self._inverted_index.setdefault(token, set()).add(record_id)

    def upsert(self, record: dict) -> dict:
        normalized = self._normalize_record(record)
        with self._lock:
            with self._get_conn() as conn:
                existing = conn.execute(
                    "SELECT created_at FROM world_tree_graph WHERE id = ?",
                    (normalized["id"],),
                ).fetchone()
                created_at = str(existing["created_at"]) if existing else normalized["createdAt"]
                updated_at = _utc_now_iso()
                conn.execute(
                    """
                    INSERT INTO world_tree_graph(id, judgment, graph_type, reasoning, created_at, updated_at, metadata_json)
                    VALUES (?, ?, 'graph', ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        judgment=excluded.judgment,
                        graph_type='graph',
                        reasoning=excluded.reasoning,
                        updated_at=excluded.updated_at,
                        metadata_json=excluded.metadata_json
                    """,
                    (
                        normalized["id"],
                        normalized["judgment"],
                        normalized["reasoning"],
                        created_at,
                        updated_at,
                        json.dumps(normalized["metadata"], ensure_ascii=False),
                    ),
                )
                self._upsert_tags(conn, normalized["id"], normalized["keywords"])
                conn.commit()

            self._update_index_for_record(normalized)
            self._index_dirty = True
            normalized["createdAt"] = created_at
            normalized["updatedAt"] = updated_at
            return normalized

    def remove(self, record_id: str) -> bool:
        key = _safe_text(record_id)
        if not key:
            return False
        with self._lock:
            with self._get_conn() as conn:
                exists = conn.execute("SELECT 1 FROM world_tree_graph WHERE id = ?", (key,)).fetchone()
                if not exists:
                    return False
                conn.execute("DELETE FROM world_tree_graph_tag_map WHERE graph_id = ?", (key,))
                conn.execute("DELETE FROM world_tree_graph WHERE id = ?", (key,))
                conn.commit()
            for token, id_set in list(self._inverted_index.items()):
                id_set.discard(key)
                if not id_set:
                    del self._inverted_index[token]
            self._index_dirty = True
            return True

    def list_records(self) -> List[dict]:
        with self._lock:
            with self._get_conn() as conn:
                rows = conn.execute(
                    """
                    SELECT id, judgment, graph_type, reasoning, created_at, updated_at, metadata_json
                    FROM world_tree_graph
                    ORDER BY updated_at DESC
                    """
                ).fetchall()
                keywords_map = self._get_keywords_map(conn)

        out: List[dict] = []
        for row in rows:
            metadata_raw = str(row["metadata_json"] or "{}")
            try:
                metadata = json.loads(metadata_raw)
                if not isinstance(metadata, dict):
                    metadata = {}
            except Exception:
                metadata = {}

            graph_id = str(row["id"])
            out.append(
                {
                    "id": graph_id,
                    "judgment": str(row["judgment"]),
                    "keywords": keywords_map.get(graph_id, []),
                    "memoryType": "world_tree_graph",
                    "reasoning": str(row["reasoning"] or ""),
                    "createdAt": str(row["created_at"]),
                    "updatedAt": str(row["updated_at"]),
                    "metadata": metadata,
                }
            )
        return out

    def rebuild_index(self) -> None:
        with self._lock:
            records = self.list_records()
            next_index: Dict[str, Set[str]] = {}
            for record in records:
                raw_text = f"{record.get('judgment', '').strip()} {' '.join(record.get('keywords', []))}".strip()
                tokens = self._tokenize(raw_text)
                for token in tokens:
                    next_index.setdefault(token, set()).add(str(record["id"]))
            self._inverted_index = next_index
            logger.info(
                "[WORLD_TREE_GRAPH] 索引重建完成: %s 条记录, %s 个 token",
                len(records),
                len(self._inverted_index),
            )

    def recall(self, query: str, top_k: int = 5) -> List[dict]:
        q = _safe_text(query)
        if not q:
            return []
        q_tokens = self._tokenize(q)
        if not q_tokens:
            return []

        with self._lock:
            records = self.list_records()
            by_id = {str(record["id"]): record for record in records}
            scores: Dict[str, float] = {}
            total_docs = max(1, len(by_id))

            for token in q_tokens:
                hits = self._inverted_index.get(token, set())
                if not hits:
                    continue
                df = len(hits)
                idf = max(0.1, (total_docs / (1 + df)))
                for rid in hits:
                    scores[rid] = scores.get(rid, 0.0) + idf

            ranked = sorted(
                scores.keys(),
                key=lambda rid: (-scores[rid], str(by_id.get(rid, {}).get("updatedAt", ""))),
            )[: max(1, int(top_k))]

            return [by_id[rid] for rid in ranked if rid in by_id]

    def stats(self) -> dict:
        records = self.list_records()
        entity_total = 0
        relation_total = 0
        event_total = 0
        file_paths: Set[str] = set()
        chunk_ids: Set[str] = set()

        for record in records:
            metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
            entities = metadata.get("entities") if isinstance(metadata.get("entities"), list) else []
            relations = metadata.get("relations") if isinstance(metadata.get("relations"), list) else []
            events = metadata.get("events") if isinstance(metadata.get("events"), list) else []

            entity_total += len(entities)
            relation_total += len(relations)
            event_total += len(events)

            file_path = _safe_text(metadata.get("file_path"))
            chunk_id = _safe_text(metadata.get("chunk_id"))
            if file_path:
                file_paths.add(file_path)
            if chunk_id:
                chunk_ids.add(chunk_id)

        return {
            "db_path": str(WORLD_TREE_GRAPH_DB),
            "record_count": len(records),
            "entity_total": entity_total,
            "relation_total": relation_total,
            "event_total": event_total,
            "file_count": len(file_paths),
            "chunk_count": len(chunk_ids),
            "token_count": len(self._inverted_index),
        }

    def recent(self, limit: int = 20) -> list[dict]:
        rows = self.list_records()[: max(1, int(limit))]
        output: list[dict] = []
        for record in rows:
            metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
            entities = metadata.get("entities") if isinstance(metadata.get("entities"), list) else []
            relations = metadata.get("relations") if isinstance(metadata.get("relations"), list) else []
            events = metadata.get("events") if isinstance(metadata.get("events"), list) else []

            output.append({
                "id": record.get("id"),
                "judgment": record.get("judgment"),
                "reasoning": record.get("reasoning"),
                "createdAt": record.get("createdAt"),
                "updatedAt": record.get("updatedAt"),
                "file_path": metadata.get("file_path"),
                "chunk_id": metadata.get("chunk_id"),
                "entity_count": len(entities),
                "relation_count": len(relations),
                "event_count": len(events),
            })
        return output


world_tree_graph_service = WorldTreeGraphService()
