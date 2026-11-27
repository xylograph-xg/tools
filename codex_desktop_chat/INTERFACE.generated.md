# codex_desktop_chat：自动接口快照

由全局更新生成；仅记录当前源码结构，不承诺业务语义或运行验收。默认参数值以源码/人工工具卡为准。列出的文件级函数也可能是内部实现，不自动成为公共 API。

权威目录：`../../paper/codex_desktop_chat`

## 相对已审查基线的变化

无源码变化。

## Python 声明

- `create_session(provider=…, **kwargs)` — [__init__.py:8](../../paper/codex_desktop_chat/__init__.py#L8)
- `ask_once(prompt, files=…, answer_timeout=…, *, model=…, thinking_high=…, state_dir=…, foreground=…, poll_interval=…, upload_timeout=…, bundle_dir=…)` — [__init__.py:13](../../paper/codex_desktop_chat/__init__.py#L13)
- `main()` — [__main__.py:10](../../paper/codex_desktop_chat/__main__.py#L10)
- `validate_files(files)` — [attachments.py:12](../../paper/codex_desktop_chat/attachments.py#L12)
- `snapshot_files(paths, folder)` — [attachments.py:33](../../paper/codex_desktop_chat/attachments.py#L33)
- `verify_snapshots(files)` — [attachments.py:53](../../paper/codex_desktop_chat/attachments.py#L53)
- `composer_nodes(snapshot)` — [attachments.py:70](../../paper/codex_desktop_chat/attachments.py#L70)
- `attachment_names(snapshot)` — [attachments.py:78](../../paper/codex_desktop_chat/attachments.py#L78)
- `upload_evidence(snapshot, expected)` — [attachments.py:88](../../paper/codex_desktop_chat/attachments.py#L88)
- `choose_file(backend, path, pid)` — [attachments.py:108](../../paper/codex_desktop_chat/attachments.py#L108)
- `image_file_names(files)` — [attachments.py:151](../../paper/codex_desktop_chat/attachments.py#L151)
- `formal_attachment_evidence(snapshot, wire, expected, image_names=…)` — [attachments.py:161](../../paper/codex_desktop_chat/attachments.py#L161)
- `channel_issue(snapshot)` — [attachments.py:189](../../paper/codex_desktop_chat/attachments.py#L189)
- `NativeBackend.__init__(self, bundle_id=…, *, helper_path=…)` — [backend.py:13](../../paper/codex_desktop_chat/backend.py#L13)
- `NativeBackend.call(self, op, *, timeout=…, **args)` — [backend.py:46](../../paper/codex_desktop_chat/backend.py#L46)
- `NativeBackend.snapshot(self)` — [backend.py:65](../../paper/codex_desktop_chat/backend.py#L65)
- `NativeBackend.press(self, query, **guards)` — [backend.py:68](../../paper/codex_desktop_chat/backend.py#L68)
- `NativeBackend.type_text(self, text, **guards)` — [backend.py:71](../../paper/codex_desktop_chat/backend.py#L71)
- `NativeBackend.escape(self)` — [backend.py:75](../../paper/codex_desktop_chat/backend.py#L75)
- `default_bundle_dir()` — [bundles.py:14](../../paper/codex_desktop_chat/bundles.py#L14)
- `verify_bundle(path)` — [bundles.py:32](../../paper/codex_desktop_chat/bundles.py#L32)
- `prepare_upload_bundle(files, *, bundle_dir=…)` — [bundles.py:73](../../paper/codex_desktop_chat/bundles.py#L73)
- `ChatGPTDesktop.__init__(self, new_chat=…, thinking_high=…, *, model=…, state_dir=…, foreground=…, window_id=…, poll_interval=…, max_windows=…, backend=…, bundle_dir=…)` — [core.py:116](../../paper/codex_desktop_chat/core.py#L116)
- `ChatGPTDesktop.start_new_chat(self)` — [core.py:246](../../paper/codex_desktop_chat/core.py#L246)
- `ChatGPTDesktop.verify_settings(self)` — [core.py:275](../../paper/codex_desktop_chat/core.py#L275)
- `ChatGPTDesktop.submit(self, prompt, files=…, *, upload_timeout=…)` — [core.py:283](../../paper/codex_desktop_chat/core.py#L283)
- `ChatGPTDesktop.collect(self, receipt, answer_timeout=…)` — [core.py:376](../../paper/codex_desktop_chat/core.py#L376)
- `ChatGPTDesktop.ask(self, prompt, files=…, answer_timeout=…, *, upload_timeout=…)` — [core.py:421](../../paper/codex_desktop_chat/core.py#L421)
- `ChatGPTDesktop.verify_attachment_channel(self)` — [core.py:437](../../paper/codex_desktop_chat/core.py#L437)
- `ChatGPTDesktop.status(self)` — [core.py:455](../../paper/codex_desktop_chat/core.py#L455)
- `DesktopChatError.__init__(self, code, message, *, receipt_id=…, may_have_sent=…)` — [errors.py:3](../../paper/codex_desktop_chat/errors.py#L3)
- `DesktopChatError.as_dict(self)` — [errors.py:7](../../paper/codex_desktop_chat/errors.py#L7)
- `main()` — [examples/ask_codex_chat.py:7](../../paper/codex_desktop_chat/examples/ask_codex_chat.py#L7)
- `atomic_json(path, payload)` — [state.py:37](../../paper/codex_desktop_chat/state.py#L37)
- `ReceiptStore.__init__(self, folder)` — [state.py:53](../../paper/codex_desktop_chat/state.py#L53)
- `ReceiptStore.path(self, receipt_id)` — [state.py:57](../../paper/codex_desktop_chat/state.py#L57)
- `ReceiptStore.save(self, receipt)` — [state.py:62](../../paper/codex_desktop_chat/state.py#L62)
- `ReceiptStore.load(self, receipt_id)` — [state.py:72](../../paper/codex_desktop_chat/state.py#L72)
- `ReceiptStore.pending(self)` — [state.py:81](../../paper/codex_desktop_chat/state.py#L81)
- `desktop_lock(timeout=…)` — [state.py:90](../../paper/codex_desktop_chat/state.py#L90)
- `TurnTests.test_later_turn_never_collected_for_original(self)` — [tests/test_audit_regressions.py:19](../../paper/codex_desktop_chat/tests/test_audit_regressions.py#L19)
- `TurnTests.test_ambiguous_assistant_turns_refused(self)` — [tests/test_audit_regressions.py:29](../../paper/codex_desktop_chat/tests/test_audit_regressions.py#L29)
- `TurnTests.test_historical_completion_does_not_complete_target(self)` — [tests/test_audit_regressions.py:33](../../paper/codex_desktop_chat/tests/test_audit_regressions.py#L33)
- `TurnTests.test_delayed_anchor_only_waits_and_collects(self)` — [tests/test_audit_regressions.py:42](../../paper/codex_desktop_chat/tests/test_audit_regressions.py#L42)
- `TurnTests.test_absent_anchor_times_out_without_resend(self)` — [tests/test_audit_regressions.py:48](../../paper/codex_desktop_chat/tests/test_audit_regressions.py#L48)
- `TurnTests.test_code_text_area_is_not_silently_dropped(self)` — [tests/test_audit_regressions.py:55](../../paper/codex_desktop_chat/tests/test_audit_regressions.py#L55)
- `TurnTests.test_start_and_settings_require_permission_before_mutation(self)` — [tests/test_audit_regressions.py:60](../../paper/codex_desktop_chat/tests/test_audit_regressions.py#L60)
- `TurnTests.test_terminal_receipt_cannot_return_to_submitting(self)` — [tests/test_audit_regressions.py:67](../../paper/codex_desktop_chat/tests/test_audit_regressions.py#L67)
- `ArchiveTests.setUp(self)` — [tests/test_audit_regressions.py:74](../../paper/codex_desktop_chat/tests/test_audit_regressions.py#L74)
- `ArchiveTests.pack(self)` — [tests/test_audit_regressions.py:78](../../paper/codex_desktop_chat/tests/test_audit_regressions.py#L78)
- `ArchiveTests.test_self_consistent_wrong_source_cache_is_rejected(self)` — [tests/test_audit_regressions.py:79](../../paper/codex_desktop_chat/tests/test_audit_regressions.py#L79)
- `ArchiveTests.test_wrong_prepacked_cache_is_rejected(self)` — [tests/test_audit_regressions.py:85](../../paper/codex_desktop_chat/tests/test_audit_regressions.py#L85)
- `ArchiveTests.test_symlink_zip_rejected(self)` — [tests/test_audit_regressions.py:91](../../paper/codex_desktop_chat/tests/test_audit_regressions.py#L91)
- `ArchiveTests.test_concurrent_publication_matches_source(self)` — [tests/test_audit_regressions.py:96](../../paper/codex_desktop_chat/tests/test_audit_regressions.py#L96)
- `FakeBackend.__init__(self, failure=…)` — [tests/test_codex_desktop_attachments.py:11](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L11)
- `FakeBackend.snapshot(self)` — [tests/test_codex_desktop_attachments.py:13](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L13)
- `FakeBackend.type_text(self, text, **kw)` — [tests/test_codex_desktop_attachments.py:27](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L27)
- `FakeBackend.press(self, query, **kw)` — [tests/test_codex_desktop_attachments.py:28](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L28)
- `FakeBackend.upload(self, path)` — [tests/test_codex_desktop_attachments.py:31](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L31)
- `AttachmentTests.setUp(self)` — [tests/test_codex_desktop_attachments.py:34](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L34)
- `AttachmentTests.composer(self, names=…, progress=…, error=…, enabled=…)` — [tests/test_codex_desktop_attachments.py:37](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L37)
- `AttachmentTests.test_absolute_existing_regular_unique_files(self)` — [tests/test_codex_desktop_attachments.py:40](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L40)
- `AttachmentTests.test_empty_and_oversized_rejected(self)` — [tests/test_codex_desktop_attachments.py:44](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L44)
- `AttachmentTests.test_frozen_snapshot_and_mutation_guard(self)` — [tests/test_codex_desktop_attachments.py:49](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L49)
- `AttachmentTests.test_ready_send_button_cannot_override_progress(self)` — [tests/test_codex_desktop_attachments.py:54](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L54)
- `AttachmentTests.test_foreign_missing_duplicate_disabled_not_ready(self)` — [tests/test_codex_desktop_attachments.py:57](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L57)
- `AttachmentTests.test_failed_upload_never_ready(self)` — [tests/test_codex_desktop_attachments.py:62](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L62)
- `AttachmentTests.test_sidebar_old_failures_do_not_block_composer(self)` — [tests/test_codex_desktop_attachments.py:65](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L65)
- `AttachmentTests.test_formal_receipt_does_not_use_composer_as_proof(self)` — [tests/test_codex_desktop_attachments.py:68](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L68)
- `AttachmentTests.session(self, b)` — [tests/test_codex_desktop_attachments.py:71](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L71)
- `AttachmentTests.test_complete_staged_upload_then_exact_guarded_send(self)` — [tests/test_codex_desktop_attachments.py:74](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L74)
- `AttachmentTests.test_failed_upload_archived_no_send_no_retry(self)` — [tests/test_codex_desktop_attachments.py:82](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L82)
- `AttachmentTests.test_two_files_have_separate_snapshots_and_exact_send_guard(self)` — [tests/test_codex_desktop_attachments.py:90](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L90)
- `AttachmentTests.test_anonymous_image_requires_bound_count_and_image_evidence(self)` — [tests/test_codex_desktop_attachments.py:99](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L99)
- `AttachmentTests.test_observed_quota_blocks_new_files_without_resending(self)` — [tests/test_codex_desktop_attachments.py:106](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L106)
- `AttachmentTests.test_native_quota_is_an_observation_not_a_reset_guarantee(self)` — [tests/test_codex_desktop_attachments.py:112](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L112)
- `AttachmentTests.test_corrupt_channel_state_blocks_attachments(self)` — [tests/test_codex_desktop_attachments.py:117](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L117)
- `AttachmentTests.test_existing_attachments_protected_before_typing(self)` — [tests/test_codex_desktop_attachments.py:122](../../paper/codex_desktop_chat/tests/test_codex_desktop_attachments.py#L122)
- `BundleTests.setUp(self)` — [tests/test_codex_desktop_bundles.py:7](../../paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py#L7)
- `BundleTests.pack(self, files)` — [tests/test_codex_desktop_bundles.py:10](../../paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py#L10)
- `BundleTests.test_exact_content_manifest_and_content_address_reuse(self)` — [tests/test_codex_desktop_bundles.py:11](../../paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py#L11)
- `BundleTests.test_changed_content_gets_new_bundle(self)` — [tests/test_codex_desktop_bundles.py:16](../../paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py#L16)
- `BundleTests.test_existing_zip_is_staged_without_nesting(self)` — [tests/test_codex_desktop_bundles.py:18](../../paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py#L18)
- `BundleTests.test_corrupt_existing_package_rejected(self)` — [tests/test_codex_desktop_bundles.py:22](../../paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py#L22)
- `BundleTests.test_unsafe_zip_and_reserved_manifest_rejected(self)` — [tests/test_codex_desktop_bundles.py:25](../../paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py#L25)
- `BundleTests.test_no_app_needed_and_temp_files_cleaned(self)` — [tests/test_codex_desktop_bundles.py:31](../../paper/codex_desktop_chat/tests/test_codex_desktop_bundles.py#L31)
- `node(i, role, value=…, title=…, parent=…, **kw)` — [tests/test_codex_desktop_chat.py:10](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L10)
- `answer_tree(prompt=…, answer=…, complete=…, busy=…)` — [tests/test_codex_desktop_chat.py:14](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L14)
- `ReadBackend.__init__(self, snapshot)` — [tests/test_codex_desktop_chat.py:24](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L24)
- `ReadBackend.snapshot(self)` — [tests/test_codex_desktop_chat.py:25](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L25)
- `ReadBackend.press(self, *a, **kw)` — [tests/test_codex_desktop_chat.py:26](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L26)
- `SafetyTests.setUp(self)` — [tests/test_codex_desktop_chat.py:29](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L29)
- `SafetyTests.session(self, tree, stage=…)` — [tests/test_codex_desktop_chat.py:33](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L33)
- `SafetyTests.test_exact_unique_prompt_required(self)` — [tests/test_codex_desktop_chat.py:41](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L41)
- `SafetyTests.test_long_full_answer_not_truncated(self)` — [tests/test_codex_desktop_chat.py:46](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L46)
- `SafetyTests.test_inline_fragment_order_is_preserved(self)` — [tests/test_codex_desktop_chat.py:50](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L50)
- `SafetyTests.test_completion_cannot_be_inferred_from_disabled_stop(self)` — [tests/test_codex_desktop_chat.py:54](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L54)
- `SafetyTests.test_completed_result_archived_before_return(self)` — [tests/test_codex_desktop_chat.py:58](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L58)
- `SafetyTests.test_unknown_receipt_can_only_collect(self)` — [tests/test_codex_desktop_chat.py:67](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L67)
- `SafetyTests.test_timeout_preserves_pending_and_never_returns_partial(self)` — [tests/test_codex_desktop_chat.py:73](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L73)
- `SafetyTests.test_other_window_or_changed_input_receipt_rejected(self)` — [tests/test_codex_desktop_chat.py:80](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L80)
- `SafetyTests.test_existing_draft_not_overwritten(self)` — [tests/test_codex_desktop_chat.py:86](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L86)
- `SafetyTests.test_history_named_new_chat_not_navigation(self)` — [tests/test_codex_desktop_chat.py:92](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L92)
- `SafetyTests.test_invalid_attachments_rejected_before_ui(self)` — [tests/test_codex_desktop_chat.py:96](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L96)
- `SafetyTests.test_pending_request_cannot_submit_again(self)` — [tests/test_codex_desktop_chat.py:101](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L101)
- `SafetyTests.test_corrupted_receipts_block(self)` — [tests/test_codex_desktop_chat.py:106](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L106)
- `SafetyTests.test_saved_answer_hash_is_checked(self)` — [tests/test_codex_desktop_chat.py:110](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L110)
- `SafetyTests.test_multiple_receipts_have_separate_window_ids(self)` — [tests/test_codex_desktop_chat.py:114](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L114)
- `SafetyTests.test_foreground_authorization_and_provider_are_explicit(self)` — [tests/test_codex_desktop_chat.py:120](../../paper/codex_desktop_chat/tests/test_codex_desktop_chat.py#L120)

## 文件 SHA-256

```json
{
  "AUDIT_RUNS/20261023-134830-a2a94b/AUDIT.md": "cf3aba09a722f474e55988691eac60f1c2186c29f325911b48fe9edcc3120b0a",
  "AUDIT_RUNS/20261023-140721-ff0c07/AUDIT.md": "7a7fa031988beb0fb1d562679598fe11670121b62a238ceb7a33849e6a1e1f0d",
  "README.md": "70deaa93db0f593f65cc812b167b4d135dbcd2dbe96acf3b19f1db23c5acde6e",
  "__init__.py": "1b6b732b80c86a954ad29dd5bb7a4218cec3b72952b434fd2b51a58e2318dd23",
  "__main__.py": "b5d18132b48c05fc490bc6b1500999b9f1b3978f2107b97c4600e4d522595647",
  "api.py": "f45a4174ca17d8fe5c178d5e21c2b5e84f28974e5934b012b68cbf613ff19e1d",
  "attachments.py": "2aa166be16069a11f8e5006828f0975b38ec3f213511cf42de72be1282e59f47",
  "backend.py": "f8b49e67e6cb070c5456d595de284c72d15fe09efa678e927390f7d7a683244d",
  "bundles.py": "c6d2e1a6fb03520f13ec1525c6a295824195bd7a637a1e14f56df06ce59f9d31",
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
  "调用说明.md": "ed03c215d4ff602ac0b2c7b683f45ebb815319adc293b2db9ee8fb8c0ecc7596"
}
```
