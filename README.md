# 可复用工具目录

这里统一登记从现有项目提取的工具，供后续项目查找、接入和维护。当前采用**源码引用模式**：工具的唯一维护位置仍在原项目，本目录保存工具清单、调用说明、源码指纹和接入规范。

首次整理：2026-09-18。本目录没有复制工具实现，也没有统一运行服务；`registry.json` 是登记表，不会自动安装、导入或同步代码。仅把本目录加入 `PYTHONPATH` 不能导入已登记工具。

## 可安装工具包

[OLED 公式整理安装包](distributions/oled-formulas/README.md) 提供 16 个本地 wheel、SHA-256 校验值和安装说明。

## 已有工具

| 工具 ID | 能力 | 调用方式 | 源码位置 | 接入说明 |
| --- | --- | --- | --- | --- |
| `literature_explorer` | 按研究主题跨 OpenAlex / Semantic Scholar 发现文献、去重排序、人工筛选后引文扩展 | Python、CLI | `/Users/xiaoyanhao/project/paper/fetch/crawler/literature_explorer` | [调用说明](tools/literature_explorer/README.md) |
| `codex_desktop_chat` | 原生 Codex App Chat 文本提问，多窗口生成并行、完整收取 | Python、JSON CLI | `/Users/xiaoyanhao/project/paper/codex_desktop_chat` | [调用说明](tools/codex_desktop_chat/README.md) |
| `codex_web_client` | Codex Web GPT 持久队列、MCP 执行与结果验收 | Python、CLI | `/Users/xiaoyanhao/project/paper/codex_web_client` | [调用说明](tools/codex_web_client/README.md) |

## 后续项目怎么用

**只需复制 [all 文件夹](all/README.md) 到新项目根目录，再在新项目执行一次：**

```bash
python3 all/setup.py
```

它会保留项目已有规则，加入根目录 AGENTS.md 联动块，创建或保留 tool-dependencies.json，并登记到中央 projects.json。仅复制文件不会执行安装，首次需要上述一步；之后全局更新会同步公共规则。

开发时先查上表和 [registry.json](registry.json)，按工具卡配置环境、通过项目适配层调用并验证。实际导出/使用关系填写到项目 tool-dependencies.json，不能把模板示例当成已接入。全局命令根据这些声明维护 owner_project/consumers。

完整流程：[跨项目接入与联动](docs/跨项目接入与联动.md)。新增/修改工具前阅读：[工具新增与维护规范](docs/工具新增与维护规范.md)。

从 GitHub clone 的公开仓库要作为新工具接入时，可把 [生成 GitHub 工具接入命令的提示词](templates/让ChatGPT生成GitHub工具接入命令的提示词.md) 发给 ChatGPT；不需要上传本机 tools 文件。ChatGPT 审核指定 commit 后生成一个针对该仓库的可下载 `.command`；脚本在本机运行时验证当前 tools schema，按 Markdown 唯一标记/明确标题插入内容、按 JSON 主键合并登记，再执行全局检查。该文件不能通用于未经审核的新 commit；私有或未推送源码仍需提供给 ChatGPT。

## 已落地的双向链接

`paper/article`、`chatgpt_playwright`、`lifelog`、`oled`、`paper/crawler`、`paper/read`、`paper`、`question` 都已加入 `AGENTS.md` 和 `tool-dependencies.json`。源项目的规则要求：修改已登记接口时，同一任务更新 tools 工具卡、清单、变更记录及受影响使用方；tools 通过 [projects.json](projects.json)、工具的 `owner_project` 和 `consumers` 反向定位项目。

八个项目也已加入 all 公共接入包。当前关系与边界见 [双向联动状态](docs/双向联动状态.md)。

## 全局检查与更新

Mac 可直接运行或双击根目录 [全局更新.command](全局更新.command)，默认检查并同步所有已登记项目。从任意工作目录运行：

```bash
/Users/xiaoyanhao/project/tools/全局更新.command
```

只检查是否有变化、不写文件：

