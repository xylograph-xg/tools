# literature_explorer：自动接口快照

由全局更新生成；仅记录当前源码结构，不承诺业务语义或运行验收。默认参数值以源码/人工工具卡为准。列出的文件级函数也可能是内部实现，不自动成为公共 API。

权威目录：`literature_explorer`

## 相对已审查基线的变化

无源码变化。

## Python 声明

- `DeferredRequest.__init__(self, retry_at, reason)` — [connectors/base.py:19](literature_explorer/connectors/base.py#L19)
- `HttpClient.__init__(self, min_interval=…, timeout=…, max_retries=…, max_rate_limit_retries=…)` — [connectors/base.py:26](literature_explorer/connectors/base.py#L26)
- `HttpClient.get_json(self, url, params=…, headers=…)` — [connectors/base.py:41](literature_explorer/connectors/base.py#L41)
- `short_id(openalex_id)` — [connectors/openalex.py:20](literature_explorer/connectors/openalex.py#L20)
- `restore_abstract(inverted_index)` — [connectors/openalex.py:24](literature_explorer/connectors/openalex.py#L24)
- `parse_work(work)` — [connectors/openalex.py:43](literature_explorer/connectors/openalex.py#L43)
- `search_openalex(query, limit=…)` — [connectors/openalex.py:86](literature_explorer/connectors/openalex.py#L86)
- `get_openalex_work(openalex_id)` — [connectors/openalex.py:90](literature_explorer/connectors/openalex.py#L90)
- `get_openalex_references(openalex_id, limit=…)` — [connectors/openalex.py:97](literature_explorer/connectors/openalex.py#L97)
- `get_openalex_citations(openalex_id, limit=…)` — [connectors/openalex.py:109](literature_explorer/connectors/openalex.py#L109)
- `parse_paper(data)` — [connectors/semantic_scholar.py:31](literature_explorer/connectors/semantic_scholar.py#L31)
- `search_semantic_scholar(query, limit=…)` — [connectors/semantic_scholar.py:50](literature_explorer/connectors/semantic_scholar.py#L50)
- `get_semantic_scholar_paper(paper_id)` — [connectors/semantic_scholar.py:71](literature_explorer/connectors/semantic_scholar.py#L71)
- `get_semantic_scholar_citations(paper_id, limit=…)` — [connectors/semantic_scholar.py:98](literature_explorer/connectors/semantic_scholar.py#L98)
- `get_semantic_scholar_references(paper_id, limit=…)` — [connectors/semantic_scholar.py:102](literature_explorer/connectors/semantic_scholar.py#L102)
- `expand_from_paper(store, paper_id, run_id, round_no=…, ref_limit=…, cit_limit=…)` — [discovery/citation_expand.py:34](literature_explorer/discovery/citation_expand.py#L34)
- `run_discovery_cycle(store, topic, top_n=…, second_wave=…)` — [discovery/loop.py:12](literature_explorer/discovery/loop.py#L12)
- `initial_queries(topic)` — [discovery/query_expand.py:10](literature_explorer/discovery/query_expand.py#L10)
- `expanded_queries(store, topic, max_new=…, top_papers=…, *, current_papers=…, scores=…)` — [discovery/query_expand.py:14](literature_explorer/discovery/query_expand.py#L14)
- `search_papers(store, query, run_id, round_no=…, limit=…)` — [discovery/search.py:19](literature_explorer/discovery/search.py#L19)
- `normalize_doi(doi)` — [models/paper.py:17](literature_explorer/models/paper.py#L17)
- `normalize_title(title)` — [models/paper.py:23](literature_explorer/models/paper.py#L23)
- `Paper.dedup_key(self)` — [models/paper.py:47](literature_explorer/models/paper.py#L47)
- `Paper.ensure_id(self)` — [models/paper.py:60](literature_explorer/models/paper.py#L60)
- `Paper.merge(self, other)` — [models/paper.py:66](literature_explorer/models/paper.py#L66)
- `Paper.to_dict(self)` — [models/paper.py:93](literature_explorer/models/paper.py#L93)
- `Paper.from_dict(cls, data)` — [models/paper.py:97](literature_explorer/models/paper.py#L97)
- `paper_text(paper)` — [ranking/embedding.py:16](literature_explorer/ranking/embedding.py#L16)
- `text_hash(text)` — [ranking/embedding.py:20](literature_explorer/ranking/embedding.py#L20)
- `is_configured()` — [ranking/embedding.py:24](literature_explorer/ranking/embedding.py#L24)
- `model_name()` — [ranking/embedding.py:28](literature_explorer/ranking/embedding.py#L28)
- `validate_vectors(vectors, count)` — [ranking/embedding.py:56](literature_explorer/ranking/embedding.py#L56)
- `embed_texts(texts, batch_size=…)` — [ranking/embedding.py:69](literature_explorer/ranking/embedding.py#L69)
- `embed_topic(topic)` — [ranking/embedding.py:100](literature_explorer/ranking/embedding.py#L100)
- `embed_papers(store, papers, expected_dimension=…)` — [ranking/embedding.py:104](literature_explorer/ranking/embedding.py#L104)
- `cosine(a, b)` — [ranking/relevance.py:16](literature_explorer/ranking/relevance.py#L16)
- `lexical_score(topic, paper)` — [ranking/relevance.py:27](literature_explorer/ranking/relevance.py#L27)
- `score_papers(store, topic, papers)` — [ranking/relevance.py:37](literature_explorer/ranking/relevance.py#L37)
- `rank(papers, scores)` — [ranking/relevance.py:54](literature_explorer/ranking/relevance.py#L54)
- `record_feedback(store, paper_id, decision, note=…)` — [screening/feedback.py:5](literature_explorer/screening/feedback.py#L5)
- `interesting_papers(store)` — [screening/feedback.py:11](literature_explorer/screening/feedback.py#L11)
- `get_review_queue(store, limit=…)` — [screening/queue.py:5](literature_explorer/screening/queue.py#L5)
- `main()` — [scripts/expand_interesting.py:22](literature_explorer/scripts/expand_interesting.py#L22)
- `main()` — [scripts/review_candidates.py:34](literature_explorer/scripts/review_candidates.py#L34)
- `main()` — [scripts/search_topic.py:18](literature_explorer/scripts/search_topic.py#L18)
- `Store.__init__(self, db_path=…)` — [storage/sqlite.py:114](literature_explorer/storage/sqlite.py#L114)
- `Store.close(self)` — [storage/sqlite.py:127](literature_explorer/storage/sqlite.py#L127)
- `Store.create_run(self, topic)` — [storage/sqlite.py:138](literature_explorer/storage/sqlite.py#L138)
- `Store.finish_run(self, run_id, status=…)` — [storage/sqlite.py:147](literature_explorer/storage/sqlite.py#L147)
- `Store.latest_run(self)` — [storage/sqlite.py:151](literature_explorer/storage/sqlite.py#L151)
- `Store.upsert_paper(self, paper, metadata=…)` — [storage/sqlite.py:188](literature_explorer/storage/sqlite.py#L188)
- `Store.get_paper(self, paper_id)` — [storage/sqlite.py:261](literature_explorer/storage/sqlite.py#L261)
- `Store.set_score(self, paper_id, score)` — [storage/sqlite.py:265](literature_explorer/storage/sqlite.py#L265)
- `Store.commit(self)` — [storage/sqlite.py:270](literature_explorer/storage/sqlite.py#L270)
- `Store.count_papers(self)` — [storage/sqlite.py:273](literature_explorer/storage/sqlite.py#L273)
- `Store.add_discovery(self, paper_id, discovery_type, parent_paper_id=…, query=…, run_id=…, round_no=…, score=…)` — [storage/sqlite.py:278](literature_explorer/storage/sqlite.py#L278)
- `Store.provenance_for(self, paper_id)` — [storage/sqlite.py:288](literature_explorer/storage/sqlite.py#L288)
- `Store.record_feedback(self, paper_id, decision, note=…)` — [storage/sqlite.py:301](literature_explorer/storage/sqlite.py#L301)
- `Store.get_feedback(self, paper_id)` — [storage/sqlite.py:310](literature_explorer/storage/sqlite.py#L310)
- `Store.review_queue(self, limit=…)` — [storage/sqlite.py:316](literature_explorer/storage/sqlite.py#L316)
- `Store.interesting_papers(self)` — [storage/sqlite.py:328](literature_explorer/storage/sqlite.py#L328)
- `Store.score_for(self, paper_id)` — [storage/sqlite.py:337](literature_explorer/storage/sqlite.py#L337)
- `Store.top_scored_papers(self, limit=…)` — [storage/sqlite.py:343](literature_explorer/storage/sqlite.py#L343)
- `Store.get_embedding(self, paper_id, model, text_hash)` — [storage/sqlite.py:353](literature_explorer/storage/sqlite.py#L353)
- `Store.save_embedding(self, paper_id, model, text_hash, vector)` — [storage/sqlite.py:360](literature_explorer/storage/sqlite.py#L360)
- `Store.citation_fetch_done(self, paper_id, direction, scope_key)` — [storage/sqlite.py:369](literature_explorer/storage/sqlite.py#L369)
- `Store.mark_citation_fetch(self, paper_id, direction, scope_key, result_count)` — [storage/sqlite.py:377](literature_explorer/storage/sqlite.py#L377)
- `Store.citation_fetch_ready(self, paper_id, direction, scope_key)` — [storage/sqlite.py:388](literature_explorer/storage/sqlite.py#L388)
- `Store.fail_citation_fetch(self, paper_id, direction, scope_key, error)` — [storage/sqlite.py:395](literature_explorer/storage/sqlite.py#L395)
- `AuditRegressions.setUp(self)` — [tests/test_audit_regressions.py:20](literature_explorer/tests/test_audit_regressions.py#L20)
- `AuditRegressions.test_conflicting_doi_is_quarantined_and_stable_id_survives_enrichment(self)` — [tests/test_audit_regressions.py:27](literature_explorer/tests/test_audit_regressions.py#L27)
- `AuditRegressions.test_citation_partial_failure_retries_only_failed_provider(self)` — [tests/test_audit_regressions.py:41](literature_explorer/tests/test_audit_regressions.py#L41)
- `AuditRegressions.test_all_citation_failures_remain_retryable(self)` — [tests/test_audit_regressions.py:60](literature_explorer/tests/test_audit_regressions.py#L60)
- `AuditRegressions.test_bad_embeddings_never_populate_cache(self)` — [tests/test_audit_regressions.py:76](literature_explorer/tests/test_audit_regressions.py#L76)
- `AuditRegressions.test_embedding_invalid_responses_and_order(self)` — [tests/test_audit_regressions.py:83](literature_explorer/tests/test_audit_regressions.py#L83)
- `AuditRegressions.test_query_keywords_only_current_run(self)` — [tests/test_audit_regressions.py:99](literature_explorer/tests/test_audit_regressions.py#L99)
- `AuditRegressions.test_retry_after_is_persistent_deferred_without_sleep(self)` — [tests/test_audit_regressions.py:106](literature_explorer/tests/test_audit_regressions.py#L106)
- `AuditRegressions.test_retry_after_http_date_and_invalid_numbers(self)` — [tests/test_audit_regressions.py:114](literature_explorer/tests/test_audit_regressions.py#L114)
- `TestNormalize.test_doi_prefixes(self)` — [tests/test_core.py:15](literature_explorer/tests/test_core.py#L15)
- `TestNormalize.test_title(self)` — [tests/test_core.py:20](literature_explorer/tests/test_core.py#L20)
- `TestDedupKey.test_priority(self)` — [tests/test_core.py:28](literature_explorer/tests/test_core.py#L28)
- `TestDedupKey.test_merge_unions_sources_and_keeps_doi(self)` — [tests/test_core.py:38](literature_explorer/tests/test_core.py#L38)
- `TestScoring.test_cosine(self)` — [tests/test_core.py:53](literature_explorer/tests/test_core.py#L53)
- `TestScoring.test_lexical_prefers_title_hits(self)` — [tests/test_core.py:58](literature_explorer/tests/test_core.py#L58)
- `TestOpenAlex.test_restore_abstract(self)` — [tests/test_core.py:66](literature_explorer/tests/test_core.py#L66)
- `TestStore.setUp(self)` — [tests/test_core.py:73](literature_explorer/tests/test_core.py#L73)
- `TestStore.tearDown(self)` — [tests/test_core.py:77](literature_explorer/tests/test_core.py#L77)
- `TestStore.test_upsert_dedup_by_doi_across_sources(self)` — [tests/test_core.py:81](literature_explorer/tests/test_core.py#L81)
- `TestStore.test_feedback_and_queue(self)` — [tests/test_core.py:95](literature_explorer/tests/test_core.py#L95)
- `TestStore.test_citation_fetch_dedup(self)` — [tests/test_core.py:107](literature_explorer/tests/test_core.py#L107)
- `TestStore.test_embedding_cache(self)` — [tests/test_core.py:112](literature_explorer/tests/test_core.py#L112)
- `TestStore.test_provenance_accumulates(self)` — [tests/test_core.py:117](literature_explorer/tests/test_core.py#L117)

## 文件 SHA-256

```json
{
  "README.md": "75456e265a75b8c68ffc9d27069e7d9028688b598a1075f8515cb4078acea3d8",
  "__init__.py": "d0e3d587df1576c316566f07427274cb0a21e3b3ee543373aa21b2230978d0e5",
  "config.py": "03d006851999f509b127de5c410c6cf60a0cc90509863a731cc32b4d48a2c928",
  "connectors/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "connectors/base.py": "77ff0ecabe832ac1331696cc962fc6bd25e3b92d2a7f071eafe719b565733e81",
  "connectors/openalex.py": "09095f789be79fa0b7949ad612688b5df64df7968f5b303404befc84f5587e6c",
  "connectors/semantic_scholar.py": "0c9966bd23307b67a2d645df0ce660c98a402c5974cff4b03695f3ece86ef211",
  "discovery/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "discovery/citation_expand.py": "7323346b7a148b6e77017326e7288c2e18abf110bc79080d3d6831f72165a083",
  "discovery/loop.py": "9d8a7d832bff62aa719c2e606dc25a6650c5c9d0c1ccb7dbdbc5cfcf63d1ded8",
  "discovery/query_expand.py": "b1d607c68fbf1d304d35f559b31f37e5acc81a78dda4f93b98a7489ccf0973b7",
  "discovery/search.py": "b7731f49c08d36d88f2f71d3a2b6a902e85a9c67b858c105d77c42deb2aa58d0",
  "models/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "models/paper.py": "73fc4d02d38108e03b94f4456d7949bf3c56d42f79912e2ef8bb895f58083577",
  "pyproject.toml": "bd6377ab0c74dfaa73667d70789f64204750b5140f3470075033a3fd7df2f940",
  "ranking/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "ranking/embedding.py": "e68190fc05fb73071eec35f8d715c9680ed2caf7bcbe7ad556093acddd856806",
  "ranking/relevance.py": "197abe914e627d663afe2b740ef5e7d745beb9a61d946c1a0355882f7424bab7",
  "screening/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "screening/feedback.py": "1206167b2492272e10c0a8c79b465a0d43cba6231510f5aca02ad3230ea89584",
  "screening/queue.py": "ba09a60fb1c3ddc280a19b1456ba47b7dd521dbdd3193ab3a5350f919b7a26d0",
  "scripts/expand_interesting.py": "d47505c3ce3490f5776118afe096b2b2386927f9c5c45b8ff581610d0b04c626",
  "scripts/review_candidates.py": "7351c0df2a784d1fba16af96eeb4446f5a984ecb13b2afba4bfbaf9261a2b276",
  "scripts/search_topic.py": "a89b1661486c99d31043779ee64d5d18186cc71b38b31bb024c9dfad192613c4",
  "storage/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "storage/sqlite.py": "1fc987d2623a83204c9eb9aeab87bcdc75b5b9c5922448fcf3c26b55cf300f7f",
  "tests/test_audit_regressions.py": "4e07af4238fa210309d4116b3bb0581750e0f6c2fa812b1093c35eedd043e4ca",
  "tests/test_core.py": "51c650fff06bb2c9a3ac82128db0b163d52c4f9a9a474b72f8eda38955b0bb25"
}
```
