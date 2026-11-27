# literature_explorer：跨项目调用说明

面向科研主题的自动文献发现闭环：输入研究主题，跨 OpenAlex / Semantic Scholar 搜索、标准化、去重、相关性排序产出候选论文池；人工标记 interesting 后自动做引文扩展生成下一轮候选。公开接口为 Python 函数 + 三个 CLI 脚本；无 HTTP 服务。纯 Python 标准库，零 pip 依赖。

- 本目录 ID：`literature_explorer`
- 权威源码：`../../../paper/fetch/crawler/literature_explorer`
- 原始说明：[README.md](../../../paper/fetch/crawler/literature_explorer/README.md)
- Python 导入根：`../../../paper/fetch/crawler/literature_explorer`（顶层包目录本身；导入形式为 `import config`、`from connectors.openalex import search_openalex`）
- 维护方规则：[crawler/AGENTS.md](../../../paper/fetch/crawler/AGENTS.md)；导出记录：[tool-dependencies.json](../../../paper/fetch/crawler/tool-dependencies.json)
- 已确认使用方：无（2026-09-18 首次登记）
- 核对日期：2026-09-18，未版本化

## 1. 准备环境

Python 3.10+（代码使用 `list[str] | None` 等语法），无第三方依赖。联网访问 OpenAlex（api.openalex.org）与 Semantic Scholar（api.semanticscholar.org）公开 API；两者均可无密钥使用。

| 环境变量 | 谁读取 | 默认及用途 |
| --- | --- | --- |
| `LITEXP_IMPORT_ROOT` | 本文的调用方示例 | 无默认值；定位导入根，不是工具原生配置 |
| `LITEXP_DB` | 工具（import config 时） | `<source_dir>/data/literature.db`，SQLite 路径 |
| `OPENALEX_EMAIL` | 工具（每次请求时读 config） | 空；设置后进入 OpenAlex polite pool |
| `S2_API_KEY` | 工具 | 空；无 key 时 Semantic Scholar 按 1 rps 保守限速 |
| `LITEXP_EMBEDDING_BASE_URL` / `LITEXP_EMBEDDING_API_KEY` / `LITEXP_EMBEDDING_MODEL` | 工具 | 空；三者同时设置才启用真实 embedding（OpenAI 兼容 `/embeddings` 接口），否则降级为词袋重叠打分 |

原生配置在 `import config` 时读取，须在导入前设置。`LITEXP_DB` 决定全部状态（论文库、反馈、缓存）的位置；多项目共用同一 DB 即共享论文池与去重状态。

## 2. 最小调用

将以下内容保存为使用方项目的 `examples/litexp_minimal.py`，在任意工作目录执行：

```python
import os
import sys
import tempfile
from pathlib import Path

import_root = Path(os.environ["LITEXP_IMPORT_ROOT"]).expanduser().resolve()
if not (import_root / "config.py").is_file():
    raise RuntimeError(f"找不到 literature_explorer 导入根：{import_root}")
sys.path.insert(0, str(import_root))

# 用临时 DB 验证，不碰正式库；须在 import config 前设置
os.environ["LITEXP_DB"] = str(Path(tempfile.mkdtemp()) / "demo.db")

from discovery.loop import run_discovery_cycle
from screening.feedback import record_feedback
from storage.sqlite import Store

with Store() as store:
    ranked, scores = run_discovery_cycle(store, "OLED triplet exciton", top_n=10,
                                         second_wave=False)
    for paper in ranked:
        print(f"{scores[paper.paper_id]:.3f} | {paper.year} | {paper.title}")
    if ranked:
        record_feedback(store, ranked[0].paper_id, "interesting", "demo")
```

此示例发起真实网络搜索（通常数十秒；无 S2 key 时更慢）。离线验证可运行工具自带测试：

```bash
cd ../../../paper/fetch/crawler/literature_explorer
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover tests -v
```

## 3. 接口契约

Python 接口（均为普通函数，参数即输入，返回 JSON 可序列化结构或 dataclass）：

| 接口 | 输入/默认值 | 返回/行为 |
| --- | --- | --- |
| `run_discovery_cycle(store, topic, top_n=30, second_wave=True)` | Store 实例、主题串 | `(ranked_papers, {paper_id: score})`；写库并创建 search_run |
| `search_papers(store, query, run_id, round_no=0, limit=50)` | 查询串 | 双源搜索→去重→入库，返回 `list[Paper]`；单源失败降级为 stderr 警告 |
| `expand_from_paper(store, paper_id, run_id, round_no=1, ref_limit=50, cit_limit=100)` | 种子 paper_id | references + citations 各扩一层，返回新入库 `list[Paper]`；来源独立scope；完成不重抓，失败持久延后；原聚合完成记录保留 |
| `score_papers(store, topic, papers)` | 论文列表 | `{paper_id: float}` 并写入 papers.relevance_score |
| `record_feedback(store, paper_id, decision, note="")` | decision ∈ interesting/reject/later | 非法 decision 抛 `ValueError` |
| `get_review_queue(store, limit=50)` / `interesting_papers(store)` | — | 待审 / 已标记论文列表 |
| `Store.upsert_paper(paper)` | Paper | `(paper_id, is_new)`；按精确键匹配；归一化DOI矛盾/跨记录身份冲突保存隔离证据并抛IdentityConflict，不改原事实 |
| `Paper.dedup_key()` / `Paper.merge(other)` | — | 去重键 / 最完整优先字段合并 |

