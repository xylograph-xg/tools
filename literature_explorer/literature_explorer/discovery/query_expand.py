"""Query expansion：确定性实现，不动用 LLM。

首轮查询就是 topic 本身；后续轮次从高相关论文的 OpenAlex keywords 元数据中
提取高频词，与 topic 拼接成新查询（参考 openalex_search 的术语反哺思路，
但只用元数据、不做 n-gram 正则提取）。
"""
from collections import Counter


def initial_queries(topic: str) -> list[str]:
    return [topic]


def expanded_queries(store, topic: str, max_new: int = 5,
                     top_papers: int = 20, *, current_papers=None, scores=None) -> list[str]:
    topic_lower = topic.lower()
    counts: Counter = Counter()
    scores = scores or {}
    papers = sorted(current_papers or [], key=lambda p: scores.get(p.paper_id, float('-inf')), reverse=True)
    for paper in papers[:top_papers]:
        for keyword in paper.keywords:
            kw = keyword.strip()
            if kw and kw.lower() not in topic_lower:
                counts[kw] += 1
    return [f"{kw} {topic}" for kw, _ in counts.most_common(max_new)]
