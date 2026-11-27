"""SQLite 持久化：所有搜索结果与状态可恢复，中断后可继续。

表结构（大纲第 6 节六表 + citation_fetches 抓取去重表）：
- papers            事实表，paper_id = dedup_key
- paper_sources     来源集合（一篇可被多个源发现）
- discovery_records provenance：第几轮、经由哪条查询/哪篇种子发现
- user_feedback     人工判断（interesting/reject/later）
- embeddings        (paper_id, model, text_hash) 内容哈希缓存键，无 TTL
- search_runs       每次运行
- citation_fetches  scope_key 抓取去重：同参数永不重抓
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import config
from models.paper import Paper, normalize_doi

class IdentityConflict(ValueError):
    """Incoming evidence was quarantined; existing facts were not changed."""


SCHEMA = """
CREATE TABLE IF NOT EXISTS identity_conflicts (
    incoming_json TEXT NOT NULL, existing_ids_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY(incoming_json, existing_ids_json)
);

CREATE TABLE IF NOT EXISTS papers (
    paper_id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    abstract TEXT NOT NULL DEFAULT '',
    authors_json TEXT NOT NULL DEFAULT '[]',
    keywords_json TEXT NOT NULL DEFAULT '[]',
    year INTEGER,
    venue TEXT NOT NULL DEFAULT '',
    doi TEXT NOT NULL DEFAULT '',
    openalex_id TEXT NOT NULL DEFAULT '',
    semantic_scholar_id TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    citation_count INTEGER,
    relevance_score REAL,
    status TEXT NOT NULL DEFAULT 'discovered',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);
CREATE INDEX IF NOT EXISTS idx_papers_openalex ON papers(openalex_id);
CREATE INDEX IF NOT EXISTS idx_papers_s2 ON papers(semantic_scholar_id);

CREATE TABLE IF NOT EXISTS paper_sources (
    paper_id TEXT NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (paper_id, source)
);

CREATE TABLE IF NOT EXISTS discovery_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL,
    discovery_type TEXT NOT NULL,
    parent_paper_id TEXT NOT NULL DEFAULT '',
    query TEXT NOT NULL DEFAULT '',
    run_id TEXT NOT NULL DEFAULT '',
    round INTEGER NOT NULL DEFAULT 0,
    score REAL,
    created_at TEXT NOT NULL,
    UNIQUE (paper_id, discovery_type, parent_paper_id, query, run_id)
);

