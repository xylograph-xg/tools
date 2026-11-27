# codex_desktop_chat：自动接口快照

由全局更新生成；仅记录当前源码结构，不承诺业务语义或运行验收。默认参数值以源码/人工工具卡为准。列出的文件级函数也可能是内部实现，不自动成为公共 API。

权威目录：`/Users/xiaoyanhao/project/paper/codex_desktop_chat`

## 相对已审查基线的变化

无源码变化。

## Python 声明

- `create_session(provider=…, **kwargs)` — [__init__.py:8](/Users/xiaoyanhao/project/paper/codex_desktop_chat/__init__.py:8)
- `ask_once(prompt, files=…, answer_timeout=…, *, model=…, thinking_high=…, state_dir=…, foreground=…, poll_interval=…, upload_timeout=…, bundle_dir=…)` — [__init__.py:13](/Users/xiaoyanhao/project/paper/codex_desktop_chat/__init__.py:13)
- `main()` — [__main__.py:10](/Users/xiaoyanhao/project/paper/codex_desktop_chat/__main__.py:10)
- `validate_files(files)` — [attachments.py:12](/Users/xiaoyanhao/project/paper/codex_desktop_chat/attachments.py:12)
- `snapshot_files(paths, folder)` — [attachments.py:33](/Users/xiaoyanhao/project/paper/codex_desktop_chat/attachments.py:33)
- `verify_snapshots(files)` — [attachments.py:53](/Users/xiaoyanhao/project/paper/codex_desktop_chat/attachments.py:53)
- `composer_nodes(snapshot)` — [attachments.py:70](/Users/xiaoyanhao/project/paper/codex_desktop_chat/attachments.py:70)
- `attachment_names(snapshot)` — [attachments.py:78](/Users/xiaoyanhao/project/paper/codex_desktop_chat/attachments.py:78)
- `upload_evidence(snapshot, expected)` — [attachments.py:88](/Users/xiaoyanhao/project/paper/codex_desktop_chat/attachments.py:88)
- `choose_file(backend, path, pid)` — [attachments.py:108](/Users/xiaoyanhao/project/paper/codex_desktop_chat/attachments.py:108)
- `image_file_names(files)` — [attachments.py:151](/Users/xiaoyanhao/project/paper/codex_desktop_chat/attachments.py:151)
- `formal_attachment_evidence(snapshot, wire, expected, image_names=…)` — [attachments.py:161](/Users/xiaoyanhao/project/paper/codex_desktop_chat/attachments.py:161)
- `channel_issue(snapshot)` — [attachments.py:189](/Users/xiaoyanhao/project/paper/codex_desktop_chat/attachments.py:189)
- `NativeBackend.__init__(self, bundle_id=…, *, helper_path=…)` — [backend.py:13](/Users/xiaoyanhao/project/paper/codex_desktop_chat/backend.py:13)
- `NativeBackend.call(self, op, *, timeout=…, **args)` — [backend.py:46](/Users/xiaoyanhao/project/paper/codex_desktop_chat/backend.py:46)
- `NativeBackend.snapshot(self)` — [backend.py:65](/Users/xiaoyanhao/project/paper/codex_desktop_chat/backend.py:65)
- `NativeBackend.press(self, query, **guards)` — [backend.py:68](/Users/xiaoyanhao/project/paper/codex_desktop_chat/backend.py:68)
- `NativeBackend.type_text(self, text, **guards)` — [backend.py:71](/Users/xiaoyanhao/project/paper/codex_desktop_chat/backend.py:71)
- `NativeBackend.escape(self)` — [backend.py:75](/Users/xiaoyanhao/project/paper/codex_desktop_chat/backend.py:75)
- `default_bundle_dir()` — [bundles.py:14](/Users/xiaoyanhao/project/paper/codex_desktop_chat/bundles.py:14)
- `verify_bundle(path)` — [bundles.py:32](/Users/xiaoyanhao/project/paper/codex_desktop_chat/bundles.py:32)
- `prepare_upload_bundle(files, *, bundle_dir=…)` — [bundles.py:73](/Users/xiaoyanhao/project/paper/codex_desktop_chat/bundles.py:73)
- `ChatGPTDesktop.__init__(self, new_chat=…, thinking_high=…, *, model=…, state_dir=…, foreground=…, window_id=…, poll_interval=…, max_windows=…, backend=…, bundle_dir=…)` — [core.py:116](/Users/xiaoyanhao/project/paper/codex_desktop_chat/core.py:116)
- `ChatGPTDesktop.start_new_chat(self)` — [core.py:246](/Users/xiaoyanhao/project/paper/codex_desktop_chat/core.py:246)
- `ChatGPTDesktop.verify_settings(self)` — [core.py:275](/Users/xiaoyanhao/project/paper/codex_desktop_chat/core.py:275)
- `ChatGPTDesktop.submit(self, prompt, files=…, *, upload_timeout=…)` — [core.py:283](/Users/xiaoyanhao/project/paper/codex_desktop_chat/core.py:283)
- `ChatGPTDesktop.collect(self, receipt, answer_timeout=…)` — [core.py:376](/Users/xiaoyanhao/project/paper/codex_desktop_chat/core.py:376)
- `ChatGPTDesktop.ask(self, prompt, files=…, answer_timeout=…, *, upload_timeout=…)` — [core.py:421](/Users/xiaoyanhao/project/paper/codex_desktop_chat/core.py:421)
- `ChatGPTDesktop.verify_attachment_channel(self)` — [core.py:437](/Users/xiaoyanhao/project/paper/codex_desktop_chat/core.py:437)
- `ChatGPTDesktop.status(self)` — [core.py:455](/Users/xiaoyanhao/project/paper/codex_desktop_chat/core.py:455)
- `DesktopChatError.__init__(self, code, message, *, receipt_id=…, may_have_sent=…)` — [errors.py:3](/Users/xiaoyanhao/project/paper/codex_desktop_chat/errors.py:3)
- `DesktopChatError.as_dict(self)` — [errors.py:7](/Users/xiaoyanhao/project/paper/codex_desktop_chat/errors.py:7)
- `main()` — [examples/ask_codex_chat.py:7](/Users/xiaoyanhao/project/paper/codex_desktop_chat/examples/ask_codex_chat.py:7)
- `atomic_json(path, payload)` — [state.py:37](/Users/xiaoyanhao/project/paper/codex_desktop_chat/state.py:37)
- `ReceiptStore.__init__(self, folder)` — [state.py:53](/Users/xiaoyanhao/project/paper/codex_desktop_chat/state.py:53)
- `ReceiptStore.path(self, receipt_id)` — [state.py:57](/Users/xiaoyanhao/project/paper/codex_desktop_chat/state.py:57)
- `ReceiptStore.save(self, receipt)` — [state.py:62](/Users/xiaoyanhao/project/paper/codex_desktop_chat/state.py:62)
- `ReceiptStore.load(self, receipt_id)` — [state.py:72](/Users/xiaoyanhao/project/paper/codex_desktop_chat/state.py:72)
- `ReceiptStore.pending(self)` — [state.py:81](/Users/xiaoyanhao/project/paper/codex_desktop_chat/state.py:81)
- `desktop_lock(timeout=…)` — [state.py:90](/Users/xiaoyanhao/project/paper/codex_desktop_chat/state.py:90)
- `TurnTests.test_later_turn_never_collected_for_original(self)` — [tests/test_audit_regressions.py:19](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_audit_regressions.py:19)
- `TurnTests.test_ambiguous_assistant_turns_refused(self)` — [tests/test_audit_regressions.py:29](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_audit_regressions.py:29)
- `TurnTests.test_historical_completion_does_not_complete_target(self)` — [tests/test_audit_regressions.py:33](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_audit_regressions.py:33)
- `TurnTests.test_delayed_anchor_only_waits_and_collects(self)` — [tests/test_audit_regressions.py:42](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_audit_regressions.py:42)
- `TurnTests.test_absent_anchor_times_out_without_resend(self)` — [tests/test_audit_regressions.py:48](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_audit_regressions.py:48)
- `TurnTests.test_code_text_area_is_not_silently_dropped(self)` — [tests/test_audit_regressions.py:55](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_audit_regressions.py:55)
- `TurnTests.test_start_and_settings_require_permission_before_mutation(self)` — [tests/test_audit_regressions.py:60](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_audit_regressions.py:60)
- `TurnTests.test_terminal_receipt_cannot_return_to_submitting(self)` — [tests/test_audit_regressions.py:67](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_audit_regressions.py:67)
- `ArchiveTests.setUp(self)` — [tests/test_audit_regressions.py:74](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_audit_regressions.py:74)
- `ArchiveTests.pack(self)` — [tests/test_audit_regressions.py:78](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_audit_regressions.py:78)
- `ArchiveTests.test_self_consistent_wrong_source_cache_is_rejected(self)` — [tests/test_audit_regressions.py:79](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_audit_regressions.py:79)
- `ArchiveTests.test_wrong_prepacked_cache_is_rejected(self)` — [tests/test_audit_regressions.py:85](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_audit_regressions.py:85)
- `ArchiveTests.test_symlink_zip_rejected(self)` — [tests/test_audit_regressions.py:91](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_audit_regressions.py:91)
- `ArchiveTests.test_concurrent_publication_matches_source(self)` — [tests/test_audit_regressions.py:96](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_audit_regressions.py:96)
- `FakeBackend.__init__(self, failure=…)` — [tests/test_codex_desktop_attachments.py:11](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:11)
- `FakeBackend.snapshot(self)` — [tests/test_codex_desktop_attachments.py:13](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:13)
- `FakeBackend.type_text(self, text, **kw)` — [tests/test_codex_desktop_attachments.py:27](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:27)
- `FakeBackend.press(self, query, **kw)` — [tests/test_codex_desktop_attachments.py:28](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:28)
- `FakeBackend.upload(self, path)` — [tests/test_codex_desktop_attachments.py:31](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:31)
- `AttachmentTests.setUp(self)` — [tests/test_codex_desktop_attachments.py:34](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:34)
- `AttachmentTests.composer(self, names=…, progress=…, error=…, enabled=…)` — [tests/test_codex_desktop_attachments.py:37](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:37)
- `AttachmentTests.test_absolute_existing_regular_unique_files(self)` — [tests/test_codex_desktop_attachments.py:40](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:40)
- `AttachmentTests.test_empty_and_oversized_rejected(self)` — [tests/test_codex_desktop_attachments.py:44](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:44)
- `AttachmentTests.test_frozen_snapshot_and_mutation_guard(self)` — [tests/test_codex_desktop_attachments.py:49](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:49)
- `AttachmentTests.test_ready_send_button_cannot_override_progress(self)` — [tests/test_codex_desktop_attachments.py:54](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:54)
- `AttachmentTests.test_foreign_missing_duplicate_disabled_not_ready(self)` — [tests/test_codex_desktop_attachments.py:57](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:57)
- `AttachmentTests.test_failed_upload_never_ready(self)` — [tests/test_codex_desktop_attachments.py:62](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:62)
- `AttachmentTests.test_sidebar_old_failures_do_not_block_composer(self)` — [tests/test_codex_desktop_attachments.py:65](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:65)
- `AttachmentTests.test_formal_receipt_does_not_use_composer_as_proof(self)` — [tests/test_codex_desktop_attachments.py:68](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:68)
- `AttachmentTests.session(self, b)` — [tests/test_codex_desktop_attachments.py:71](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:71)
- `AttachmentTests.test_complete_staged_upload_then_exact_guarded_send(self)` — [tests/test_codex_desktop_attachments.py:74](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:74)
- `AttachmentTests.test_failed_upload_archived_no_send_no_retry(self)` — [tests/test_codex_desktop_attachments.py:82](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:82)
- `AttachmentTests.test_two_files_have_separate_snapshots_and_exact_send_guard(self)` — [tests/test_codex_desktop_attachments.py:90](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:90)
- `AttachmentTests.test_anonymous_image_requires_bound_count_and_image_evidence(self)` — [tests/test_codex_desktop_attachments.py:99](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:99)
- `AttachmentTests.test_observed_quota_blocks_new_files_without_resending(self)` — [tests/test_codex_desktop_attachments.py:106](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:106)
- `AttachmentTests.test_native_quota_is_an_observation_not_a_reset_guarantee(self)` — [tests/test_codex_desktop_attachments.py:112](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:112)
- `AttachmentTests.test_corrupt_channel_state_blocks_attachments(self)` — [tests/test_codex_desktop_attachments.py:117](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:117)
- `AttachmentTests.test_existing_attachments_protected_before_typing(self)` — [tests/test_codex_desktop_attachments.py:122](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py:122)
- `BundleTests.setUp(self)` — [tests/test_codex_desktop_bundles.py:7](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py:7)
- `BundleTests.pack(self, files)` — [tests/test_codex_desktop_bundles.py:10](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py:10)
- `BundleTests.test_exact_content_manifest_and_content_address_reuse(self)` — [tests/test_codex_desktop_bundles.py:11](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py:11)
- `BundleTests.test_changed_content_gets_new_bundle(self)` — [tests/test_codex_desktop_bundles.py:16](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py:16)
- `BundleTests.test_existing_zip_is_staged_without_nesting(self)` — [tests/test_codex_desktop_bundles.py:18](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py:18)
- `BundleTests.test_corrupt_existing_package_rejected(self)` — [tests/test_codex_desktop_bundles.py:22](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py:22)
- `BundleTests.test_unsafe_zip_and_reserved_manifest_rejected(self)` — [tests/test_codex_desktop_bundles.py:25](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py:25)
- `BundleTests.test_no_app_needed_and_temp_files_cleaned(self)` — [tests/test_codex_desktop_bundles.py:31](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py:31)
- `node(i, role, value=…, title=…, parent=…, **kw)` — [tests/test_codex_desktop_chat.py:10](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:10)
- `answer_tree(prompt=…, answer=…, complete=…, busy=…)` — [tests/test_codex_desktop_chat.py:14](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:14)
- `ReadBackend.__init__(self, snapshot)` — [tests/test_codex_desktop_chat.py:24](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:24)
- `ReadBackend.snapshot(self)` — [tests/test_codex_desktop_chat.py:25](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:25)
- `ReadBackend.press(self, *a, **kw)` — [tests/test_codex_desktop_chat.py:26](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:26)
- `SafetyTests.setUp(self)` — [tests/test_codex_desktop_chat.py:29](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:29)
- `SafetyTests.session(self, tree, stage=…)` — [tests/test_codex_desktop_chat.py:33](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:33)
- `SafetyTests.test_exact_unique_prompt_required(self)` — [tests/test_codex_desktop_chat.py:41](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:41)
- `SafetyTests.test_long_full_answer_not_truncated(self)` — [tests/test_codex_desktop_chat.py:46](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:46)
- `SafetyTests.test_inline_fragment_order_is_preserved(self)` — [tests/test_codex_desktop_chat.py:50](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:50)
- `SafetyTests.test_completion_cannot_be_inferred_from_disabled_stop(self)` — [tests/test_codex_desktop_chat.py:54](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:54)
- `SafetyTests.test_completed_result_archived_before_return(self)` — [tests/test_codex_desktop_chat.py:58](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:58)
- `SafetyTests.test_unknown_receipt_can_only_collect(self)` — [tests/test_codex_desktop_chat.py:67](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:67)
- `SafetyTests.test_timeout_preserves_pending_and_never_returns_partial(self)` — [tests/test_codex_desktop_chat.py:73](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:73)
- `SafetyTests.test_other_window_or_changed_input_receipt_rejected(self)` — [tests/test_codex_desktop_chat.py:80](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:80)
- `SafetyTests.test_existing_draft_not_overwritten(self)` — [tests/test_codex_desktop_chat.py:86](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:86)
- `SafetyTests.test_history_named_new_chat_not_navigation(self)` — [tests/test_codex_desktop_chat.py:92](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:92)
- `SafetyTests.test_invalid_attachments_rejected_before_ui(self)` — [tests/test_codex_desktop_chat.py:96](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:96)
- `SafetyTests.test_pending_request_cannot_submit_again(self)` — [tests/test_codex_desktop_chat.py:101](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:101)
- `SafetyTests.test_corrupted_receipts_block(self)` — [tests/test_codex_desktop_chat.py:106](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:106)
- `SafetyTests.test_saved_answer_hash_is_checked(self)` — [tests/test_codex_desktop_chat.py:110](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:110)
- `SafetyTests.test_multiple_receipts_have_separate_window_ids(self)` — [tests/test_codex_desktop_chat.py:114](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:114)
- `SafetyTests.test_foreground_authorization_and_provider_are_explicit(self)` — [tests/test_codex_desktop_chat.py:120](/Users/xiaoyanhao/project/paper/codex_desktop_chat/tests/test_codex_desktop_chat.py:120)

