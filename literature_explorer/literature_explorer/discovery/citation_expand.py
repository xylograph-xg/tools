"""Citation expansion：只对 interesting 论文执行，每轮只扩一层。

防爆炸机制：
- 入口闸门：只有用户标记 interesting 的论文才会进入扩展（大纲 9.8）
- scope_key 抓取去重：同参数永不重抓（citation_fetches 表）
- paper_id 去重 + discovery_records 累积多路径 provenance
"""
import sys

import config
from connectors import openalex, semantic_scholar
from connectors.base import ConnectorError
from models.paper import Paper
from storage.sqlite import IdentityConflict


def _ingest(store, papers: list[Paper], discovery_type: str, parent_id: str,
            run_id: str, round_no: int) -> list[Paper]:
    ingested = []
    for paper in papers:
        if not paper.dedup_key():
            continue
        try:
            paper_id, _ = store.upsert_paper(paper)
        except IdentityConflict as error:
            print(f"[warn] {error}", file=sys.stderr)
            continue
        store.add_discovery(paper_id, discovery_type, parent_paper_id=parent_id,
                            run_id=run_id, round_no=round_no)
        ingested.append(store.get_paper(paper_id))
    return ingested


def expand_from_paper(store, paper_id: str, run_id: str, round_no: int = 1,
                      ref_limit: int = config.CITATION_REFERENCE_LIMIT,
                      cit_limit: int = config.CITATION_FORWARD_LIMIT) -> list[Paper]:
    seed = store.get_paper(paper_id)
    if seed is None:
        print(f"[warn] 未找到论文 {paper_id}，跳过扩展", file=sys.stderr)
        return []

    found: list[Paper] = []
    s2_id = seed.semantic_scholar_id or (f"DOI:{seed.doi}" if seed.doi else "")
    requests = []
    if seed.openalex_id:
        requests.append(('references', ref_limit, 'openalex',
            lambda: openalex.get_openalex_references(seed.openalex_id, limit=ref_limit)))
    elif seed.semantic_scholar_id:
        requests.append(('references', ref_limit, 's2',
            lambda: semantic_scholar.get_semantic_scholar_references(seed.semantic_scholar_id, limit=ref_limit)))
    if seed.openalex_id:
        requests.append(('citations', cit_limit, 'openalex',
            lambda: openalex.get_openalex_citations(seed.openalex_id, limit=cit_limit)))
    if s2_id:
        requests.append(('citations', cit_limit, 's2',
            lambda: semantic_scholar.get_semantic_scholar_citations(s2_id, limit=cit_limit)))
    for direction, limit, provider, fetch in requests:
        legacy_scope = f"{direction}|limit={limit}"
        scope = f"{legacy_scope}|provider={provider}"
        # Historical aggregate completions require a separate authorized audit.
        if store.citation_fetch_done(paper_id, direction, legacy_scope):
            continue
        if not store.citation_fetch_ready(paper_id, direction, scope):
            continue
        try:
            papers = fetch()
        except ConnectorError as error:
            store.fail_citation_fetch(paper_id, direction, scope, error)
            print(f"[warn] {provider} {direction}: {error}", file=sys.stderr)
            continue
        found += _ingest(store, papers, 'reference_of' if direction == 'references' else 'citation_of',
                         paper_id, run_id, round_no)
        store.mark_citation_fetch(paper_id, direction, scope, len(papers))
    return list({p.paper_id: p for p in found}.values())
