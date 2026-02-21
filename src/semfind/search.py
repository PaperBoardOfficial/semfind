"""Search: embed query, FAISS lookup, return ranked results."""

from dataclasses import dataclass

import faiss
import numpy as np

from .index import DEFAULT_MODEL, build_index, _get_model


@dataclass
class Result:
    file: str
    line_num: int
    text: str
    score: float


def search(
    query: str,
    filepaths: list[str],
    top_k: int = 5,
    max_distance: float | None = None,
    model_name: str = DEFAULT_MODEL,
    reindex: bool = False,
    no_cache: bool = False,
) -> list[Result]:
    """Search files for lines semantically similar to query."""
    all_embeddings: list[np.ndarray] = []
    all_metadata: list[dict] = []

    for fp in filepaths:
        embeddings, metadata = build_index(fp, model_name, reindex=reindex, no_cache=no_cache)
        if embeddings.size == 0:
            continue
        all_embeddings.append(embeddings)
        all_metadata.extend(metadata)

    if not all_embeddings:
        return []

    combined = np.vstack(all_embeddings)
    dim = combined.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(combined)

    model = _get_model(model_name)
    query_vec = np.array(list(model.embed([query])), dtype=np.float32)
    faiss.normalize_L2(query_vec)

    k = min(top_k, len(all_metadata))
    distances, indices = index.search(query_vec, k)

    results: list[Result] = []
    for score, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        if max_distance is not None and score < max_distance:
            continue
        m = all_metadata[idx]
        results.append(Result(file=m["file"], line_num=m["line_num"], text=m["text"], score=float(score)))

    return results
