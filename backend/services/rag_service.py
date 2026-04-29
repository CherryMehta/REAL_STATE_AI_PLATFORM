from __future__ import annotations

import hashlib
import json
import math
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from collections import Counter
from pathlib import Path

from app.core.config import get_settings


def _chunk_text(text: str, *, chunk_size: int = 900, overlap: int = 160) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        chunks.append(cleaned[start:end].strip())
        if end >= len(cleaned):
            break
        start = max(end - overlap, start + 1)
    return chunks


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    distance: float


def _tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2]


def _bm25_scores(query: str, chunks: list[dict]) -> list[tuple[float, dict]]:
    query_terms = _tokenize(query)
    if not query_terms:
        return [(1.0, chunk) for chunk in chunks]

    tokenized_chunks = [_tokenize(str(chunk.get("text", ""))) for chunk in chunks]
    chunk_count = max(len(tokenized_chunks), 1)
    average_length = sum(len(tokens) for tokens in tokenized_chunks) / chunk_count
    average_length = max(average_length, 1.0)
    document_frequency = Counter(
        term
        for tokens in tokenized_chunks
        for term in set(tokens)
    )

    k1 = 1.5
    b = 0.75
    scored: list[tuple[float, dict]] = []
    for chunk, tokens in zip(chunks, tokenized_chunks, strict=False):
        term_frequency = Counter(tokens)
        score = 0.0
        for term in query_terms:
            frequency = term_frequency.get(term, 0)
            if frequency == 0:
                continue

            idf = math.log(1 + (chunk_count - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
            denominator = frequency + k1 * (1 - b + b * (len(tokens) / average_length))
            score += idf * ((frequency * (k1 + 1)) / denominator)

        scored.append((1.0 / (1.0 + score), chunk))
    return scored


def _cosine_distance(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 1.0

    dot = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 1.0
    return 1.0 - (dot / (left_norm * right_norm))


class EmbeddingApiClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.resolved_embeddings_api_key)

    def embed(self, texts: list[str]) -> list[list[float]] | None:
        if not texts or not self.enabled:
            return None

        endpoint = f"{self.settings.embeddings_base_url.rstrip('/')}/embeddings"
        payload = json.dumps({"model": self.settings.embeddings_model, "input": texts}).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.settings.resolved_embeddings_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.settings.embeddings_timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return None

        data = body.get("data", [])
        embeddings: list[list[float]] = []
        for item in data:
            embedding = item.get("embedding") if isinstance(item, dict) else None
            if not isinstance(embedding, list):
                return None
            embeddings.append([float(value) for value in embedding])

        return embeddings if len(embeddings) == len(texts) else None


class RagService:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.store_path = Path(settings.rag_store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.embedding_api = EmbeddingApiClient()
        self._store = self._load_store()

    def _load_store(self) -> dict:
        if not self.store_path.exists():
            return {"documents": {}}
        try:
            with self.store_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return {"documents": {}}
        return data if isinstance(data, dict) else {"documents": {}}

    def _save_store(self) -> None:
        with self.store_path.open("w", encoding="utf-8") as file:
            json.dump(self._store, file, ensure_ascii=False, indent=2)

    def ingest(self, document_id: str, text: str, metadata: dict | None = None) -> int:
        chunks = _chunk_text(text)
        if not chunks:
            return 0

        embeddings = self.embedding_api.embed(chunks)
        stored_chunks = []
        for index, chunk in enumerate(chunks):
            chunk_key = hashlib.sha1(f"{document_id}:{index}:{chunk}".encode("utf-8")).hexdigest()
            merged_meta = {"document_id": document_id, "chunk_index": index}
            if metadata:
                merged_meta.update(metadata)
            stored_chunks.append(
                {
                    "id": chunk_key,
                    "text": chunk,
                    "metadata": merged_meta,
                    "embedding": embeddings[index] if embeddings else None,
                }
            )

        self._store.setdefault("documents", {})[document_id] = {"chunks": stored_chunks}
        self._save_store()
        return len(chunks)

    def retrieve(self, document_id: str, query: str, *, k: int = 4) -> list[RetrievedChunk]:
        document = self._store.get("documents", {}).get(document_id, {})
        chunks = document.get("chunks", [])
        if not isinstance(chunks, list):
            return []

        query_embedding = self.embedding_api.embed([query])
        has_chunk_embeddings = any(chunk.get("embedding") for chunk in chunks if isinstance(chunk, dict))
        if query_embedding and has_chunk_embeddings:
            scored = [
                (
                    _cosine_distance(query_embedding[0], chunk.get("embedding") or []),
                    chunk,
                )
                for chunk in chunks
            ]
        else:
            scored = _bm25_scores(query, chunks)

        scored.sort(key=lambda item: item[0])
        retrieved: list[RetrievedChunk] = []
        for distance, chunk in scored[:k]:
            meta = chunk.get("metadata", {}) if isinstance(chunk, dict) else {}
            retrieved.append(
                RetrievedChunk(
                    chunk_id=str(meta.get("chunk_index", "0")),
                    text=str(chunk.get("text", "")),
                    distance=float(distance),
                )
            )
        return retrieved
