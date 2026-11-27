"""OpenAlex connector：搜索 / 单篇 / references / citations。

- cursor 分页（参考 findpapers connectors/openalex.py）
- abstract inverted index 还原（参考 openalex_search restore_abstract）
- 设置 OPENALEX_EMAIL 环境变量进入 polite pool
"""
import config
from connectors.base import HttpClient
from models.paper import Paper

BASE = "https://api.openalex.org"
_FIELDS = (
    "id,doi,title,publication_year,authorships,primary_location,"
    "cited_by_count,abstract_inverted_index,keywords,referenced_works"
)

_client = HttpClient(min_interval=0.1, timeout=config.REQUEST_TIMEOUT)


def short_id(openalex_id: str) -> str:
    return openalex_id.rstrip("/").rsplit("/", 1)[-1] if openalex_id else ""


def restore_abstract(inverted_index: dict | None) -> str:
    if not inverted_index:
        return ""
    positions = {}
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))


def _params(extra=None):
    params = {}
    if config.OPENALEX_EMAIL:
        params["mailto"] = config.OPENALEX_EMAIL
    if extra:
        params.update(extra)
    return params


def parse_work(work: dict) -> Paper:
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    paper = Paper(
        title=work.get("title") or "",
        abstract=restore_abstract(work.get("abstract_inverted_index")),
        authors=[
            a.get("author", {}).get("display_name", "")
            for a in work.get("authorships") or []
            if a.get("author", {}).get("display_name")
        ],
        year=work.get("publication_year"),
        venue=source.get("display_name") or "",
        doi=(work.get("doi") or "").replace("https://doi.org/", ""),
        openalex_id=short_id(work.get("id") or ""),
        url=location.get("landing_page_url") or work.get("id") or "",
        citation_count=work.get("cited_by_count"),
        source=["openalex"],
        keywords=[k["display_name"] for k in work.get("keywords") or [] if k.get("display_name")],
    )
    paper.ensure_id()
    return paper


def _fetch_works(params, limit):
    papers = []
    cursor = "*"
    per_page = min(200, max(25, limit))
    while len(papers) < limit:
        data = _client.get_json(
            f"{BASE}/works",
            params=_params({**params, "per-page": per_page, "cursor": cursor, "select": _FIELDS}),
        )
        results = data.get("results") or []
        if not results:
            break
        papers.extend(parse_work(w) for w in results)
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor:
            break
    return papers[:limit]


def search_openalex(query: str, limit: int = 50) -> list[Paper]:
    return _fetch_works({"filter": f"title_and_abstract.search:{query}"}, limit)


def get_openalex_work(openalex_id: str) -> Paper | None:
    work = _client.get_json(
        f"{BASE}/works/{short_id(openalex_id)}", params=_params({"select": _FIELDS})
    )
    return parse_work(work) if work else None


def get_openalex_references(openalex_id: str, limit: int = 50) -> list[Paper]:
    work = _client.get_json(
        f"{BASE}/works/{short_id(openalex_id)}", params=_params({"select": "referenced_works"})
    )
    ref_ids = [short_id(r) for r in (work.get("referenced_works") or [])][:limit]
    papers = []
    for i in range(0, len(ref_ids), 50):
        chunk = ref_ids[i : i + 50]
        papers.extend(_fetch_works({"filter": f"openalex_id:{'|'.join(chunk)}"}, len(chunk)))
    return papers


def get_openalex_citations(openalex_id: str, limit: int = 100) -> list[Paper]:
    return _fetch_works(
        {"filter": f"cites:{short_id(openalex_id)}", "sort": "cited_by_count:desc"}, limit
    )
