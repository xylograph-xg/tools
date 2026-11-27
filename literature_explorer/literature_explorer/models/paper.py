"""统一 Paper 数据模型：去重键、合并规则、序列化。

去重优先级（大纲 9.4）：DOI → OpenAlex ID → Semantic Scholar ID → normalized title
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field

_DOI_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.IGNORECASE)
_HTML_RE = re.compile(r"<[^>]+>")
_NON_ALNUM_RE = re.compile(r"[^0-9a-z一-鿿]+")
_WS_RE = re.compile(r"\s+")


def normalize_doi(doi: str | None) -> str:
    if not doi:
        return ""
    return _WS_RE.sub("", _DOI_RE.sub("", doi.strip())).lower()


def normalize_title(title: str | None) -> str:
    if not title:
        return ""
    text = unicodedata.normalize("NFKC", _HTML_RE.sub(" ", title)).lower()
    return _WS_RE.sub(" ", _NON_ALNUM_RE.sub(" ", text)).strip()


@dataclass
class Paper:
    paper_id: str = ""
    title: str = ""
    abstract: str = ""
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str = ""
    doi: str = ""
    openalex_id: str = ""
    semantic_scholar_id: str = ""
    url: str = ""
    citation_count: int | None = None
    source: list[str] = field(default_factory=list)
    status: str = "discovered"
    keywords: list[str] = field(default_factory=list)

    def dedup_key(self) -> str:
        doi = normalize_doi(self.doi)
        if doi:
            return f"doi:{doi}"
        if self.openalex_id:
            return f"openalex:{self.openalex_id}"
        if self.semantic_scholar_id:
            return f"s2:{self.semantic_scholar_id}"
        title = normalize_title(self.title)
        if title:
            return f"title:{title}"
        return ""

    def ensure_id(self) -> str:
        key = self.dedup_key()
        if key:
            self.paper_id = key
        return self.paper_id

    def merge(self, other: "Paper") -> "Paper":
        """最完整优先：None 让位、字符串取长、数值取大、集合求并；DOI 先到先得。"""
        if self.doi and other.doi and normalize_doi(self.doi) != normalize_doi(other.doi):
            raise ValueError("conflicting DOI; automatic merge refused")
        stable_id = self.paper_id
        if not self.doi and other.doi:
            self.doi = other.doi
        for attr in ("openalex_id", "semantic_scholar_id", "url", "venue"):
            if not getattr(self, attr) and getattr(other, attr):
                setattr(self, attr, getattr(other, attr))
        if len(other.title) > len(self.title):
            self.title = other.title
        if len(other.abstract or "") > len(self.abstract or ""):
            self.abstract = other.abstract
        if self.year is None:
            self.year = other.year
        if (other.citation_count or 0) > (self.citation_count or 0):
            self.citation_count = other.citation_count
        if len(other.authors) > len(self.authors):
            self.authors = other.authors
        for group in ("source", "keywords"):
            merged = list(dict.fromkeys(getattr(self, group) + getattr(other, group)))
            setattr(self, group, merged)
        if not stable_id:
            self.ensure_id()
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Paper":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
