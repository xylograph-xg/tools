# OLED 行间公式整理

本项目处理已准入 OLED 文献的完整 PDF 页面。它把多篇论文的页图与文字坐标打成 ZIP，当前通过 Codex Web GPT 临时聊天转录行间公式，默认 GPT-6.2 Sol Extra High，支持 High 回退和 Pro 可用性检查，按篇保存公式、代码与可回查的原文路径。单篇论文可以跨多个批次，覆盖范围见结果的 `pages_checked`。

## 在哪里查看结果

在任务面板的“公式整理”行查看 Codex Web GPT 的活动回合、批次进度和结果目录。数据根目录由 `infrastructure/data/formula-only-control.json` 的 `folder` 指定。以下路径相对于该数据根目录。

| 文件 | 用途 |
| --- | --- |
| `display-equations/by-paper/<paper_id>.json` | 按篇查看原文路径、原文哈希、已检查页、公式和待复核项 |
| `display-equations/batches/<六位批次号>/batch.zip` | 重看实际发送的页图、布局与清单 |
| 同批次的 `attempt.json`、`response.txt` | 核对实际模型、提交回执与网页原回答 |
| 同批次的 `formulas.jsonl`、`equations/` | 逐行读取公式记录，对照原图裁切。Python 表达式仅在可转写时提供 |
| `display-equations/queue.sqlite3`、同目录的 `status.json` 和 `window-observation.json` | 持久队列、后台状态与最近一次网页观测 |

## 运行入口

在工作区根目录使用项目的网页 Python 环境。查看命令帮助可运行 `infrastructure/environments/web/bin/python -m oled_formulas --help`。面板的“启动”和“暂停”分别对应 `python -m oled_formulas start` 和 `python -m oled_formulas pause`。启动请求交给原有的 web-cards 服务执行。

生产服务持有共享锁时通过 `oled_formulas.api.run(config)` 接续登记队列。公开的 `enabled(config)` 检查启用状态和原任务的暂停记录，`control_pilot(config, start)` 提交启停。每小时的 Codex 巡检读取同一队列和回执。

## 当前源码

App 派发与回执收取见 [app_queue.py](app_queue.py)，模型菜单检查见 [pro_menu.py](pro_menu.py)。[formula_queue.py](formula_queue.py) 负责排队和发布，[formula_only.py](formula_only.py) 维护启停、范围和原文校验。[display_equations.py](display_equations.py)、[formula_pilot.py](formula_pilot.py) 和 [formula_results.py](formula_results.py) 处理页图、原回答和按篇结果。[legacy_receipts.py](legacy_receipts.py) 只读取历史上传及释放记录，供 App 判断批次是否曾发送。

旧 Chrome 派发、收取和故障恢复的处理方法见[历史归档](../旧网页分支处理方法.md)。
