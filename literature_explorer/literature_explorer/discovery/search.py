"""双源搜索：OpenAlex + Semantic Scholar → 标准化 → 去重合并 → 入库 → 记 provenance。

单源失败降级为警告，不拖垮整体（参考 findpapers 容错哲学）。
"""
import sys

import config
from connectors import openalex, semantic_scholar
from connectors.base import ConnectorError
from models.paper import Paper
from storage.sqlite import IdentityConflict

_SEARCHERS = (
    ("openalex", openalex.search_openalex),
    ("semantic_scholar", semantic_scholar.search_semantic_scholar),
)


def search_papers(store, query: str, run_id: str, round_no: int = 0,
                  limit: int = config.SEARCH_PER_SOURCE_LIMIT) -> list[Paper]:
    collected: dict[str, Paper] = {}
    for name, searcher in _SEARCHERS:
        try:
            results = searcher(query, limit=limit)
        except ConnectorError as e:
            print(f"[warn] {name} 搜索失败（已跳过）: {e}", file=sys.stderr)
            continue
        for paper in results:
            key = paper.dedup_key()
            if not key:
                continue
            if key in collected:
                collected[key].merge(paper)
            else:
                collected[key] = paper

    papers = []
    for paper in collected.values():
        try:
            paper_id, _ = store.upsert_paper(paper)
        except IdentityConflict as error:
            print(f"[warn] {error}", file=sys.stderr)
            continue
        store.add_discovery(paper_id, "topic_search", query=query,
                            run_id=run_id, round_no=round_no)
        papers.append(store.get_paper(paper_id))
    return papers
