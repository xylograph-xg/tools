"""Semantic Scholar connector：搜索 / 单篇 / references / citations。

- offset 分页，单页上限 100
- 设置 S2_API_KEY 环境变量获得独立限速池；无 key 时按 1 rps 保守限速
- paper_id 支持 S2 paperId、"DOI:10.xxx"、"ARXIV:xxxx" 等前缀形式
"""
import config
from connectors.base import HttpClient
from models.paper import Paper

BASE = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "paperId,title,abstract,authors,year,venue,externalIds,url,citationCount,openAccessPdf"

_client = None


def _get_client() -> HttpClient:
    global _client
    if _client is None:
        _client = HttpClient(
            min_interval=0.1 if config.S2_API_KEY else 1.0,
            timeout=config.REQUEST_TIMEOUT,
        )
    return _client


def _headers():
    return {"x-api-key": config.S2_API_KEY} if config.S2_API_KEY else None


def parse_paper(data: dict) -> Paper:
    external = data.get("externalIds") or {}
    paper = Paper(
        title=data.get("title") or "",
        abstract=data.get("abstract") or "",
        authors=[a.get("name", "") for a in data.get("authors") or [] if a.get("name")],
        year=data.get("year"),
        venue=data.get("venue") or "",
        doi=external.get("DOI") or "",
        openalex_id=external.get("OpenAlex") or "",
        semantic_scholar_id=data.get("paperId") or "",
        url=data.get("url") or "",
        citation_count=data.get("citationCount"),
        source=["semantic_scholar"],
    )
    paper.ensure_id()
    return paper


def search_semantic_scholar(query: str, limit: int = 50) -> list[Paper]:
    papers = []
    offset = 0
    while len(papers) < limit:
        page_size = min(100, limit - len(papers))
        data = _get_client().get_json(
            f"{BASE}/paper/search",
            params={"query": query, "limit": page_size, "offset": offset, "fields": _FIELDS},
            headers=_headers(),
        )
        results = data.get("data") or []
        if not results:
            break
        papers.extend(parse_paper(p) for p in results if p)
        offset += len(results)
        total = data.get("total") or 0
        if offset >= total:
            break
    return papers[:limit]


def get_semantic_scholar_paper(paper_id: str) -> Paper | None:
    data = _get_client().get_json(
        f"{BASE}/paper/{paper_id}", params={"fields": _FIELDS}, headers=_headers()
    )
    return parse_paper(data) if data else None


def _fetch_edges(paper_id: str, edge: str, field: str, limit: int) -> list[Paper]:
    papers = []
    offset = 0
    while len(papers) < limit:
        page_size = min(100, limit - len(papers))
        data = _get_client().get_json(
            f"{BASE}/paper/{paper_id}/{edge}",
            params={"fields": _FIELDS, "limit": page_size, "offset": offset},
            headers=_headers(),
        )
        rows = data.get("data") or []
        if not rows:
            break
        papers.extend(parse_paper(r[field]) for r in rows if r.get(field))
        offset += len(rows)
        if len(rows) < page_size:
            break
    return papers[:limit]


def get_semantic_scholar_citations(paper_id: str, limit: int = 100) -> list[Paper]:
    return _fetch_edges(paper_id, "citations", "citingPaper", limit)


def get_semantic_scholar_references(paper_id: str, limit: int = 100) -> list[Paper]:
    return _fetch_edges(paper_id, "references", "citedPaper", limit)