```bash
/Users/xiaoyanhao/project/tools/全局更新.command check
```

等价的跨平台 Python 入口是 `python3 /Users/xiaoyanhao/project/tools/scripts/sync_tools.py update` 或 `check`；Windows 另提供 [全局更新.cmd](全局更新.cmd)，需安装 Python 并调整本机项目路径（本次未在 Windows 验证）。

自动更新范围：各项目 all 公共规则、AGENTS 受管理块、依赖中的当前源码指纹、工具反向登记、三份接口结构快照和 [全局更新报告](updates/latest.md)。新项目会纳入同一流程。源码、工具卡中的业务解释和适配代码仍需开发者审查修改。

**all/RULES.md 已要求：修改接口后必须运行全局 update。** 遇到源码变化，报告保留待审查状态；开发者核对实现、说明与使用方后，用 `accept --tool <id> --note "核对依据"` 登记工具审查，用 `acknowledge --project <项目名> --tool <id> --note "适配核对"` 登记使用方静态核对。完整命令见 [all 使用说明](all/README.md)。普通 update 不会悄悄更新已审查基线或验收日期。

结束前还需运行原有只读检查：

```bash
python3 /Users/xiaoyanhao/project/tools/scripts/check_links.py
```

该只读命令检查源码漂移、漏登记文件、双向关系和路径；全局 check 还检查公共规则与派生文件是否需要同步。命令退出码：0 无待办，1 需更新/审查，2 配置/冲突/权限错误。

## 四项目接口提取评估

已审核 `article`、`chatgpt_playwright`、`lifelog`、`oled` 的主要实现，整理了 20 项接口候选、各项目内部排名与综合排名：

- [四项目接口审核报告（2026-09-18）](audits/2026-09-18-四项目接口审核.md)：源码依据、输入输出边界、提取成本、验证结果及联动方案。
- [接口候选评分与证据 JSON](audits/2026-09-18-接口候选排名.json)：可复算分数及源文件指纹。

审核候选尚未自动登记为可用工具；近期优先考虑论文清洗去重、知识树、论文检索与知识目录读取。已有浏览器调用应先统一完成状态与调度约定。

## 目录结构

```text
tools/
  README.md                         总入口与工具索引
  AGENTS.md                         本目录的维护约定
  registry.json                     源码、接口、指纹和使用方登记
  projects.json                     已登记项目规则与依赖记录的反向索引
  all/                              复制到新项目的唯一接入包
  全局更新.command / 全局更新.cmd     Mac / Windows 入口
  scripts/sync_tools.py             全局检查、同步、首次接入及审查登记
  scripts/check_links.py            只读检查源码基线与双向登记
  updates/                          最近全局报告及模块指纹变化记录
  CHANGELOG.md                      本目录变更记录
  audits/                           项目审核、候选接口与排名
  docs/                             接入流程与维护规范
  tools/<tool_id>/README.md          每个工具的跨项目调用说明
  tools/<tool_id>/INTERFACE.generated.md  自动生成的当前源码结构快照
  templates/                        新工具说明、项目依赖及联动约定模板
```

源码仍在各自项目内；目录中 `tools/<tool_id>/` 当前只存说明。以后需要集中维护代码时，可逐个迁入 `packages/<package_name>/` 并提供安装配置；迁移前先核对使用方，迁移后更新所有登记和导入路径。每个工具始终只有一个权威维护位置。

## 当前验证与边界

见 [CHANGELOG.md](CHANGELOG.md)。源码文件 SHA-256 登记在清单中，用于发现文档可能落后于代码；它不是版本锁定，也不能恢复旧代码。

全局命令按需同步已登记项目，不在后台监听；未安装 Git hook、CI 或定时任务。更新前保存受影响旧文件到 .sync-backups；文件冲突会停止，写入失败会尝试回滚本轮已写入文件。项目自定义规则放在 AGENTS 受管理块之外。原项目源码变更会直接影响使用路径导入的新进程，升级前需主动核对和验证。
