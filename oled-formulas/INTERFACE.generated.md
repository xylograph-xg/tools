# oled_formulas：自动接口快照

由全局更新生成；仅记录当前源码结构，不承诺业务语义或运行验收。默认参数值以源码/人工工具卡为准。列出的文件级函数也可能是内部实现，不自动成为公共 API。

权威目录：`oled_formulas`

## 相对已审查基线的变化

无源码变化。

## Python 声明

- `main()` — [__main__.py:9](oled_formulas/__main__.py#L9)
- `archived_unsent(db, output, batch, control, traces)` — [app_queue.py:27](oled_formulas/app_queue.py#L27)
- `admit(db, output, *, control=…, traces=…)` — [app_queue.py:55](oled_formulas/app_queue.py#L55)
- `material(config, root, folder, batch, db, *, answer_format=…)` — [app_queue.py:73](oled_formulas/app_queue.py#L73)
- `AccountCheck.__init__(self)` — [app_queue.py:113](oled_formulas/app_queue.py#L113)
- `AccountCheck.invalidate(self)` — [app_queue.py:119](oled_formulas/app_queue.py#L119)
- `AccountCheck.verify(self, client)` — [app_queue.py:123](oled_formulas/app_queue.py#L123)
- `AccountCheck.completed(self, token, receipt)` — [app_queue.py:154](oled_formulas/app_queue.py#L154)
- `gate()` — [app_queue.py:164](oled_formulas/app_queue.py#L164)
- `sources_ok(config, root, rows)` — [app_queue.py:192](oled_formulas/app_queue.py#L192)
- `set_state(db, batch, state, reason=…)` — [app_queue.py:200](oled_formulas/app_queue.py#L200)
- `prepare_job(client, db, config, root, folder, batch)` — [app_queue.py:205](oled_formulas/app_queue.py#L205)
- `dispatch_job(client, config, root, output, batch, active, slot, guard)` — [app_queue.py:219](oled_formulas/app_queue.py#L219)
- `collect_job(db, control, root, output, batch, receipt)` — [app_queue.py:253](oled_formulas/app_queue.py#L253)
- `run(config, control, db, output, active)` — [app_queue.py:278](oled_formulas/app_queue.py#L278)
- `failure(folder, batch)` — [attachment_gate.py:10](oled_formulas/attachment_gate.py#L10)
- `record_failure(state, event)` — [attachment_gate.py:22](oled_formulas/attachment_gate.py#L22)
- `load_gate(output, db)` — [attachment_gate.py:32](oled_formulas/attachment_gate.py#L32)
- `trial_success(receipt, trial)` — [attachment_gate.py:56](oled_formulas/attachment_gate.py#L56)
- `held_intent(db, receipt, trial)` — [attachment_gate.py:64](oled_formulas/attachment_gate.py#L64)
- `probe_menu(page, guard)` — [attachment_gate.py:72](oled_formulas/attachment_gate.py#L72)
- `plan(db, root, seeds)` — [display_equations.py:32](oled_formulas/display_equations.py#L32)
- `evidence(page)` — [display_equations.py:49](oled_formulas/display_equations.py#L49)
- `build_packet(db, config, root, folder, batch)` — [display_equations.py:69](oled_formulas/display_equations.py#L69)
- `prose(text)` — [display_equations.py:131](oled_formulas/display_equations.py#L131)
- `mark_page_conflicts(records)` — [display_equations.py:138](oled_formulas/display_equations.py#L138)
- `locate(item, lines)` — [display_equations.py:149](oled_formulas/display_equations.py#L149)
- `transcription_check(item, lines)` — [display_equations.py:226](oled_formulas/display_equations.py#L226)
- `include_edge_symbols(image, box)` — [display_equations.py:249](oled_formulas/display_equations.py#L249)
- `crop_results(folder, manifest, records)` — [display_equations.py:273](oled_formulas/display_equations.py#L273)
- `release_path(folder)` — [entry_retry.py:11](oled_formulas/entry_retry.py#L11)
- `EntryTraces.__init__(self, path)` — [entry_retry.py:20](oled_formulas/entry_retry.py#L20)
- `EntryTraces.refresh(self)` — [entry_retry.py:26](oled_formulas/entry_retry.py#L26)
- `EntryTraces.verified(self, attempt, status)` — [entry_retry.py:48](oled_formulas/entry_retry.py#L48)
- `resume_one(db, output, control, gate, active, now, traces)` — [entry_retry.py:65](oled_formulas/entry_retry.py#L65)
- `recover_preflight(db, output, traces, active)` — [entry_retry.py:144](oled_formulas/entry_retry.py#L144)
- `observe(config, browser, output)` — [formula_dispatch.py:23](oled_formulas/formula_dispatch.py#L23)
- `available(checks, pool, reserved, cooldown, now)` — [formula_dispatch.py:85](oled_formulas/formula_dispatch.py#L85)
- `idle_effort_candidate(check, entry, *, held=…)` — [formula_dispatch.py:105](oled_formulas/formula_dispatch.py#L105)
- `held_before_send(db, output, entry, tid)` — [formula_dispatch.py:116](oled_formulas/formula_dispatch.py#L116)
- `empty_formula_home(check)` — [formula_dispatch.py:134](oled_formulas/formula_dispatch.py#L134)
- `historical_slot_receipt(control, output, batch, state, tid, receipt, original_release=…)` — [formula_dispatch.py:142](oled_formulas/formula_dispatch.py#L142)
- `release_unsent_slots(config, control, db, browser, pw, checks, pool, output, active)` — [formula_dispatch.py:176](oled_formulas/formula_dispatch.py#L176)
- `prepare_idle_effort(config, control, db, browser, checks, pool, reserved, retry_after, output, active)` — [formula_dispatch.py:242](oled_formulas/formula_dispatch.py#L242)
- `resume_visible_answers(db, output, checks)` — [formula_dispatch.py:298](oled_formulas/formula_dispatch.py#L298)
- `index_paper_order(db)` — [formula_dispatch.py:312](oled_formulas/formula_dispatch.py#L312)
- `dispatch(config, control, db, output, pw, browser, active, process, legacy)` — [formula_dispatch.py:322](oled_formulas/formula_dispatch.py#L322)
- `digest(path)` — [formula_only.py:29](oled_formulas/formula_only.py#L29)
- `enabled(config)` — [formula_only.py:32](oled_formulas/formula_only.py#L32)
- `check_answer(raw, job, evidence)` — [formula_only.py:43](oled_formulas/formula_only.py#L43)
- `fresh(config, article, *, for_upload=…)` — [formula_only.py:63](oled_formulas/formula_only.py#L63)
- `publish(db, job, article, receipt, raw)` — [formula_only.py:76](oled_formulas/formula_only.py#L76)
- `configure_web_runtime()` — [formula_only.py:84](oled_formulas/formula_only.py#L84)
- `run(config)` — [formula_only.py:90](oled_formulas/formula_only.py#L90)
- `control_pilot(config, start)` — [formula_only.py:290](oled_formulas/formula_only.py#L290)
- `browser_connection()` — [formula_pilot.py:22](oled_formulas/formula_pilot.py#L22)
- `saved_formula_blank(control, tid, entry)` — [formula_pilot.py:33](oled_formulas/formula_pilot.py#L33)
- `saved_formula_response(control, tid, saved)` — [formula_pilot.py:41](oled_formulas/formula_pilot.py#L41)
- `save_observation(output, window_id, pool, checks)` — [formula_pilot.py:90](oled_formulas/formula_pilot.py#L90)
- `run(config, control, *, registered=…, connection=…, observer=…)` — [formula_pilot.py:107](oled_formulas/formula_pilot.py#L107)
- `temporary(page)` — [formula_pilot.py:322](oled_formulas/formula_pilot.py#L322)
- `temporary_settings(page, model, *, set_high=…)` — [formula_pilot.py:330](oled_formulas/formula_pilot.py#L330)
- `send_sample(config, control, folder, browser, page, tid, lock, stopped, note)` — [formula_pilot.py:359](oled_formulas/formula_pilot.py#L359)
- `terminal_evidence(page, folder, receipt, snapshot)` — [formula_pilot.py:496](oled_formulas/formula_pilot.py#L496)
- `exact_user_turn(page, prompt)` — [formula_pilot.py:527](oled_formulas/formula_pilot.py#L527)
- `collect_sample(config, control, folder, browser, page, rec, stopped, note)` — [formula_pilot.py:539](oled_formulas/formula_pilot.py#L539)
- `prolonged_empty_answer(folder, receipt, snapshot)` — [formula_pilot.py:627](oled_formulas/formula_pilot.py#L627)
- `confirm_empty_answer(folder, receipt, snapshot)` — [formula_pilot.py:650](oled_formulas/formula_pilot.py#L650)
- `replace_text(path, value)` — [formula_pilot.py:676](oled_formulas/formula_pilot.py#L676)
- `completed_formula_text(snapshot)` — [formula_pilot.py:689](oled_formulas/formula_pilot.py#L689)
- `image_warning(health)` — [formula_pilot.py:701](oled_formulas/formula_pilot.py#L701)
- `response_objects(raw)` — [formula_pilot.py:705](oled_formulas/formula_pilot.py#L705)
- `save_formulas(control, folder, rec, note)` — [formula_pilot.py:730](oled_formulas/formula_pilot.py#L730)
- `schedule(db, root, control, config)` — [formula_queue.py:20](oled_formulas/formula_queue.py#L20)
- `packet(db, config, root, folder, batch)` — [formula_queue.py:75](oled_formulas/formula_queue.py#L75)
- `publish(db, root, output, batch, folder)` — [formula_queue.py:120](oled_formulas/formula_queue.py#L120)
- `render_paper(db, root, output, paper, cache)` — [formula_queue.py:156](oled_formulas/formula_queue.py#L156)
- `recover_saved_reviews(db, config, control, root, output, active)` — [formula_queue.py:225](oled_formulas/formula_queue.py#L225)
- `refresh_image_reviews(db, root, output, active)` — [formula_queue.py:279](oled_formulas/formula_queue.py#L279)
- `recover_publications(db, root, output, active)` — [formula_queue.py:302](oled_formulas/formula_queue.py#L302)
- `run(config, control)` — [formula_queue.py:315](oled_formulas/formula_queue.py#L315)
- `stalled_load(check, entry, minimum_age)` — [formula_reload.py:16](oled_formulas/formula_reload.py#L16)
- `recover_load(config, control, db, browser, checks, pool, output, observed, active)` — [formula_reload.py:35](oled_formulas/formula_reload.py#L35)
- `reconcile_saved_slots(config, control, db, browser, pw, checks, pool, output, reserved, active)` — [formula_reload.py:85](oled_formulas/formula_reload.py#L85)
- `completed_home(control, db, output, tid, entry)` — [formula_reload.py:138](oled_formulas/formula_reload.py#L138)
- `adopt_completed_homes(config, control, db, browser, pw, checks, pool, output, reserved, observed, active)` — [formula_reload.py:167](oled_formulas/formula_reload.py#L167)
- `scalar_node(node)` — [formula_results.py:22](oled_formulas/formula_results.py#L22)
- `check_python(item)` — [formula_results.py:54](oled_formulas/formula_results.py#L54)
- `bound_warning(folder, batch)` — [formula_results.py:70](oled_formulas/formula_results.py#L70)
- `apply_audit_holds(article, source, items)` — [formula_results.py:82](oled_formulas/formula_results.py#L82)
- `python_mapping_issues(item)` — [formula_results.py:94](oled_formulas/formula_results.py#L94)
- `review_python(item)` — [formula_results.py:111](oled_formulas/formula_results.py#L111)
- `verified_latex(article, formulas, review, evidence)` — [formula_results.py:121](oled_formulas/formula_results.py#L121)
- `training_view(article, formulas, review=…, evidence=…)` — [formula_results.py:149](oled_formulas/formula_results.py#L149)
- `frozen_pages(db, folder, batch)` — [formula_results.py:166](oled_formulas/formula_results.py#L166)
- `coverage(db, paper, records)` — [formula_results.py:187](oled_formulas/formula_results.py#L187)
- `read_menu(folder, since, now)` — [pro_menu.py:12](oled_formulas/pro_menu.py#L12)
- `ProMenu.__init__(self, path, diagnostics)` — [pro_menu.py:45](oled_formulas/pro_menu.py#L45)
- `ProMenu.observe(self, now)` — [pro_menu.py:55](oled_formulas/pro_menu.py#L55)
- `ProMenu.retire_slot(self, slot, job)` — [pro_menu.py:82](oled_formulas/pro_menu.py#L82)
- `oled_candidate(title, abstract)` — [scope.py:8](oled_formulas/scope.py#L8)
- `ordinary_words_only(record)` — [scope.py:19](oled_formulas/scope.py#L19)
- `quiet(view)` — [slot_recovery.py:26](oled_formulas/slot_recovery.py#L26)
- `draft_matches(value, prompt)` — [slot_recovery.py:32](oled_formulas/slot_recovery.py#L32)
- `own_draft(view, receipt)` — [slot_recovery.py:40](oled_formulas/slot_recovery.py#L40)
- `upload_pair(events, receipt, status)` — [slot_recovery.py:49](oled_formulas/slot_recovery.py#L49)
- `stopped_text(folder, receipt, view)` — [slot_recovery.py:62](oled_formulas/slot_recovery.py#L62)
- `archive_page(folder, page, view, receipt, entry)` — [slot_recovery.py:78](oled_formulas/slot_recovery.py#L78)
- `recover(config, control, db, browser, pw, checks, pool, output, reserved, active, timers, traces)` — [slot_recovery.py:96](oled_formulas/slot_recovery.py#L96)
- `AppQueueTests.test_only_clean_unsent_batches_move_and_restart_is_idempotent(self)` — [tests/test_app_queue.py:13](oled_formulas/tests/test_app_queue.py#L13)
- `AppQueueTests.test_account_check_requires_authenticated_embedded_app(self)` — [tests/test_app_queue.py:28](oled_formulas/tests/test_app_queue.py#L28)
- `AppQueueTests.test_no_slot_recovery_requires_absence_of_any_transfer(self)` — [tests/test_app_queue.py:52](oled_formulas/tests/test_app_queue.py#L52)
- `AppQueueTests.test_app_only_route_finishes_without_revisiting_legacy_chrome(self)` — [tests/test_app_queue.py:71](oled_formulas/tests/test_app_queue.py#L71)
- `AppQueueTests.test_free_slot_refills_while_four_other_jobs_are_still_running(self)` — [tests/test_app_queue.py:100](oled_formulas/tests/test_app_queue.py#L100)
- `AppQueueTests.test_busy_inspector_needs_recent_same_session_evidence(self)` — [tests/test_app_queue.py:131](oled_formulas/tests/test_app_queue.py#L131)
- `AttachmentBackoffTests.test_two_distinct_slots_and_one_quota_notice(self)` — [tests/test_attachment_gate.py:12](oled_formulas/tests/test_attachment_gate.py#L12)
- `AttachmentBackoffTests.test_native_menu_disabled_overrides_hidden_document_input(self)` — [tests/test_attachment_gate.py:21](oled_formulas/tests/test_attachment_gate.py#L21)
- `AttachmentBackoffTests.test_native_probe_requires_enabled_menu_item_and_zip_input(self)` — [tests/test_attachment_gate.py:32](oled_formulas/tests/test_attachment_gate.py#L32)
- `AttachmentBackoffTests.test_native_document_input_without_menuitem_role(self)` — [tests/test_attachment_gate.py:49](oled_formulas/tests/test_attachment_gate.py#L49)
- `AttachmentBackoffTests.test_preflight_recovery_requires_no_transfer_and_is_spent_once(self)` — [tests/test_attachment_gate.py:65](oled_formulas/tests/test_attachment_gate.py#L65)
- `AttachmentBackoffTests.test_restart_and_bound_success(self)` — [tests/test_attachment_gate.py:87](oled_formulas/tests/test_attachment_gate.py#L87)
- `AttachmentBackoffTests.test_recovery_requires_transfer_and_archive_proof_and_is_spent_once(self)` — [tests/test_attachment_gate.py:111](oled_formulas/tests/test_attachment_gate.py#L111)
- `DisplayEquations.test_number_is_optional_and_math_inside_a_sentence_is_rejected(self)` — [tests/test_display_equations.py:13](oled_formulas/tests/test_display_equations.py#L13)
- `DisplayEquations.test_no_files_for_inline_or_empty_regions(self)` — [tests/test_display_equations.py:25](oled_formulas/tests/test_display_equations.py#L25)
- `DisplayEquations.test_missing_layout_requires_isolated_math_evidence(self)` — [tests/test_display_equations.py:42](oled_formulas/tests/test_display_equations.py#L42)
- `DisplayEquations.test_oled_scope_and_unfrozen_mixed_batch(self)` — [tests/test_display_equations.py:54](oled_formulas/tests/test_display_equations.py#L54)
- `FormulaTests.test_dispatch_requires_fresh_eligible_unassigned_tab(self)` — [tests/test_formula_only.py:9](oled_formulas/tests/test_formula_only.py#L9)
- `FormulaTests.test_paper_order_keeps_later_pages_of_earlier_group(self)` — [tests/test_formula_only.py:23](oled_formulas/tests/test_formula_only.py#L23)
- `FormulaTests.test_parallel_dispatch_shares_loop_and_never_assigns_a_tab_twice(self)` — [tests/test_formula_only.py:36](oled_formulas/tests/test_formula_only.py#L36)
- `FormulaTests.test_idle_effort_only_adjusts_owned_empty_available_home(self)` — [tests/test_formula_only.py:76](oled_formulas/tests/test_formula_only.py#L76)
- `FormulaTests.test_held_composer_setting_excludes_sent_or_misattributed_work(self)` — [tests/test_formula_only.py:88](oled_formulas/tests/test_formula_only.py#L88)
- `FormulaTests.test_unsent_slot_release_preserves_held_batch_and_prior_archive(self)` — [tests/test_formula_only.py:108](oled_formulas/tests/test_formula_only.py#L108)
- `FormulaTests.test_completed_turn_requires_single_stable_candidate(self)` — [tests/test_formula_only.py:181](oled_formulas/tests/test_formula_only.py#L181)
- `FormulaTests.test_reused_blank_requires_the_original_completed_formula_receipt(self)` — [tests/test_formula_only.py:190](oled_formulas/tests/test_formula_only.py#L190)
- `FormulaTests.test_legacy_archived_batch_requires_its_original_prompt_zip_and_number(self)` — [tests/test_formula_only.py:212](oled_formulas/tests/test_formula_only.py#L212)
- `FormulaTests.test_loading_recovery_rechecks_live_page_and_navigates_only_once(self)` — [tests/test_formula_only.py:237](oled_formulas/tests/test_formula_only.py#L237)
- `FormulaTests.test_jsonl_language_label_is_only_removed_before_a_valid_object(self)` — [tests/test_formula_only.py:268](oled_formulas/tests/test_formula_only.py#L268)
- `FormulaTests.test_adjacent_json_objects_preserve_math_and_reject_partial_replies(self)` — [tests/test_formula_only.py:275](oled_formulas/tests/test_formula_only.py#L275)
- `FormulaTests.test_pdf_small_type_qualifier_flags_missing_token(self)` — [tests/test_formula_only.py:284](oled_formulas/tests/test_formula_only.py#L284)
- `FormulaTests.test_vector_symbol_at_left_edge_is_kept_without_crossing_whitespace(self)` — [tests/test_formula_only.py:292](oled_formulas/tests/test_formula_only.py#L292)
- `FormulaTests.test_mode_requires_all_original_pauses(self)` — [tests/test_formula_only.py:303](oled_formulas/tests/test_formula_only.py#L303)
- `FormulaTests.test_packet_coverage(self)` — [tests/test_formula_only.py:314](oled_formulas/tests/test_formula_only.py#L314)
- `FormulaTests.test_panel_controls_only_the_registered_pilot(self)` — [tests/test_formula_only.py:324](oled_formulas/tests/test_formula_only.py#L324)
- `FormulaTests.test_temporary_locked_picker_requires_exact_model_and_high(self)` — [tests/test_formula_only.py:353](oled_formulas/tests/test_formula_only.py#L353)
- `FormulaTests.test_multi_paper_batch_preserves_multiple_equations_and_non_equations(self)` — [tests/test_formula_only.py:372](oled_formulas/tests/test_formula_only.py#L372)
- `ProMenuTests.test_single_window_cadence_across_restart_and_preservation(self)` — [tests/test_pro_menu.py:12](oled_formulas/tests/test_pro_menu.py#L12)
- `ProjectEntry.test_legacy_owner_and_control_resolve_to_project(self)` — [tests/test_project_entry.py:10](oled_formulas/tests/test_project_entry.py#L10)
- `ReportRegressions.test_training_candidates_and_printed_labels(self)` — [tests/test_report_regressions.py:16](oled_formulas/tests/test_report_regressions.py#L16)
- `ReportRegressions.test_blank_wait_requires_contiguous_confirmations_and_resumes_only_original(self)` — [tests/test_report_regressions.py:32](oled_formulas/tests/test_report_regressions.py#L32)
- `ReportRegressions.test_scientific_training_receipt_is_bound_to_saved_formula(self)` — [tests/test_report_regressions.py:54](oled_formulas/tests/test_report_regressions.py#L54)
- `ReportRegressions.test_code_is_validated_without_execution(self)` — [tests/test_report_regressions.py:73](oled_formulas/tests/test_report_regressions.py#L73)
- `ReportRegressions.test_empty_terminal_requires_two_stationary_observations(self)` — [tests/test_report_regressions.py:84](oled_formulas/tests/test_report_regressions.py#L84)
- `ReportRegressions.test_publish_recovery_and_partial_coverage(self)` — [tests/test_report_regressions.py:97](oled_formulas/tests/test_report_regressions.py#L97)
- `ReportRegressions.test_home_recovery_requires_stable_empty_target_and_receipt(self)` — [tests/test_report_regressions.py:166](oled_formulas/tests/test_report_regressions.py#L166)
- `ReportRegressions.test_terminal_evidence_stays_on_original_assistant_turn(self)` — [tests/test_report_regressions.py:200](oled_formulas/tests/test_report_regressions.py#L200)
- `ReportRegressions.test_disjoint_box_requires_unique_printed_equation_number(self)` — [tests/test_report_regressions.py:216](oled_formulas/tests/test_report_regressions.py#L216)
- `SlotRecoveryTests.test_clean_only_matching_unsent_content(self)` — [tests/test_slot_recovery.py:10](oled_formulas/tests/test_slot_recovery.py#L10)
- `SlotRecoveryTests.test_finished_upload_identity_must_match_before_cleanup(self)` — [tests/test_slot_recovery.py:22](oled_formulas/tests/test_slot_recovery.py#L22)
- `SlotRecoveryTests.test_unavailable_release_verifies_original_and_returned_evidence(self)` — [tests/test_slot_recovery.py:33](oled_formulas/tests/test_slot_recovery.py#L33)
- `SlotRecoveryTests.test_stopped_text_requires_exact_raw_and_every_frozen_page(self)` — [tests/test_slot_recovery.py:53](oled_formulas/tests/test_slot_recovery.py#L53)
- `authorized(folder, job, tid)` — [unavailable_slots.py:13](oled_formulas/unavailable_slots.py#L13)
- `released(folder, job, tid)` — [unavailable_slots.py:32](oled_formulas/unavailable_slots.py#L32)
- `released_blank(control, tid, entry)` — [unavailable_slots.py:46](oled_formulas/unavailable_slots.py#L46)
- `release_home(folder, job, tid, db, n, page, entry, pool_path, guard)` — [unavailable_slots.py:55](oled_formulas/unavailable_slots.py#L55)

## 文件 SHA-256

```json
{
  "README.md": "8abb5dc80a20cf31283c7ff889181c26e42b3ee4145ca01b6b4f082bc0d82c22",
  "__init__.py": "e32755f0d241922a2fe762b0b98dfaee58c735acb5e36675259fb474b1f62aa9",
  "__main__.py": "f22cca0108b4a4d51501c889486467f8ad7529f9a8eb67fe56348fe464d8f19b",
  "api.py": "375389485c88b5ec6e522972de9fec6c74d48df1e84f75c43e9cb3a703b491b5",
  "app_queue.py": "723929a9cb3e4d9e7cedb3e4a0c210608dc2637142938adc521b73e342ce9aee",
  "attachment_gate.py": "76d02bd712f7a07b1dff6186903cfc5b9f30c37ff6b356d67c6d24879d5b547a",
  "audit-review-items.json": "bb7c5ceff195fdb565b38d522220c55c4ad60d764250da4cec5f701b03410b66",
  "display_equations.py": "4885c74f395a17480272994706c4e8fc9c8f7cd563b1a46269ab2dd67801f2c3",
  "entry_retry.py": "dc24d178bfd9e1a6acad32d0d311f3882cc42e2f3eedd5af189ecaf023abdb1a",
  "formula_dispatch.py": "6105d23fb01195ec93922ab79dab344bba95133e65a66dbc0b26f7a208591c32",
  "formula_only.py": "72788d0de5549a99ffc9a9893525f2c6a519376c3522a1bb5c65652d433196df",
  "formula_pilot.py": "3f9a890768c798b8c47befff77d8c221d0a26344a2e7374a9a57a554195bcbb8",
  "formula_queue.py": "52c05d93c5d89cd5784f54a3bd556cf97914abca359748882b09e279a2b34526",
  "formula_reload.py": "46e766305a66c5916a6e85cc04201a60d9bfb78fcfe39dd757e213676ddecd9e",
  "formula_results.py": "60a8a5928d3963764ffcc5628a00ab2b3aa62f7218e3d409a1934db543a95ff2",
  "interface.json": "217d79bf1cdc35390d68c338d646aa616fa74b2fbc9507d7a167a2290fc70caa",
  "pro_menu.py": "f710edc7315bdcc2e295386205b0d71bdfda577ed7665428777454cb20939fb4",
  "pyproject.toml": "78ed63cf18864e6a26d6d341060fe49859c5c8034971befaba934e2a7b97ae93",
  "scope.py": "886ca1522d1be1ff118b71f25a15361ebe7b4475b8fa9a50af550223452f6bf1",
  "slot_recovery.py": "05ff6c545e7a918de92a46724ab6f9a9497134a2fce1386907b0e30041254959",
  "tests/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "tests/test_app_queue.py": "2d7d1eb434d58eac23f75a040fcb694f00f6e1d413954762dfbcb82701262c2f",
  "tests/test_attachment_gate.py": "3dd55cd0a12c80bb681192b764e119d30e5ca44eb0d93c40bc6b53e879e19415",
  "tests/test_display_equations.py": "6270253739f70c8549aa2af7d5b3e0f152e0bf0df0ff981720a3aaf6f6a69f14",
  "tests/test_formula_only.py": "c4779cb785ebd7e66faf4196b18642b0d2d4368eed8ca90e8a54920c9a9b85dd",
  "tests/test_pro_menu.py": "5958e1d6c36b8420791e20e5824a348d63b952cbbf3846aea37ebc6b94d17a42",
  "tests/test_project_entry.py": "fa2184eeb9da55255a69bf995992530625da14023797f6de965579a443dc71e8",
  "tests/test_report_regressions.py": "4a532e1817de836b33d74bb45dcbad8cd6cd02fcf8a6d4bf8d87006060fe5044",
  "tests/test_slot_recovery.py": "49580bd653d6f6eb770b5ec5c5d1ba6c1d5e8f45d9f2162b4adfb32890ac8e31",
  "unavailable-slot-authorization.json": "f52ae8c77e76a8eae92cb38162d2285cdbcdafda4a9b0fd914a622e4c89aeff2",
  "unavailable_slots.py": "de1481a97c8e058535061c15c12a27f431ec5a901b94921271db146cbda8ae85"
}
```
