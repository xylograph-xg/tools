"""Embedding provider：OpenAI 兼容 /embeddings 接口 + (paper_id, model, text_hash) 缓存。

未配置 LITEXP_EMBEDDING_* 时 is_configured() 为 False，relevance 层降级为词袋打分。
缓存键用内容哈希：文本变了自然 miss，永不过期但永不陈旧（参考 openalex_search）。
"""
import hashlib
import json
import math
import urllib.error
import urllib.request

import config
from models.paper import Paper


def paper_text(paper: Paper) -> str:
    return f"Title: {paper.title}\nAbstract: {paper.abstract or ''}"


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_configured() -> bool:
    return bool(config.EMBEDDING_BASE_URL and config.EMBEDDING_API_KEY and config.EMBEDDING_MODEL)


def model_name() -> str:
    return config.EMBEDDING_MODEL or "lexical"


def _embed_batch(texts: list[str]) -> list[list[float]]:
    url = config.EMBEDDING_BASE_URL.rstrip("/") + "/embeddings"
    payload = json.dumps({"model": config.EMBEDDING_MODEL, "input": texts}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {config.EMBEDDING_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    items = data["data"]
    if not isinstance(items, list) or len(items) != len(texts):
        raise ValueError("embedding response cardinality mismatch")
    indices = [item['index'] for item in items]
    if any(type(i) is not int for i in indices) or sorted(indices) != list(range(len(texts))):
        raise ValueError("embedding response indices mismatch")
    vectors = [item['embedding'] for item in sorted(items, key=lambda item: item['index'])]
    validate_vectors(vectors, len(texts))
    return vectors


def validate_vectors(vectors, count):
    if not isinstance(vectors, list) or len(vectors) != count:
        raise ValueError("embedding cardinality mismatch")
    dimension = None
    for vector in vectors:
        if not isinstance(vector, list) or not vector:
            raise ValueError("empty or invalid embedding")
        if dimension is None:
            dimension = len(vector)
        if len(vector) != dimension or any(type(v) not in (int, float) or not math.isfinite(v) for v in vector):
            raise ValueError("invalid embedding dimension or numeric value")


def embed_texts(texts: list[str], batch_size: int = 32) -> list[list[float] | None]:
    """批量 embedding：3 次重试 + 失败后二分拆批，单条彻底失败则该位为 None。"""
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError("batch_size must be positive")
    results: list[list[float] | None] = [None] * len(texts)
    dimension = [None]

    def _run(lo: int, hi: int, retries: int):
        batch = texts[lo:hi]
        try:
            vectors = _embed_batch(batch)
            validate_vectors(vectors, len(batch))
            if dimension[0] is not None and len(vectors[0]) != dimension[0]:
                raise ValueError("embedding dimension changed across batches")
            dimension[0] = len(vectors[0])
            for index, vector in enumerate(vectors, lo):
                results[index] = vector
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, ValueError, TypeError):
            if retries > 0:
                _run(lo, hi, retries - 1)
            elif hi - lo > 1:
                mid = (lo + hi) // 2
                _run(lo, mid, 1)
                _run(mid, hi, 1)
            # 单条失败：保持 None，由调用方降级

    for lo in range(0, len(texts), batch_size):
        _run(lo, min(lo + batch_size, len(texts)), retries=3)
    return results


def embed_topic(topic: str) -> list[float] | None:
    return embed_texts([f"Topic: {topic}"])[0]


def embed_papers(store, papers: list[Paper], expected_dimension: int | None = None) -> dict[str, list[float]]:
    """缓存感知的批量 embedding：命中缓存不请求，每批落库保证断点可续。"""
    model = model_name()
    vectors: dict[str, list[float]] = {}
    pending: list[tuple[Paper, str, str]] = []  # (paper, text, hash)
    for paper in papers:
        text = paper_text(paper)
        hashed = text_hash(text)
        try:
            cached = store.get_embedding(paper.paper_id, model, hashed)
        except (ValueError, TypeError):
            continue
        if cached is not None:
            try:
                validate_vectors([cached], 1)
                if expected_dimension is not None and len(cached) != expected_dimension:
                    continue
            except (ValueError, TypeError):
                continue
            vectors[paper.paper_id] = cached
        else:
            pending.append((paper, text, hashed))

    batch_size = 32
    for lo in range(0, len(pending), batch_size):
        chunk = pending[lo : lo + batch_size]
        for (paper, _, hashed), vector in zip(chunk, embed_texts([t for _, t, _ in chunk])):
            if vector is not None and (expected_dimension is None or len(vector) == expected_dimension):
                store.save_embedding(paper.paper_id, model, hashed, vector)
                vectors[paper.paper_id] = vector
        store.commit()
    return vectors
