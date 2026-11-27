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
- `plan(db, root, seeds)` — [display_equations.py:32](oled_formulas/display_equations.py#L32)
- `evidence(page)` — [display_equations.py:49](oled_formulas/display_equations.py#L49)
- `build_packet(db, config, root, folder, batch)` — [display_equations.py:69](oled_formulas/display_equations.py#L69)
- `prose(text)` — [display_equations.py:131](oled_formulas/display_equations.py#L131)
- `mark_page_conflicts(records)` — [display_equations.py:138](oled_formulas/display_equations.py#L138)
- `locate(item, lines)` — [display_equations.py:149](oled_formulas/display_equations.py#L149)
- `transcription_check(item, lines)` — [display_equations.py:226](oled_formulas/display_equations.py#L226)
- `include_edge_symbols(image, box)` — [display_equations.py:249](oled_formulas/display_equations.py#L249)
- `crop_results(folder, manifest, records)` — [display_equations.py:273](oled_formulas/display_equations.py#L273)
- `digest(path)` — [formula_only.py:12](oled_formulas/formula_only.py#L12)
- `app_route(request)` — [formula_only.py:15](oled_formulas/formula_only.py#L15)
- `enabled(config)` — [formula_only.py:21](oled_formulas/formula_only.py#L21)
- `check_answer(raw, job, evidence)` — [formula_only.py:32](oled_formulas/formula_only.py#L32)
- `fresh(config, article, *, for_upload=…)` — [formula_only.py:52](oled_formulas/formula_only.py#L52)
- `publish(db, job, article, receipt, raw)` — [formula_only.py:65](oled_formulas/formula_only.py#L65)
- `run(config)` — [formula_only.py:73](oled_formulas/formula_only.py#L73)
- `control_pilot(config, start)` — [formula_only.py:91](oled_formulas/formula_only.py#L91)
- `replace_text(path, value)` — [formula_pilot.py:8](oled_formulas/formula_pilot.py#L8)
- `image_warning(health)` — [formula_pilot.py:21](oled_formulas/formula_pilot.py#L21)
- `response_objects(raw)` — [formula_pilot.py:25](oled_formulas/formula_pilot.py#L25)
- `save_formulas(control, folder, rec, note)` — [formula_pilot.py:50](oled_formulas/formula_pilot.py#L50)
- `schedule(db, root, control, config)` — [formula_queue.py:20](oled_formulas/formula_queue.py#L20)
- `packet(db, config, root, folder, batch)` — [formula_queue.py:75](oled_formulas/formula_queue.py#L75)
- `publish(db, root, output, batch, folder)` — [formula_queue.py:120](oled_formulas/formula_queue.py#L120)
- `render_paper(db, root, output, paper, cache)` — [formula_queue.py:156](oled_formulas/formula_queue.py#L156)
- `recover_saved_reviews(db, config, control, root, output, active)` — [formula_queue.py:225](oled_formulas/formula_queue.py#L225)
- `refresh_image_reviews(db, root, output, active)` — [formula_queue.py:279](oled_formulas/formula_queue.py#L279)
- `recover_publications(db, root, output, active)` — [formula_queue.py:302](oled_formulas/formula_queue.py#L302)
- `run(config, control)` — [formula_queue.py:315](oled_formulas/formula_queue.py#L315)
- `index_paper_order(db)` — [formula_queue.py:343](oled_formulas/formula_queue.py#L343)
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
- `release_path(folder)` — [legacy_receipts.py:6](oled_formulas/legacy_receipts.py#L6)
- `EntryTraces.__init__(self, path)` — [legacy_receipts.py:15](oled_formulas/legacy_receipts.py#L15)
- `EntryTraces.refresh(self)` — [legacy_receipts.py:21](oled_formulas/legacy_receipts.py#L21)
- `EntryTraces.verified(self, attempt, status)` — [legacy_receipts.py:43](oled_formulas/legacy_receipts.py#L43)
- `empty_formula_home(check)` — [legacy_receipts.py:60](oled_formulas/legacy_receipts.py#L60)
- `historical_slot_receipt(control, output, batch, state, tid, receipt, original_release=…)` — [legacy_receipts.py:68](oled_formulas/legacy_receipts.py#L68)
- `read_menu(folder, since, now)` — [pro_menu.py:12](oled_formulas/pro_menu.py#L12)
- `ProMenu.__init__(self, path, diagnostics)` — [pro_menu.py:45](oled_formulas/pro_menu.py#L45)
- `ProMenu.observe(self, now)` — [pro_menu.py:55](oled_formulas/pro_menu.py#L55)
- `ProMenu.retire_slot(self, slot, job)` — [pro_menu.py:82](oled_formulas/pro_menu.py#L82)
- `oled_candidate(title, abstract)` — [scope.py:8](oled_formulas/scope.py#L8)
- `ordinary_words_only(record)` — [scope.py:19](oled_formulas/scope.py#L19)
- `AppQueueTests.test_only_clean_unsent_batches_move_and_restart_is_idempotent(self)` — [tests/test_app_queue.py:13](oled_formulas/tests/test_app_queue.py#L13)
- `AppQueueTests.test_account_check_requires_authenticated_embedded_app(self)` — [tests/test_app_queue.py:28](oled_formulas/tests/test_app_queue.py#L28)
- `AppQueueTests.test_no_slot_recovery_requires_absence_of_any_transfer(self)` — [tests/test_app_queue.py:52](oled_formulas/tests/test_app_queue.py#L52)
- `AppQueueTests.test_app_only_route_finishes_without_revisiting_legacy_chrome(self)` — [tests/test_app_queue.py:71](oled_formulas/tests/test_app_queue.py#L71)
- `AppQueueTests.test_free_slot_refills_while_four_other_jobs_are_still_running(self)` — [tests/test_app_queue.py:97](oled_formulas/tests/test_app_queue.py#L97)
- `AppQueueTests.test_busy_inspector_needs_recent_same_session_evidence(self)` — [tests/test_app_queue.py:128](oled_formulas/tests/test_app_queue.py#L128)
- `DisplayEquations.test_number_is_optional_and_math_inside_a_sentence_is_rejected(self)` — [tests/test_display_equations.py:13](oled_formulas/tests/test_display_equations.py#L13)
- `DisplayEquations.test_no_files_for_inline_or_empty_regions(self)` — [tests/test_display_equations.py:25](oled_formulas/tests/test_display_equations.py#L25)
- `DisplayEquations.test_missing_layout_requires_isolated_math_evidence(self)` — [tests/test_display_equations.py:42](oled_formulas/tests/test_display_equations.py#L42)
- `DisplayEquations.test_oled_scope_and_unfrozen_mixed_batch(self)` — [tests/test_display_equations.py:54](oled_formulas/tests/test_display_equations.py#L54)
- `FormulaTests.test_paper_order_keeps_later_pages_of_earlier_group(self)` — [tests/test_formula_only.py:10](oled_formulas/tests/test_formula_only.py#L10)
- `FormulaTests.test_jsonl_language_label_is_only_removed_before_a_valid_object(self)` — [tests/test_formula_only.py:31](oled_formulas/tests/test_formula_only.py#L31)
- `FormulaTests.test_adjacent_json_objects_preserve_math_and_reject_partial_replies(self)` — [tests/test_formula_only.py:38](oled_formulas/tests/test_formula_only.py#L38)
- `FormulaTests.test_pdf_small_type_qualifier_flags_missing_token(self)` — [tests/test_formula_only.py:47](oled_formulas/tests/test_formula_only.py#L47)
- `FormulaTests.test_vector_symbol_at_left_edge_is_kept_without_crossing_whitespace(self)` — [tests/test_formula_only.py:55](oled_formulas/tests/test_formula_only.py#L55)
- `FormulaTests.test_mode_requires_all_original_pauses(self)` — [tests/test_formula_only.py:66](oled_formulas/tests/test_formula_only.py#L66)
- `FormulaTests.test_packet_coverage(self)` — [tests/test_formula_only.py:77](oled_formulas/tests/test_formula_only.py#L77)
- `FormulaTests.test_multi_paper_batch_preserves_multiple_equations_and_non_equations(self)` — [tests/test_formula_only.py:89](oled_formulas/tests/test_formula_only.py#L89)
- `ProMenuTests.test_single_window_cadence_across_restart_and_preservation(self)` — [tests/test_pro_menu.py:12](oled_formulas/tests/test_pro_menu.py#L12)
- `ProjectEntry.test_legacy_owner_and_control_resolve_to_project(self)` — [tests/test_project_entry.py:10](oled_formulas/tests/test_project_entry.py#L10)
- `ReportRegressions.test_training_candidates_and_printed_labels(self)` — [tests/test_report_regressions.py:15](oled_formulas/tests/test_report_regressions.py#L15)
- `ReportRegressions.test_scientific_training_receipt_is_bound_to_saved_formula(self)` — [tests/test_report_regressions.py:32](oled_formulas/tests/test_report_regressions.py#L32)
- `ReportRegressions.test_code_is_validated_without_execution(self)` — [tests/test_report_regressions.py:51](oled_formulas/tests/test_report_regressions.py#L51)
- `ReportRegressions.test_publish_recovery_and_partial_coverage(self)` — [tests/test_report_regressions.py:63](oled_formulas/tests/test_report_regressions.py#L63)
- `ReportRegressions.test_disjoint_box_requires_unique_printed_equation_number(self)` — [tests/test_report_regressions.py:135](oled_formulas/tests/test_report_regressions.py#L135)

## 文件 SHA-256

```json
{
  "README.md": "dff1c73fb19a7ab3b021890ae26a38a754446bb7f81b636be7551ede01247d05",
  "__init__.py": "e32755f0d241922a2fe762b0b98dfaee58c735acb5e36675259fb474b1f62aa9",
  "__main__.py": "f22cca0108b4a4d51501c889486467f8ad7529f9a8eb67fe56348fe464d8f19b",
  "api.py": "375389485c88b5ec6e522972de9fec6c74d48df1e84f75c43e9cb3a703b491b5",
  "app_queue.py": "b06861cb4694f343c1f678e803464c8e69aa80709fbf68ed842bc032e64eca5e",
  "audit-review-items.json": "bb7c5ceff195fdb565b38d522220c55c4ad60d764250da4cec5f701b03410b66",
  "display_equations.py": "4885c74f395a17480272994706c4e8fc9c8f7cd563b1a46269ab2dd67801f2c3",
  "formula_only.py": "c35f9def9db9e49bb68b74a562371e2c02723cf7bb5d7943941b4ca67a2cecda",
  "formula_pilot.py": "95255727243a1aa1e7885f24f28a6a42a005854292d142a45ca480bac9b76d46",
  "formula_queue.py": "f13fceaf584cac5afa83ab9801c11e01d568eac8a5b2dde01a63fbadd415332d",
  "formula_results.py": "60a8a5928d3963764ffcc5628a00ab2b3aa62f7218e3d409a1934db543a95ff2",
  "interface.json": "8e163b56ea16b99bbf4109897c43029755989e3ea735c2b194bd0c41e7c67a96",
  "legacy_receipts.py": "604acb8fd971a278a27d9811586e197b39a96026820c2a6381f2a58951687e6f",
  "pro_menu.py": "f710edc7315bdcc2e295386205b0d71bdfda577ed7665428777454cb20939fb4",
  "pyproject.toml": "12a9c02a70967b3a535cd53c6ebec4e9820aee3c314bc9fa5ba4077a27ff96c7",
  "scope.py": "886ca1522d1be1ff118b71f25a15361ebe7b4475b8fa9a50af550223452f6bf1",
  "tests/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "tests/test_app_queue.py": "5c5611fbf47f190fe070c36959ade34cce964ff38f7f3a4bae321aa60d8f2b9c",
  "tests/test_display_equations.py": "6270253739f70c8549aa2af7d5b3e0f152e0bf0df0ff981720a3aaf6f6a69f14",
  "tests/test_formula_only.py": "0419cf20cdbc0617977bb769104298aaddb53dfe387ff06abc1202925723e95f",
  "tests/test_pro_menu.py": "5958e1d6c36b8420791e20e5824a348d63b952cbbf3846aea37ebc6b94d17a42",
  "tests/test_project_entry.py": "fa2184eeb9da55255a69bf995992530625da14023797f6de965579a443dc71e8",
  "tests/test_report_regressions.py": "8e6bd1c90f99015d4edfa9ec2de2138a3dedd9e654da5715d41855d3bbd30f4d",
  "unavailable-slot-authorization.json": "f52ae8c77e76a8eae92cb38162d2285cdbcdafda4a9b0fd914a622e4c89aeff2"
}
```