CLI 入口（工作目录须为源码目录，或先设 PYTHONPATH 为导入根）：

```bash
python3 scripts/search_topic.py "OLED triplet exciton" [--limit 30] [--db path] [--no-second-wave]
python3 scripts/review_candidates.py [--limit 50] [--db path]
python3 scripts/expand_interesting.py [--limit 30] [--db path]
```

输出为人读表格（非机器协议）；`review_candidates.py` 是交互式 CLI，接受 `i/r/l/s/q` 输入。三个脚本均无显式退出码约定外的非零退出（未捕获异常即 traceback 退出）。

## 4. 副作用与限制

- 联网调用 OpenAlex / Semantic Scholar 公开 API（只读 GET）；配置 embedding 后另调用其 `/embeddings`。
- 写 SQLite：论文、provenance、反馈、embedding 缓存、抓取状态。可重复运行不重复抓取（`citation_fetches` scope_key 去重）、不丢反馈、中断后可恢复。
- 单源失败降级为 stderr 警告并继续；429/503转为持久主机冷却并抛DeferredRequest（ConnectorError子类）；其它5xx单次等待超过5秒也延后，不截短Retry-After要求。
- 去重为精确键匹配（DOI/OA/S2/标准化标题），不做模糊匹配；跨源无 DOI 的同一论文可能重复入库。
- embedding 未配置时词袋打分质量有限；排序信号仅供人工筛选参考，不代表论文质量。
- 引文扩展只应在人工标记 interesting 后执行；直接对大种子集调用会产生大量 API 请求。
- 非线程安全设计：Store 单连接单进程使用；多进程并发写同一 DB 未验证。
- Semantic Scholar 无 key 时共享限速池可能频繁 429，一次搜索耗时可达数分钟。

## 5. 验证与维护

- 2026-09-18：在源码目录运行 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover tests -v`，Python 3.13.3，12 项通过。覆盖去重键优先级、跨源合并、cosine/词袋打分、OpenAlex 摘要重建、SQLite 去重/反馈/队列/缓存/provenance。
- 2026-09-18：真实 API 验收 `python3 scripts/search_topic.py "OLED triplet exciton" --limit 20`：OpenAlex + Semantic Scholar 双源入库 130+ 篇、去重与打分正常（运行时无 S2 key、无 embedding 配置，走降级打分）。
- 未验证：`review_candidates.py` 交互流程的真实终端会话；配置真实 embedding provider 后的打分质量；S2 有 key 时的限速行为。
- 当前源码结构见 [自动接口快照](INTERFACE.generated.md)。修改接口后必须运行 `python3 ../../../tools/scripts/sync_tools.py update`，按 [all 规则](../../all/RULES.md) 核对说明与使用方并处理待审查记录。

## 2026-10-14 审核修复与接入调整

`expanded_queries(store, topic, max_new=5, top_papers=20, *, current_papers=None, scores=None)` 不再读取全库旧分数，调用方必须传当前波次候选与本主题分数；未传返回空列表。`discovery.loop` 已适配。`embed_papers(store, papers, expected_dimension=None)` 可按主题向量维度过滤；response数量、索引、非空维度和有限数值严格验证，失败保留逐输入占位并按原预算拆批，不缓存错位结果；非法历史缓存留存降级，不自动迁移。

Store初始化仅增建 `identity_conflicts` 表和 `citation_fetches.last_error/retry_at` 两列；冲突保存原输入和命中ID，搜索/引文入口跳过冲突继续其它候选。补DOI保留稳定ID和反馈。引文完成状态按来源保存，失败至少60秒后可重试；旧聚合完成记录不自动重扫。HTTP冷却独立写 `<LITEXP_DB>.http-cooldowns.sqlite3`，支持数字/HTTP-date，构造参数max_rate_limit_retries保留兼容但429改为一次后延后。

登记 consumers 当前为空；主fetch通过 crawler.api 只加载OpenAlex/S2解析器，不调用此工具的引文扩展/embedding/HttpClient网络路径，主生产来源控制仍是 fetch.network.ProviderClient。20项独立离线回归通过，无真实网络调用、向量服务或历史库修复验收。
