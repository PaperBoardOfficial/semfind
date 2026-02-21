"""Indexing: embed file lines, save/load from cache."""

import hashlib
import json
import os
from pathlib import Path

import faiss
import numpy as np
from fastembed import TextEmbedding

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
CACHE_DIR = Path.home() / ".cache" / "semfind"

# Module-level model cache to avoid re-loading across calls
_model_cache: dict[str, TextEmbedding] = {}


def _get_model(model_name: str) -> TextEmbedding:
    if model_name not in _model_cache:
        _model_cache[model_name] = TextEmbedding(model_name=model_name)
    return _model_cache[model_name]


def _content_hash(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _cache_key(filepath: str, model_name: str, content_hash: str) -> str:
    raw = f"{os.path.abspath(filepath)}|{content_hash}|{model_name}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_paths(key: str) -> tuple[Path, Path]:
    return CACHE_DIR / f"{key}.npy", CACHE_DIR / f"{key}.json"


def _load_cache(filepath: str, model_name: str) -> tuple[np.ndarray, list[dict]] | None:
    ch = _content_hash(filepath)
    key = _cache_key(filepath, model_name, ch)
    npy_path, json_path = _cache_paths(key)
    if npy_path.exists() and json_path.exists():
        embeddings = np.load(npy_path)
        with open(json_path) as f:
            metadata = json.load(f)
        return embeddings, metadata
    return None


def _save_cache(filepath: str, model_name: str, embeddings: np.ndarray, metadata: list[dict]) -> None:
    ch = _content_hash(filepath)
    key = _cache_key(filepath, model_name, ch)
    npy_path, json_path = _cache_paths(key)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.save(npy_path, embeddings)
    with open(json_path, "w") as f:
        json.dump(metadata, f)


def build_index(
    filepath: str,
    model_name: str = DEFAULT_MODEL,
    reindex: bool = False,
    no_cache: bool = False,
) -> tuple[np.ndarray, list[dict]]:
    """Embed all non-empty lines of a file. Returns (embeddings, metadata)."""
    if not reindex and not no_cache:
        cached = _load_cache(filepath, model_name)
        if cached is not None:
            return cached

    with open(filepath) as f:
        raw_lines = f.readlines()

    lines: list[str] = []
    metadata: list[dict] = []
    for i, line in enumerate(raw_lines):
        stripped = line.rstrip("\n")
        if stripped.strip():
            lines.append(stripped)
            metadata.append({"file": filepath, "line_num": i + 1, "text": stripped})

    if not lines:
        empty = np.empty((0, 0), dtype=np.float32)
        return empty, []

    model = _get_model(model_name)
    embeddings = np.array(list(model.embed(lines)), dtype=np.float32)
    faiss.normalize_L2(embeddings)

    if not no_cache:
        _save_cache(filepath, model_name, embeddings, metadata)

    return embeddings, metadata
