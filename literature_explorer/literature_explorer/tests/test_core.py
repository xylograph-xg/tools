import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from connectors.openalex import restore_abstract
from models.paper import Paper, normalize_doi, normalize_title
from ranking.relevance import cosine, lexical_score
from storage.sqlite import Store


class TestNormalize(unittest.TestCase):
    def test_doi_prefixes(self):
        self.assertEqual(normalize_doi("https://doi.org/10.1002/ABC"), "10.1002/abc")
        self.assertEqual(normalize_doi("DOI: 10.1/X"), "10.1/x")
        self.assertEqual(normalize_doi(""), "")

    def test_title(self):
        self.assertEqual(
            normalize_title("<b>Triplet</b>  Exciton: A Study!"), "triplet exciton a study"
        )
        self.assertEqual(normalize_title(None), "")


class TestDedupKey(unittest.TestCase):
    def test_priority(self):
        p = Paper(doi="10.1/X", openalex_id="W1", semantic_scholar_id="abc", title="T")
        self.assertEqual(p.dedup_key(), "doi:10.1/x")
        p.doi = ""
        self.assertEqual(p.dedup_key(), "openalex:W1")
        p.openalex_id = ""
        self.assertEqual(p.dedup_key(), "s2:abc")
        p.semantic_scholar_id = ""
        self.assertEqual(p.dedup_key(), "title:t")

    def test_merge_unions_sources_and_keeps_doi(self):
        a = Paper(doi="10.1/x", title="short", source=["openalex"], citation_count=3)
        b = Paper(doi="https://doi.org/10.1/X", title="a much longer title",
                  source=["semantic_scholar"], citation_count=10,
                  semantic_scholar_id="s2id")
        a.ensure_id()
        a.merge(b)
        self.assertEqual(a.paper_id, "doi:10.1/x")
        self.assertEqual(a.title, "a much longer title")
        self.assertEqual(a.citation_count, 10)
        self.assertEqual(a.semantic_scholar_id, "s2id")
        self.assertEqual(a.source, ["openalex", "semantic_scholar"])


class TestScoring(unittest.TestCase):
    def test_cosine(self):
        self.assertAlmostEqual(cosine([1, 0], [1, 0]), 1.0)
        self.assertAlmostEqual(cosine([1, 0], [0, 1]), 0.0)
        self.assertEqual(cosine([0, 0], [1, 1]), 0.0)

    def test_lexical_prefers_title_hits(self):
        topic = "OLED triplet exciton"
        hit = Paper(title="Triplet exciton dynamics in OLED")
        miss = Paper(title="Unrelated work", abstract="nothing matching here")
        self.assertGreater(lexical_score(topic, hit), lexical_score(topic, miss))


class TestOpenAlex(unittest.TestCase):
    def test_restore_abstract(self):
        index = {"hello": [0, 2], "world": [1]}
        self.assertEqual(restore_abstract(index), "hello world hello")
        self.assertEqual(restore_abstract(None), "")


class TestStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_upsert_dedup_by_doi_across_sources(self):
        p1 = Paper(doi="10.1/x", title="Title", source=["openalex"])
        p2 = Paper(doi="10.1/X", title="Title", source=["semantic_scholar"],
                   semantic_scholar_id="s2")
        id1, new1 = self.store.upsert_paper(p1)
        id2, new2 = self.store.upsert_paper(p2)
        self.assertTrue(new1)
        self.assertFalse(new2)
        self.assertEqual(id1, id2)
        self.assertEqual(self.store.count_papers(), 1)
        merged = self.store.get_paper(id1)
        self.assertEqual(merged.semantic_scholar_id, "s2")
        self.assertEqual(sorted(merged.source), ["openalex", "semantic_scholar"])

    def test_feedback_and_queue(self):
        p = Paper(doi="10.1/y", title="T")
        pid, _ = self.store.upsert_paper(p)
        self.assertEqual(len(self.store.review_queue()), 1)
        self.store.record_feedback(pid, "reject")
        self.assertEqual(len(self.store.review_queue()), 0)
        self.store.record_feedback(pid, "later")
        self.assertEqual(len(self.store.review_queue()), 1)
        self.store.record_feedback(pid, "interesting")
        self.assertEqual(len(self.store.interesting_papers()), 1)
        self.assertEqual(len(self.store.review_queue()), 0)

    def test_citation_fetch_dedup(self):
        self.assertFalse(self.store.citation_fetch_done("p", "references", "k"))
        self.store.mark_citation_fetch("p", "references", "k", 5)
        self.assertTrue(self.store.citation_fetch_done("p", "references", "k"))

    def test_embedding_cache(self):
        self.assertIsNone(self.store.get_embedding("p", "m", "h"))
        self.store.save_embedding("p", "m", "h", [0.1, 0.2])
        self.assertEqual(self.store.get_embedding("p", "m", "h"), [0.1, 0.2])

    def test_provenance_accumulates(self):
        pid, _ = self.store.upsert_paper(Paper(doi="10.1/z", title="T"))
        self.store.add_discovery(pid, "topic_search", query="q1", run_id="r1")
        self.store.add_discovery(pid, "reference_of", parent_paper_id="p2", run_id="r2", round_no=1)
        provenance = self.store.provenance_for(pid)
        self.assertEqual(len(provenance), 2)
        self.assertIn("r0:topic_search:q1", provenance)


if __name__ == "__main__":
    unittest.main()
