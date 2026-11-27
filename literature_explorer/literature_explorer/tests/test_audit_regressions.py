import io
import json
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import config
from connectors.base import ConnectorError, DeferredRequest, HttpClient
from discovery.citation_expand import expand_from_paper
from discovery.query_expand import expanded_queries
from models.paper import Paper
from ranking import embedding
from storage.sqlite import Store, IdentityConflict


class AuditRegressions(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.db = Path(temp.name)/'test.sqlite'
        self.store = Store(self.db)
        self.addCleanup(self.store.close)

    def test_conflicting_doi_is_quarantined_and_stable_id_survives_enrichment(self):
        pid, _ = self.store.upsert_paper(Paper(openalex_id='W2', title='original'))
        enriched, _ = self.store.upsert_paper(Paper(doi='10.1/a', openalex_id='W2'))
        self.assertEqual(pid, enriched)
        self.assertEqual(self.store.get_paper(pid).paper_id, pid)
        with self.assertRaises(IdentityConflict):
            self.store.upsert_paper(Paper(doi='10.1/b', openalex_id='W2', title='wrong'))
        self.assertEqual(self.store.get_paper(pid).doi, '10.1/a')
        self.assertEqual(self.store.conn.execute('SELECT count(*) FROM identity_conflicts').fetchone()[0], 1)
        same, _ = self.store.upsert_paper(Paper(doi='https://doi.org/10.1/A', openalex_id='W3'))
        self.assertEqual(same, pid)
        other, _ = self.store.upsert_paper(Paper(doi='10.1/b', title='original'))
        self.assertNotEqual(other, pid)

    def test_citation_partial_failure_retries_only_failed_provider(self):
        pid, _ = self.store.upsert_paper(Paper(doi='10.1/a', openalex_id='W1'))
        with patch('discovery.citation_expand.openalex.get_openalex_references', return_value=[]), \
             patch('discovery.citation_expand.openalex.get_openalex_citations', return_value=[Paper(doi='10.1/c')]) as oa, \
             patch('discovery.citation_expand.semantic_scholar.get_semantic_scholar_citations', side_effect=ConnectorError('429')) as s2:
            expand_from_paper(self.store, pid, 'run')
            expand_from_paper(self.store, pid, 'run')
            self.assertEqual(oa.call_count, 1)
            self.assertEqual(s2.call_count, 1)
        row = self.store.conn.execute("SELECT * FROM citation_fetches WHERE status='deferred'").fetchone()
        self.assertIn('429', row['last_error'])
        self.store.conn.execute('UPDATE citation_fetches SET retry_at=0')
        self.store.commit()
        with patch('discovery.citation_expand.openalex.get_openalex_citations') as oa, \
             patch('discovery.citation_expand.semantic_scholar.get_semantic_scholar_citations', return_value=[Paper(doi='10.1/c')]):
            expand_from_paper(self.store, pid, 'run')
            oa.assert_not_called()
        self.assertEqual(self.store.conn.execute('SELECT count(*) FROM discovery_records').fetchone()[0], 1)

    def test_all_citation_failures_remain_retryable(self):
        pid,_=self.store.upsert_paper(Paper(doi='10.1/a',openalex_id='W1'))
        names=['openalex.get_openalex_references','openalex.get_openalex_citations',
               'semantic_scholar.get_semantic_scholar_citations']
        from contextlib import ExitStack
        with ExitStack() as stack:
            for name in names:stack.enter_context(patch('discovery.citation_expand.'+name,side_effect=ConnectorError('page failed')))
            expand_from_paper(self.store,pid,'run')
        rows=self.store.conn.execute('SELECT status FROM citation_fetches').fetchall()
        self.assertEqual([r[0] for r in rows],['deferred']*3)
        self.store.conn.execute('UPDATE citation_fetches SET retry_at=0');self.store.commit()
        with ExitStack() as stack:
            for name in names:stack.enter_context(patch('discovery.citation_expand.'+name,return_value=[]))
            expand_from_paper(self.store,pid,'run')
        self.assertEqual(self.store.conn.execute("SELECT count(*) FROM citation_fetches WHERE status='complete'").fetchone()[0],3)

    def test_bad_embeddings_never_populate_cache(self):
        papers=[Paper(doi='10.1/'+str(i)) for i in range(3)]
        for paper in papers:self.store.upsert_paper(paper)
        with patch('ranking.embedding._embed_batch',side_effect=lambda texts:[[float('nan')]]*len(texts)):
            self.assertEqual(embedding.embed_papers(self.store,papers),{})
        self.assertEqual(self.store.conn.execute('SELECT count(*) FROM embeddings').fetchone()[0],0)

    def test_embedding_invalid_responses_and_order(self):
        invalid = [[], [{'index':0,'embedding':[1]}],
            [{'index':0,'embedding':[1]}, {'index':0,'embedding':[2]}],
            [{'index':0,'embedding':[1]}, {'index':2,'embedding':[2]}],
            [{'index':0,'embedding':[float('nan')]}, {'index':1,'embedding':[2]}],
            [{'index':0,'embedding':[1,2]}, {'index':1,'embedding':[2]}]]
        for items in invalid:
            with self.subTest(items=items), patch('ranking.embedding.urllib.request.urlopen', return_value=io.BytesIO(json.dumps({'data':items}).encode())), \
                 patch.object(config,'EMBEDDING_BASE_URL','https://example.test'):
                with self.assertRaises(ValueError):embedding._embed_batch(['a','b'])
        with patch('ranking.embedding._embed_batch', return_value=[[1]]):
            self.assertEqual(len(embedding.embed_texts(['a','b','c'])), 3)
        items=[{'index':1,'embedding':[2]}, {'index':0,'embedding':[1]}]
        with patch('ranking.embedding.urllib.request.urlopen', return_value=io.BytesIO(json.dumps({'data':items}).encode())), patch.object(config,'EMBEDDING_BASE_URL','https://example.test'):
            self.assertEqual(embedding._embed_batch(['a','b']), [[1],[2]])

    def test_query_keywords_only_current_run(self):
        old=Paper(doi='10.1/old',keywords=['Graphene'])
        current=Paper(doi='10.1/current',keywords=['MR-TADF'])
        self.store.upsert_paper(old);self.store.upsert_paper(current)
        self.assertEqual(expanded_queries(self.store,'OLED',current_papers=[current],scores={current.paper_id:.3}), ['MR-TADF OLED'])
        self.assertEqual(expanded_queries(self.store,'OLED'), [])

    def test_retry_after_is_persistent_deferred_without_sleep(self):
        error=urllib.error.HTTPError('https://example.test',429,'limited',{'Retry-After':'3600'},None)
        with patch.object(config,'DB_PATH',self.db), patch('connectors.base.urllib.request.urlopen',side_effect=error) as call, patch('connectors.base.time.sleep') as sleep:
            with self.assertRaises(DeferredRequest) as caught:HttpClient(min_interval=0).get_json('https://example.test/a')
            self.assertGreater(caught.exception.retry_at,time.time()+3500)
            with self.assertRaises(DeferredRequest):HttpClient(min_interval=0).get_json('https://example.test/b')
            self.assertEqual(call.call_count,1);sleep.assert_not_called()

    def test_retry_after_http_date_and_invalid_numbers(self):
        from email.utils import formatdate
        error=urllib.error.HTTPError('https://example.test',503,'busy',
            {'Retry-After':formatdate(time.time()+3600,usegmt=True)},None)
        self.assertGreater(HttpClient._backoff(error,1,1),3500)
        for value in ('nan','inf','-1','broken'):
            error.headers={'Retry-After':value}
            self.assertTrue(0<HttpClient._backoff(error,1,1)<5)
