"""相关性打分：embedding cosine 优先，未配置 embedding 时降级为词袋重叠打分。"""
import math
import re

from models.paper import Paper
from ranking import embedding

_STOPWORDS = frozenset(
    "a an the of in on for and or to with by from at as is are was were be been "
    "this that these those we our their its it into via using use based study "
    "analysis research paper review approach method methods results".split()
)
_TOKEN_RE = re.compile(r"[a-z0-9]{2,}")


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall((text or "").lower()) if t not in _STOPWORDS}


def lexical_score(topic: str, paper: Paper) -> float:
    """降级打分：topic 词在标题（权重 3）+ 摘要（权重 1）中的覆盖率。"""
    topic_tokens = _tokens(topic)
    if not topic_tokens:
        return 0.0
    title_hits = len(topic_tokens & _tokens(paper.title))
    abstract_hits = len(topic_tokens & _tokens(paper.abstract))
    return (3 * title_hits + abstract_hits) / (4 * len(topic_tokens))


def score_papers(store, topic: str, papers: list[Paper]) -> dict[str, float]:
    """对候选论文打分并写入 papers.relevance_score，返回 {paper_id: score}。"""
    scores: dict[str, float] = {}
    if embedding.is_configured():
        topic_vector = embedding.embed_topic(topic)
        if topic_vector is not None:
            for paper_id, vector in embedding.embed_papers(store, papers, expected_dimension=len(topic_vector)).items():
                scores[paper_id] = cosine(topic_vector, vector)
    for paper in papers:
        if paper.paper_id not in scores:
            scores[paper.paper_id] = lexical_score(topic, paper)
    for paper_id, score in scores.items():
        store.set_score(paper_id, score)
    store.commit()
    return scores


def rank(papers: list[Paper], scores: dict[str, float]) -> list[Paper]:
    return sorted(papers, key=lambda p: scores.get(p.paper_id, 0.0), reverse=True)
