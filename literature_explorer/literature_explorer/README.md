# Literature Explorer

面向科研工作的自动文献发现系统。第一版完成核心闭环：

```text
研究主题 → OpenAlex / Semantic Scholar 搜索 → 统一 Paper 格式 → 去重
→ SQLite → embedding 相关性排序 → 候选论文 → 人工标记
→ 从 interesting 论文做引文扩展 → 新一轮候选
```

原则：用户负责判断「值不值得继续看」，系统负责扩大搜索、整理候选、持续扩展。
纯 Python 标准库实现（urllib + sqlite3），零 pip 依赖。Python 3.10+。

## 快速开始

```bash
cd literature_explorer

# 1. 搜索主题，产出 Top N 候选
python scripts/search_topic.py "OLED triplet exciton"

# 2. 逐篇人工审核
python scripts/review_candidates.py

# 3. 对 interesting 论文做引文扩展，生成下一批候选
python scripts/expand_interesting.py
```

三个脚本均可重复运行：不重复抓取已有论文（citation_fetches scope_key 去重）、
不丢用户反馈、可追踪每篇论文来源（discovery_records）、中断后可恢复（SQLite 持久化）。

## 环境变量（均可选）

| 变量 | 作用 |
|---|---|
| `OPENALEX_EMAIL` | OpenAlex polite pool，建议设置 |
| `S2_API_KEY` | Semantic Scholar 独立限速池；不设置则按 1 rps 保守限速 |
| `LITEXP_EMBEDDING_BASE_URL` | OpenAI 兼容 embedding 接口地址，如 `https://api.siliconflow.cn/v1` |
| `LITEXP_EMBEDDING_API_KEY` | embedding 接口密钥 |
| `LITEXP_EMBEDDING_MODEL` | embedding 模型名 |
| `LITEXP_DB` | SQLite 路径（默认 `data/literature.db`） |

不配置 `LITEXP_EMBEDDING_*` 时自动降级为词袋重叠打分，流程不断链。

## 目录结构

```text
config.py               环境变量配置
connectors/             数据源（base 限流重试 + openalex + semantic_scholar）
models/paper.py         统一 Paper 模型 + 去重键 + 合并规则
discovery/              搜索 / 查询扩展 / 引文扩展 / 主循环
ranking/                embedding provider + 相关性打分（含降级）
screening/              待审队列 + 人工反馈
storage/sqlite.py       七张表：papers / paper_sources / discovery_records /
                        user_feedback / embeddings / search_runs / citation_fetches
scripts/                三个 CLI 入口
tests/                  python -m unittest discover tests
data/                   literature.db（自动创建）
```

## 去重规则

`Paper.dedup_key()` 优先级：DOI → OpenAlex ID → Semantic Scholar ID → normalized title。
跨源同一论文按「最完整优先」合并：DOI 先到先得、摘要看长、被引数取大、来源求并。

## 后续阶段（本版不做）

- PDF 获取 `fetch_fulltext()`（参考 findpapers DownloadRunner 思路）
- Quick Summary / Deep Read：预留 PaperQA2 接口

```python
def summarize_paper(paper_id): ...   # 第二阶段接入
def deep_read(paper_id): ...         # 第二阶段接入 PaperQA2
```

- 多轮自动 discovery（边际收益停止规则，参考 openalex_search `should_stop_for_marginal_gain`）
- 标题模糊去重与预印本年份兼容（参考 findpapers 两阶段去重）
- Zotero 同步、OLED 知识库摄入（仅 deep_read + 人工确认高价值的论文进入）

## 审核修复合同（2026-10-14）

- `discovery/citation_expand.py` 按来源独立记录scope；只有完整返回才标记完成。失败记 `deferred/last_error/retry_at`（至少60秒），成功来源不重抓。无可用来源身份不记完成。既有聚合完成记录保留，不能仅凭零结果自动重扫。
- `storage/sqlite.py` 新增 `IdentityConflict` 和 `identity_conflicts` 原始输入隔离表；合并前核对所有命中记录及归一化DOI，矛盾时保存证据并拒绝变更原事实。搜索/引文入口跳过已隔离记录，继续其它候选。补DOI保留原稳定ID和provenance。历史记录不自动拆分。
- `models/paper.py` 的 `Paper.merge` 拒绝矛盾DOI、保留已存在ID。相同DOI可补来自不同来源的信息；外部ID仅保留原首个值，不引入未经审核的历史别名迁移。
- `ranking/embedding.py` 的 `validate_vectors` 检查完整索引集合、批次数量、非空一致维度及有限数值；失败走原有有界重试/拆批，保持逐输入占位。`embed_papers(..., expected_dimension=None)` 可按主题向量维度过滤缓存和新向量；非法历史缓存留存并降级，不自动覆盖，旧错位缓存不能靠维度检查证明正确。
- `discovery/query_expand.py` 的 `expanded_queries(..., *, current_papers=None, scores=None)` 仅使用显式本轮候选及本主题评分；没有候选返回空。`discovery/loop.py` 已同步传入首波候选和本轮分数。
- `connectors/base.py` 新增 `DeferredRequest(retry_at, reason)`（继承 `ConnectorError`）及每主机持久冷却。429/503不长睡；其它5xx单次需等待超过5秒时也延后。冷却数据库为 `<LITEXP_DB>.http-cooldowns.sqlite3`，跨HttpClient/进程保留Retry-After数字或HTTP-date，不截短上游要求。原有max_rate_limit_retries构造参数保留兼容；429改为单次请求后延后。Store的引文scope和HTTP主机冷却分别保存，不恢复其它任务暂停。
- [tests/test_audit_regressions.py](tests/test_audit_regressions.py) 是离线故障注入测试；不代表真实来源、embedding服务或历史库科学验收。
