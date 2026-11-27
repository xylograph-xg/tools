# OLED 公式工具安装包

当前源码只通过 App 派发。[旧网页分支处理方法](旧网页分支处理方法.md)记录退役前的故障处置。下列 wheel 是退役前冻结的发行版本。

此目录收集当前 paper 工作区的 OLED 公式整理包，以及按 Python 包依赖递归解析出的全部本地发行包。16 个 wheel 的版本在文件名中，文件摘要见 [SHA256SUMS](SHA256SUMS)。开发源码见[源码目录](oled_formulas/README.md)，项目运行目录见 [paper 工作区](../../paper/WORKFLOWS.md)。

| 入口 | 用途 |
|---|---|
| paper-oled-formulas | 公式页取证、裁图、LaTeX 与 Python 结果检查、按篇发布，以及公式队列控制入口 |
| codex-web-client | App 任务提交、并行领取、回执检查与收取 |
| paper-codex-desktop-chat | 桌面聊天接口与附件打包 |
| 其余 13 个 wheel | 上述入口依赖的 paper 内部组件，由 pip 一起解析 |

## 安装和验证

在本目录执行以下命令。使用 Python 3.11 或更高版本；本机验证版本为 Python 3.13。pip 从此目录安装本地包，从配置的软件源解析 PyMuPDF、Pillow、Playwright 等第三方依赖。

```sh
shasum -a 256 -c SHA256SUMS
python3.13 -m venv ~/venv/oled-formulas
~/venv/oled-formulas/bin/python -m pip install ./wheels/*.whl
export PAPER_WORKSPACE_ROOT="$(cd ../../paper && pwd)"
~/venv/oled-formulas/bin/python -m pip check
~/venv/oled-formulas/bin/python -m oled_formulas --help
```

公式入口从 PAPER_WORKSPACE_ROOT 找到工作区清单、配置及队列。真实派发另依赖已配置的 Codex Web GPT 桌面服务。旧 Chrome 接口另依赖外部 web_gpt。安装目录不含账户状态、原始 PDF、模型权重或第三方 OCR 候选。2026-11-27 在新虚拟环境安装后检查了依赖、CLI 帮助和 18 项公式回归测试。

公式整理包 1.0.0+review.1 包含逐页矛盾隔离、缺排版字段的有证据裁图，以及可执行 Python 的映射复核。该包通过独立安装环境的 19 项相关回归和 pip 依赖检查。

公式包 1.0.0+review.2 及客户端 1.3.0+proprobe.1 默认从 Extra High 开始，每三小时抽取一个 App 窗口的菜单。