## 文件 SHA-256

```json
{
  "AUDIT_RUNS/20261023-134830-a2a94b/AUDIT.md": "cf3aba09a722f474e55988691eac60f1c2186c29f325911b48fe9edcc3120b0a",
  "AUDIT_RUNS/20261023-140721-ff0c07/AUDIT.md": "7a7fa031988beb0fb1d562679598fe11670121b62a238ceb7a33849e6a1e1f0d",
  "README.md": "bc7b23637715f21e5928350442dc3afff1ec61e94f4ea75a71941194452f21c5",
  "__init__.py": "1b6b732b80c86a954ad29dd5bb7a4218cec3b72952b434fd2b51a58e2318dd23",
  "__main__.py": "b5d18132b48c05fc490bc6b1500999b9f1b3978f2107b97c4600e4d522595647",
  "api.py": "f45a4174ca17d8fe5c178d5e21c2b5e84f28974e5934b012b68cbf613ff19e1d",
  "attachments.py": "2aa166be16069a11f8e5006828f0975b38ec3f213511cf42de72be1282e59f47",
  "backend.py": "f8b49e67e6cb070c5456d595de284c72d15fe09efa678e927390f7d7a683244d",
  "bundles.py": "c48ee08c16f410f7839d570244f246bcde410d3e8369d4b23e4fabf176ebc962",
  "core.py": "a88e0bfaee157ce4f9d54a5e1ee170ff397217506f4351b8b62ce9892ec5dac4",
  "errors.py": "8aeb8fc64fe42e70892b946a983c745d79857767f433601e9aca7450f41feef8",
  "examples/ask_codex_chat.py": "771dc79f6b33ec7da4a3093a9cb0a42f80db3b097fee85ad3e633a57d13f5d86",
  "input.schema.json": "368cb8c5cf8487179c85b3089ae914ada01a2f995cb86860908b973cd317bd0c",
  "interface.json": "71c54ea2c26d55c40ddbe17b38e91e29bc16cf80465dbaf49b4502c40f002639",
  "native.swift": "cd15cf5b067f929fef0ef0ff7c75fa3bac2b9e36c932acb6aedb7a0645b09538",
  "pyproject.toml": "cb7091ae2e4af2ec8e90564498bf8cf69818d987f942cd6a2daaeba23f057aa4",
  "state.py": "8bcd18e406af8b17cc7c361f533baea562aee6df695752d6c2633fd6ed328c71",
  "tests/__init__.py": "fb944c320ac7e19a5eb780d82676bedee218e48ac298310954e9bec70b38081e",
  "tests/test_audit_regressions.py": "61fc5e56266a1933116c09d50dc104c64ca53d0b5cc466943a64419efaa89e38",
  "tests/test_codex_desktop_attachments.py": "3cace24e20399dae866c641b6ef05d58e91cb2cbdcc6356ae17fac11ee0da773",
  "tests/test_codex_desktop_bundles.py": "da614705c145f8335c86757e113f27b3cddc43f7bc72cca5f1c9a8e8620378e8",
  "tests/test_codex_desktop_chat.py": "0fbaccc58d0d13bfa67ba047e1bad6c73efce05905e4abfdf3e9e758a7c1a0d9",
  "调用说明.md": "5c2e0940ececa10bfb662dbaf3bfd289679d45cf60ba12a4002da1ed82f15e2f"
}
```