CREATE TABLE IF NOT EXISTS user_feedback (
    paper_id TEXT PRIMARY KEY,
    decision TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS embeddings (
    paper_id TEXT NOT NULL,
    model TEXT NOT NULL,
    text_hash TEXT NOT NULL,
    vector_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (paper_id, model, text_hash)
);

CREATE TABLE IF NOT EXISTS search_runs (
    run_id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    started_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running'
);

CREATE TABLE IF NOT EXISTS citation_fetches (
    paper_id TEXT NOT NULL,
    direction TEXT NOT NULL,
    scope_key TEXT NOT NULL,
    status TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    result_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (paper_id, direction, scope_key)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, db_path=None):
        self.db_path = Path(db_path or config.DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        columns = {r[1] for r in self.conn.execute('PRAGMA table_info(citation_fetches)')}
        for name, kind in [('last_error', "TEXT NOT NULL DEFAULT ''"),
                           ('retry_at', 'REAL NOT NULL DEFAULT 0')]:
            if name not in columns:
                self.conn.execute(f'ALTER TABLE citation_fetches ADD COLUMN {name} {kind}')
        self.conn.commit()

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ---- runs ----

    def create_run(self, topic: str) -> str:
        run_id = uuid.uuid4().hex[:12]
        self.conn.execute(
            "INSERT INTO search_runs (run_id, topic, started_at) VALUES (?, ?, ?)",
            (run_id, topic, _now()),
        )
        self.conn.commit()
        return run_id

    def finish_run(self, run_id: str, status: str = "done"):
        self.conn.execute("UPDATE search_runs SET status = ? WHERE run_id = ?", (status, run_id))
        self.conn.commit()

    def latest_run(self) -> tuple[str, str] | None:
        row = self.conn.execute(
            "SELECT run_id, topic FROM search_runs ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        return (row["run_id"], row["topic"]) if row else None

    # ---- papers ----

    def _find_existing(self, paper: Paper) -> sqlite3.Row | None:
        matches = {}
        for column, value in (
            ("paper_id", paper.paper_id),
            ("doi", normalize_doi(paper.doi)),
            ("openalex_id", paper.openalex_id),
            ("semantic_scholar_id", paper.semantic_scholar_id),
        ):
            if not value:
                continue
            if column == "doi":
                row = self.conn.execute(
                    "SELECT * FROM papers WHERE lower(doi) = ?", (value,)
                ).fetchone()
            else:
                row = self.conn.execute(
                    f"SELECT * FROM papers WHERE {column} = ?", (value,)
                ).fetchone()
            if row:
                matches[row['paper_id']] = row
        conflicts = [row for row in matches.values() if paper.doi and row['doi']
                     and normalize_doi(paper.doi) != normalize_doi(row['doi'])]
        if conflicts or len(matches) > 1:
            self.conn.execute('INSERT OR IGNORE INTO identity_conflicts VALUES(?,?,?)',
                (json.dumps(paper.to_dict(), sort_keys=True), json.dumps(sorted(matches)), _now()))
            self.conn.commit()
            raise IdentityConflict('contradictory identity claims; evidence quarantined')
        return next(iter(matches.values()), None)

    def upsert_paper(self, paper: Paper, metadata: dict | None = None) -> tuple[str, bool]:
        """返回 (paper_id, is_new)。已存在则按 merge 规则补全字段。"""
        paper.doi = normalize_doi(paper.doi)
        paper.ensure_id()
        if not paper.paper_id:
            raise ValueError("paper has no usable identity (no DOI/OA/S2 id/title)")
        existing = self._find_existing(paper)
        now = _now()
        if existing:
            merged = self._row_to_paper(existing)
            merged.merge(paper)
            self.conn.execute(
                """UPDATE papers SET title=?, abstract=?, authors_json=?, keywords_json=?,
                   year=?, venue=?, doi=?, openalex_id=?, semantic_scholar_id=?, url=?,
                   citation_count=?, updated_at=? WHERE paper_id=?""",
                (
                    merged.title, merged.abstract, json.dumps(merged.authors, ensure_ascii=False),
                    json.dumps(merged.keywords, ensure_ascii=False), merged.year, merged.venue,
                    merged.doi, merged.openalex_id, merged.semantic_scholar_id, merged.url,
                    merged.citation_count, now, existing["paper_id"],
                ),
            )
            paper_id = existing["paper_id"]
            is_new = False
        else:
            self.conn.execute(
                """INSERT INTO papers (paper_id, title, abstract, authors_json, keywords_json,
                   year, venue, doi, openalex_id, semantic_scholar_id, url, citation_count,
                   status, metadata_json, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    paper.paper_id, paper.title, paper.abstract,
                    json.dumps(paper.authors, ensure_ascii=False),
                    json.dumps(paper.keywords, ensure_ascii=False), paper.year, paper.venue,
                    paper.doi, paper.openalex_id, paper.semantic_scholar_id, paper.url,
                    paper.citation_count, paper.status,
                    json.dumps(metadata or {}, ensure_ascii=False), now, now,
                ),
            )
            paper_id = paper.paper_id
            is_new = True
        for source in paper.source:
            self.conn.execute(
                "INSERT OR IGNORE INTO paper_sources (paper_id, source) VALUES (?, ?)",
                (paper_id, source),
            )
        self.conn.commit()
        return paper_id, is_new

    def _row_to_paper(self, row: sqlite3.Row) -> Paper:
        sources = [
            r["source"]
            for r in self.conn.execute(
                "SELECT source FROM paper_sources WHERE paper_id = ?", (row["paper_id"],)
            )
        ]
        return Paper(
            paper_id=row["paper_id"],
            title=row["title"],
            abstract=row["abstract"],
            authors=json.loads(row["authors_json"]),
            keywords=json.loads(row["keywords_json"]),
            year=row["year"],
            venue=row["venue"],
            doi=row["doi"],
            openalex_id=row["openalex_id"],
            semantic_scholar_id=row["semantic_scholar_id"],
            url=row["url"],
            citation_count=row["citation_count"],
            source=sources,
            status=row["status"],
        )

    def get_paper(self, paper_id: str) -> Paper | None:
        row = self.conn.execute("SELECT * FROM papers WHERE paper_id = ?", (paper_id,)).fetchone()
        return self._row_to_paper(row) if row else None

    def set_score(self, paper_id: str, score: float):
        self.conn.execute(
            "UPDATE papers SET relevance_score = ? WHERE paper_id = ?", (score, paper_id)
        )

    def commit(self):
        self.conn.commit()

    def count_papers(self) -> int:
        return self.conn.execute("SELECT COUNT(*) AS c FROM papers").fetchone()["c"]

    # ---- discovery ----

    def add_discovery(self, paper_id, discovery_type, parent_paper_id="",
                      query="", run_id="", round_no=0, score=None):
        self.conn.execute(
            """INSERT OR IGNORE INTO discovery_records
               (paper_id, discovery_type, parent_paper_id, query, run_id, round, score, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (paper_id, discovery_type, parent_paper_id, query, run_id, round_no, score, _now()),
        )
        self.conn.commit()

    def provenance_for(self, paper_id: str) -> list[str]:
        rows = self.conn.execute(
            """SELECT discovery_type, parent_paper_id, query, round FROM discovery_records
               WHERE paper_id = ? ORDER BY round, id""",
            (paper_id,),
        ).fetchall()
        return [
            f"r{r['round']}:{r['discovery_type']}:{r['query'] or r['parent_paper_id']}"
            for r in rows
        ]

    # ---- feedback & review queue ----

    def record_feedback(self, paper_id: str, decision: str, note: str = ""):
        self.conn.execute(
            """INSERT INTO user_feedback (paper_id, decision, note, updated_at) VALUES (?,?,?,?)
               ON CONFLICT(paper_id) DO UPDATE SET decision=excluded.decision,
               note=excluded.note, updated_at=excluded.updated_at""",
            (paper_id, decision, note, _now()),
        )
        self.conn.commit()

    def get_feedback(self, paper_id: str) -> str | None:
        row = self.conn.execute(
            "SELECT decision FROM user_feedback WHERE paper_id = ?", (paper_id,)
        ).fetchone()
        return row["decision"] if row else None

    def review_queue(self, limit: int = 50) -> list[Paper]:
        """已打分、未被判定为 interesting/reject 的论文（later 会回到队列）。"""
        rows = self.conn.execute(
            """SELECT p.* FROM papers p
               LEFT JOIN user_feedback f ON f.paper_id = p.paper_id
               WHERE f.decision IS NULL OR f.decision = 'later'
               ORDER BY p.relevance_score IS NULL, p.relevance_score DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [self._row_to_paper(r) for r in rows]

    def interesting_papers(self) -> list[Paper]:
        rows = self.conn.execute(
            """SELECT p.* FROM papers p
               JOIN user_feedback f ON f.paper_id = p.paper_id
               WHERE f.decision = 'interesting'
               ORDER BY p.relevance_score DESC"""
        ).fetchall()
        return [self._row_to_paper(r) for r in rows]

    def score_for(self, paper_id: str) -> float | None:
        row = self.conn.execute(
            "SELECT relevance_score FROM papers WHERE paper_id = ?", (paper_id,)
        ).fetchone()
        return row["relevance_score"] if row else None

    def top_scored_papers(self, limit: int = 20) -> list[Paper]:
        rows = self.conn.execute(
            """SELECT * FROM papers WHERE relevance_score IS NOT NULL
               ORDER BY relevance_score DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [self._row_to_paper(r) for r in rows]

    # ---- embeddings cache ----

    def get_embedding(self, paper_id: str, model: str, text_hash: str) -> list[float] | None:
        row = self.conn.execute(
            "SELECT vector_json FROM embeddings WHERE paper_id=? AND model=? AND text_hash=?",
            (paper_id, model, text_hash),
        ).fetchone()
        return json.loads(row["vector_json"]) if row else None

    def save_embedding(self, paper_id: str, model: str, text_hash: str, vector: list[float]):
        self.conn.execute(
            """INSERT OR IGNORE INTO embeddings (paper_id, model, text_hash, vector_json, created_at)
               VALUES (?,?,?,?,?)""",
            (paper_id, model, text_hash, json.dumps(vector), _now()),
        )

    # ---- citation fetch dedup ----

    def citation_fetch_done(self, paper_id: str, direction: str, scope_key: str) -> bool:
        row = self.conn.execute(
            """SELECT status FROM citation_fetches
               WHERE paper_id=? AND direction=? AND scope_key=?""",
            (paper_id, direction, scope_key),
        ).fetchone()
        return bool(row and row["status"] == "complete")

    def mark_citation_fetch(self, paper_id: str, direction: str, scope_key: str, result_count: int):
        self.conn.execute(
            """INSERT INTO citation_fetches (paper_id, direction, scope_key, status, fetched_at, result_count)
               VALUES (?,?,?,'complete',?,?)
               ON CONFLICT(paper_id, direction, scope_key)
               DO UPDATE SET status='complete', fetched_at=excluded.fetched_at,
               result_count=excluded.result_count,last_error='',retry_at=0""",
            (paper_id, direction, scope_key, _now(), result_count),
        )
        self.conn.commit()

    def citation_fetch_ready(self, paper_id, direction, scope_key):
        import time
        row = self.conn.execute('SELECT status,retry_at FROM citation_fetches '
            'WHERE paper_id=? AND direction=? AND scope_key=?',
            (paper_id,direction,scope_key)).fetchone()
        return not row or (row['status'] != 'complete' and row['retry_at'] <= time.time())

    def fail_citation_fetch(self, paper_id, direction, scope_key, error):
        import time
        retry_at = max(time.time() + 60, getattr(error, 'retry_at', 0))
        self.conn.execute("INSERT INTO citation_fetches "
            "(paper_id,direction,scope_key,status,fetched_at,last_error,retry_at) "
            "VALUES(?,?,?,'deferred',?,?,?) ON CONFLICT(paper_id,direction,scope_key) "
            "DO UPDATE SET status='deferred',fetched_at=excluded.fetched_at,"
            "last_error=excluded.last_error,retry_at=excluded.retry_at",
            (paper_id,direction,scope_key,_now(),str(error),retry_at))
        self.conn.commit()
