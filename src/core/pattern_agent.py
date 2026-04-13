import os
import json
import zlib
import base64
import sqlite3
import hashlib
import asyncio
import datetime
from typing import Any, Dict, List, Optional

import google.generativeai as genai


class PatternWeaverDaemon:
    """Daily daemon that extracts stable behavior axioms from recent telemetry."""

    def __init__(
        self,
        db_path: str = "data/db/memory.sqlite",
        gemini_model: str = "gemini-1.5-flash",
    ):
        self.db_path = db_path
        self.gemini_model_name = gemini_model

        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.gemini_model_name)
        else:
            self.model = None

        self._init_storage()

    def _init_storage(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pattern_axioms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    axiom_text TEXT NOT NULL,
                    confidence REAL,
                    scope TEXT,
                    evidence_hint TEXT,
                    axiom_hash TEXT NOT NULL,
                    axiom_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    source TEXT DEFAULT 'pattern_weaver',
                    UNIQUE(axiom_hash, axiom_date)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pattern_axiom_embeddings (
                    axiom_id INTEGER PRIMARY KEY,
                    embedding_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (axiom_id) REFERENCES pattern_axioms(id) ON DELETE CASCADE
                )
                """
            )
            conn.commit()

    async def run_forever(self) -> None:
        """Runs a daily loop that mines telemetry and persists inferred axioms."""
        while True:
            try:
                telemetry = self.collect_recent_telemetry(limit=10000)
                chunks = self.chunk_telemetry(telemetry)
                inferred = self.infer_axioms_with_gemini(chunks)
                self.persist_axioms(inferred)
            except Exception as exc:
                print(f"⚠️ PatternWeaverDaemon cycle failed: {exc}")
            await asyncio.sleep(86400)

    def collect_recent_telemetry(self, limit: int = 10000) -> List[Dict[str, Any]]:
        """Fetches latest telemetry rows from system_telemetry as dictionaries."""
        limit = max(1, int(limit))
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            order_columns = ["timestamp", "created_at", "id", "rowid"]
            last_error: Optional[Exception] = None

            for col in order_columns:
                try:
                    rows = conn.execute(
                        f"SELECT * FROM system_telemetry ORDER BY {col} DESC LIMIT ?",
                        (limit,),
                    ).fetchall()
                    return [dict(r) for r in rows]
                except Exception as exc:
                    last_error = exc

            if last_error:
                raise RuntimeError(f"Failed to query system_telemetry: {last_error}")
            return []

    def chunk_telemetry(
        self,
        telemetry_rows: List[Dict[str, Any]],
        batch_size: int = 250,
        max_chunk_chars: int = 12000,
    ) -> List[str]:
        """Builds compact JSON chunks and compresses each chunk for efficient model context packing."""
        if not telemetry_rows:
            return []

        chunks: List[str] = []
        batch: List[Dict[str, Any]] = []

        for row in telemetry_rows:
            batch.append(row)
            if len(batch) >= batch_size:
                chunks.extend(self._emit_compact_chunks(batch, max_chunk_chars=max_chunk_chars))
                batch = []

        if batch:
            chunks.extend(self._emit_compact_chunks(batch, max_chunk_chars=max_chunk_chars))

        return chunks

    def _emit_compact_chunks(self, rows: List[Dict[str, Any]], max_chunk_chars: int) -> List[str]:
        serialized = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
        if len(serialized) <= max_chunk_chars:
            return [self._compress_text(serialized)]

        mid = max(1, len(rows) // 2)
        left = self._emit_compact_chunks(rows[:mid], max_chunk_chars=max_chunk_chars)
        right = self._emit_compact_chunks(rows[mid:], max_chunk_chars=max_chunk_chars)
        return left + right

    @staticmethod
    def _compress_text(text: str) -> str:
        compressed = zlib.compress(text.encode("utf-8"), level=9)
        return base64.b64encode(compressed).decode("ascii")

    @staticmethod
    def _decompress_text(encoded: str) -> str:
        raw = base64.b64decode(encoded.encode("ascii"))
        return zlib.decompress(raw).decode("utf-8")

    def infer_axioms_with_gemini(self, chunks: List[str]) -> List[Dict[str, Any]]:
        """Sends compressed telemetry summaries to Gemini and requests strict structured JSON."""
        if not chunks or self.model is None:
            return []

        prompt = (
            "You are an observability pattern miner. "
            "I will provide compressed telemetry JSON chunks (zlib+base64). "
            "Infer durable behavioral axioms that can guide future automation decisions.\n\n"
            "Return ONLY valid JSON with this exact structure:\n"
            "{\"axioms\":[{\"axiom\":\"...\",\"confidence\":0.0,\"scope\":\"...\",\"evidence_hint\":\"...\"}]}\n\n"
            "Rules:\n"
            "- confidence must be between 0 and 1\n"
            "- no markdown, no prose outside JSON\n"
            "- generate at most 20 axioms\n"
            "- each axiom must be concise and non-duplicative\n\n"
            f"Compressed chunks:\n{json.dumps(chunks, ensure_ascii=False)}"
        )

        response = self.model.generate_content(prompt)
        raw = (response.text or "").strip()

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return []

        axioms = payload.get("axioms", [])
        normalized: List[Dict[str, Any]] = []

        for item in axioms:
            axiom_text = str(item.get("axiom", "")).strip()
            if not axiom_text:
                continue
            confidence = item.get("confidence", 0)
            try:
                confidence = max(0.0, min(1.0, float(confidence)))
            except Exception:
                confidence = 0.0

            normalized.append(
                {
                    "axiom": axiom_text,
                    "confidence": confidence,
                    "scope": str(item.get("scope", "general")).strip() or "general",
                    "evidence_hint": str(item.get("evidence_hint", "")).strip(),
                }
            )

        return normalized

    def persist_axioms(self, axioms: List[Dict[str, Any]]) -> int:
        """Stores deduplicated axioms and optional embeddings."""
        if not axioms:
            return 0

        today = datetime.date.today().isoformat()
        stored = 0

        with sqlite3.connect(self.db_path) as conn:
            for item in axioms:
                text = item.get("axiom", "").strip()
                if not text:
                    continue

                axiom_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                existing = conn.execute(
                    "SELECT id FROM pattern_axioms WHERE axiom_hash = ? AND axiom_date = ?",
                    (axiom_hash, today),
                ).fetchone()
                if existing:
                    continue

                cursor = conn.execute(
                    """
                    INSERT INTO pattern_axioms
                    (axiom_text, confidence, scope, evidence_hint, axiom_hash, axiom_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        text,
                        float(item.get("confidence", 0.0)),
                        item.get("scope", "general"),
                        item.get("evidence_hint", ""),
                        axiom_hash,
                        today,
                    ),
                )
                axiom_id = cursor.lastrowid
                stored += 1

                embedding = self._generate_embedding(text)
                if embedding:
                    conn.execute(
                        "INSERT OR REPLACE INTO pattern_axiom_embeddings (axiom_id, embedding_json) VALUES (?, ?)",
                        (axiom_id, json.dumps(embedding, separators=(",", ":"))),
                    )

            conn.commit()

        return stored

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Attempts Gemini embedding generation; safely degrades if unavailable."""
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="SEMANTIC_SIMILARITY",
            )
            values = result.get("embedding", []) if isinstance(result, dict) else []
            if isinstance(values, list) and values:
                return [float(x) for x in values]
        except Exception:
            return None
        return None
