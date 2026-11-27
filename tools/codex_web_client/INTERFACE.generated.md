# codex_web_client：自动接口快照

由全局更新生成；仅记录当前源码结构，不承诺业务语义或运行验收。默认参数值以源码/人工工具卡为准。列出的文件级函数也可能是内部实现，不自动成为公共 API。

权威目录：`../paper/codex_web_client`

## 相对已审查基线的变化

无源码变化。

## Python 声明

- `main()` — [__main__.py:10](../../../paper/codex_web_client/__main__.py#L10)
- `Client.__init__(self, state_dir=…, *, port=…, timeout=…)` — [api.py:126](../../../paper/codex_web_client/api.py#L126)
- `Client.health(self)` — [api.py:160](../../../paper/codex_web_client/api.py#L160)
- `Client.submit(self, key, prompt, *, workdir=…, require_command=…, expected=…, json_match=…, images=…, guarded=…)` — [api.py:178](../../../paper/codex_web_client/api.py#L178)
- `Client.get(self, key)` — [api.py:219](../../../paper/codex_web_client/api.py#L219)
- `Client.counts(self)` — [api.py:232](../../../paper/codex_web_client/api.py#L232)
- `Client.dispatch_status(self)` — [api.py:236](../../../paper/codex_web_client/api.py#L236)
- `Client.run_once(self, *, before_send=…, key=…, pro_first=…, parallel_slot=…, allow_pro=…)` — [api.py:265](../../../paper/codex_web_client/api.py#L265)
- `ClientTests.setUp(self)` — [tests/test_client.py:13](../../../paper/codex_web_client/tests/test_client.py#L13)
- `ClientTests.evidence(self, text, *, command=…, message=…, completed=…, exited=…)` — [tests/test_client.py:18](../../../paper/codex_web_client/tests/test_client.py#L18)
- `ClientTests.test_finished_without_command(self)` — [tests/test_client.py:35](../../../paper/codex_web_client/tests/test_client.py#L35)
- `ClientTests.test_incomplete(self)` — [tests/test_client.py:40](../../../paper/codex_web_client/tests/test_client.py#L40)
- `ClientTests.test_mixed_answer(self)` — [tests/test_client.py:44](../../../paper/codex_web_client/tests/test_client.py#L44)
- `ClientTests.test_unknown_exit(self)` — [tests/test_client.py:48](../../../paper/codex_web_client/tests/test_client.py#L48)
- `ClientTests.test_recover_and_reuse(self)` — [tests/test_client.py:52](../../../paper/codex_web_client/tests/test_client.py#L52)
- `ClientTests.test_json_accept(self)` — [tests/test_client.py:61](../../../paper/codex_web_client/tests/test_client.py#L61)
- `ClientTests.test_json_reject_wrong_type_or_duplicate(self)` — [tests/test_client.py:65](../../../paper/codex_web_client/tests/test_client.py#L65)
- `ClientTests.test_lock_and_offline(self)` — [tests/test_client.py:71](../../../paper/codex_web_client/tests/test_client.py#L71)
- `ClientTests.test_concurrent_submission(self)` — [tests/test_client.py:81](../../../paper/codex_web_client/tests/test_client.py#L81)
- `ClientTests.fake_cli(self, body)` — [tests/test_client.py:87](../../../paper/codex_web_client/tests/test_client.py#L87)
- `ClientTests.test_timeout_is_not_replayed(self)` — [tests/test_client.py:93](../../../paper/codex_web_client/tests/test_client.py#L93)
- `ClientTests.test_exited_zero_without_events(self)` — [tests/test_client.py:102](../../../paper/codex_web_client/tests/test_client.py#L102)
- `ClientTests.test_backoff_persists_across_workers_and_clears_on_success(self)` — [tests/test_client.py:110](../../../paper/codex_web_client/tests/test_client.py#L110)
- `ClientTests.test_guarded_images_frozen_select_exact_job(self)` — [tests/test_client.py:121](../../../paper/codex_web_client/tests/test_client.py#L121)
- `ClientTests.test_pro_then_extra_high_then_high_with_persistent_quota_evidence(self)` — [tests/test_client.py:135](../../../paper/codex_web_client/tests/test_client.py#L135)
- `ClientTests.test_general_limit_and_uncertain_submission_never_retry_job(self)` — [tests/test_client.py:154](../../../paper/codex_web_client/tests/test_client.py#L154)
- `ClientTests.test_app_upload_quota_blocks_next_dispatch_across_models_and_restart(self)` — [tests/test_client.py:164](../../../paper/codex_web_client/tests/test_client.py#L164)
- `ClientTests.test_five_parallel_keys_keep_exclusive_job_and_slot_locks(self)` — [tests/test_client.py:178](../../../paper/codex_web_client/tests/test_client.py#L178)
- `ClientTests.test_parallel_success_keeps_another_jobs_quota_cooldown(self)` — [tests/test_client.py:207](../../../paper/codex_web_client/tests/test_client.py#L207)
- `ClientTests.test_absent_pro_starts_extra_high_then_high_on_unsent_tier_quota(self)` — [tests/test_client.py:216](../../../paper/codex_web_client/tests/test_client.py#L216)

## 文件 SHA-256

```json
{
  "README.md": "e9f17aec333059288c5329ed4859f9adc39095b1fcc789aea03150c544b38df2",
  "__init__.py": "e6a2cd2a4b36d0a21213b66d110e3fd37562efa8d5b36f41ac85db52d982c7a4",
  "__main__.py": "97194f8f36876c9aeb75cc510efe37232f308d92c8f82160e37d7ae11072d3a4",
  "api.py": "19b72e8096437ba9e0d8161f9b515ec2193a4f6bb8e25d7b835bc8376650eb06",
  "interface.json": "c45e54d270377719d4f81b5f934a11ce0af09ad2dd507e0f14ae453e814331ef",
  "pyproject.toml": "ad41b5014e61f09ea8ba291caac35a20e1e119de7a823fa0735e98b0e377ccd5",
  "setup.cfg": "0b76feba0424280a3c635eecf1eef5b2b54f3a70f7d1d7041dc01c647f5e365e",
  "tests/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "tests/test_client.py": "4b83c3591c24a13cabbe6ebe3fb23959bbbc16fd2190420ed0b3904b8001ce7d"
}
```
