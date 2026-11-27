# codex_web_client：自动接口快照

由全局更新生成；仅记录当前源码结构，不承诺业务语义或运行验收。默认参数值以源码/人工工具卡为准。列出的文件级函数也可能是内部实现，不自动成为公共 API。

权威目录：`/Users/xiaoyanhao/project/paper/codex_web_client`

## 相对已审查基线的变化

无源码变化。

## Python 声明

- `main()` — [__main__.py:10](/Users/xiaoyanhao/project/paper/codex_web_client/__main__.py:10)
- `Client.__init__(self, state_dir=…, *, port=…, timeout=…)` — [api.py:126](/Users/xiaoyanhao/project/paper/codex_web_client/api.py:126)
- `Client.health(self)` — [api.py:160](/Users/xiaoyanhao/project/paper/codex_web_client/api.py:160)
- `Client.submit(self, key, prompt, *, workdir=…, require_command=…, expected=…, json_match=…, images=…, guarded=…)` — [api.py:178](/Users/xiaoyanhao/project/paper/codex_web_client/api.py:178)
- `Client.get(self, key)` — [api.py:219](/Users/xiaoyanhao/project/paper/codex_web_client/api.py:219)
- `Client.counts(self)` — [api.py:232](/Users/xiaoyanhao/project/paper/codex_web_client/api.py:232)
- `Client.dispatch_status(self)` — [api.py:236](/Users/xiaoyanhao/project/paper/codex_web_client/api.py:236)
- `Client.run_once(self, *, before_send=…, key=…, pro_first=…, parallel_slot=…)` — [api.py:265](/Users/xiaoyanhao/project/paper/codex_web_client/api.py:265)
- `ClientTests.setUp(self)` — [tests/test_client.py:13](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:13)
- `ClientTests.evidence(self, text, *, command=…, message=…, completed=…, exited=…)` — [tests/test_client.py:18](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:18)
- `ClientTests.test_finished_without_command(self)` — [tests/test_client.py:35](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:35)
- `ClientTests.test_incomplete(self)` — [tests/test_client.py:40](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:40)
- `ClientTests.test_mixed_answer(self)` — [tests/test_client.py:44](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:44)
- `ClientTests.test_unknown_exit(self)` — [tests/test_client.py:48](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:48)
- `ClientTests.test_recover_and_reuse(self)` — [tests/test_client.py:52](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:52)
- `ClientTests.test_json_accept(self)` — [tests/test_client.py:61](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:61)
- `ClientTests.test_json_reject_wrong_type_or_duplicate(self)` — [tests/test_client.py:65](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:65)
- `ClientTests.test_lock_and_offline(self)` — [tests/test_client.py:71](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:71)
- `ClientTests.test_concurrent_submission(self)` — [tests/test_client.py:81](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:81)
- `ClientTests.fake_cli(self, body)` — [tests/test_client.py:87](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:87)
- `ClientTests.test_timeout_is_not_replayed(self)` — [tests/test_client.py:93](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:93)
- `ClientTests.test_exited_zero_without_events(self)` — [tests/test_client.py:102](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:102)
- `ClientTests.test_backoff_persists_across_workers_and_clears_on_success(self)` — [tests/test_client.py:110](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:110)
- `ClientTests.test_guarded_images_frozen_select_exact_job(self)` — [tests/test_client.py:121](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:121)
- `ClientTests.test_pro_then_extra_high_then_high_with_persistent_quota_evidence(self)` — [tests/test_client.py:135](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:135)
- `ClientTests.test_general_limit_and_uncertain_submission_never_retry_job(self)` — [tests/test_client.py:154](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:154)
- `ClientTests.test_app_upload_quota_blocks_next_dispatch_across_models_and_restart(self)` — [tests/test_client.py:164](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:164)
- `ClientTests.test_five_parallel_keys_keep_exclusive_job_and_slot_locks(self)` — [tests/test_client.py:178](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:178)
- `ClientTests.test_parallel_success_keeps_another_jobs_quota_cooldown(self)` — [tests/test_client.py:207](/Users/xiaoyanhao/project/paper/codex_web_client/tests/test_client.py:207)

## 文件 SHA-256

```json
{
  "README.md": "b8c87ea32979d44b86e96312fcd8ede05d20e5c0b3012bdffb42d277f93f473f",
  "__init__.py": "e6a2cd2a4b36d0a21213b66d110e3fd37562efa8d5b36f41ac85db52d982c7a4",
  "__main__.py": "97194f8f36876c9aeb75cc510efe37232f308d92c8f82160e37d7ae11072d3a4",
  "api.py": "291cb616ed91cfa63aa6e41168394ec5722b567e853419f5f487949efbd74455",
  "interface.json": "42071a79ea2052caa473f09b6e3d15d1a4dca001419418c3fe293299be2e92ae",
  "pyproject.toml": "ad41b5014e61f09ea8ba291caac35a20e1e119de7a823fa0735e98b0e377ccd5",
  "setup.cfg": "9e167da843f3f44fe54e93b50e0f69e22c785b72884bf2a8129379b449c258e3",
  "tests/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "tests/test_client.py": "81841c488eac6f3b5da9730d8c6cea0edeb063971d1d590d24e8d5c078756d9a"
}
```
