# 让 ChatGPT 生成 GitHub 工具接入命令的提示词

用途：把下面的提示词发给 ChatGPT，只提供 GitHub 仓库地址和目标能力，不需要上传任何本机 tools 文件。ChatGPT 审核公开仓库后，应返回一个可下载的、针对该仓库生成的 macOS `.command` 文件。下载并运行该文件时，它才动态读取并更新本机 `../../tools`。

发送前填写尖括号中的内容。私有仓库或本地有未推送修改时仍须向 ChatGPT 提供对应源码；公开 GitHub commit 则不需要发送本机文件。

```text
请审核下面的 GitHub 仓库，并为我的 macOS 生成一个“下载后双击即可运行”的单文件接入程序。这个程序运行后，要把仓库中适合复用的能力登记进我本机的 tools 工具管理目录。

GitHub 仓库地址：<填写 URL>
要使用的 branch/tag/commit：<填写；不确定时请先分析默认分支并告诉我采用的 commit>
本机 clone 后的预期路径：<例如 ../../example-repo；如果可能变化，让脚本启动时询问或接受拖入路径>
希望提取的能力：<填写；不确定时写“请审核后只选择最适合复用且已经实现的能力”>
预期使用项目：<可选；没有时写“暂时没有使用方，只登记维护方”>
本机 tools 根目录：../../tools

我的 tools 采用 source-reference：工具实现继续留在 clone 的仓库中，tools 只保存工具卡、登记信息、源码指纹、项目关系和更新报告。请不要把第三方仓库源码复制进 tools。

不要要求我上传任何本机 tools 文件。你只分析 GitHub 上指定 commit 的 README、许可证、依赖文件、公开入口、测试和源码。生成的 `.command` 必须在本机运行时读取当前 tools 文件，并在写入前验证下列本地契约；不满足就停止，不能猜测或迁移格式：

- tools 根目录必须存在 `README.md`、`registry.json`、`projects.json`、`CHANGELOG.md`、`all/`、`scripts/sync_tools.py` 和 `scripts/check_links.py`。
- `registry.json.schema_version` 必须为 1，且顶层 `tools` 是数组；工具以 `id` 为稳定主键。
- `projects.json.schema_version` 必须为 1，且顶层 `projects` 是数组；项目以 `name` 为稳定主键。
- 项目关系表是仓库根目录 `tool-dependencies.json`，顶层包含 `project_name`、`project_root`、`registry_path`、`projects_index_path`、`rules_path`、`exports`、`tools` 和 `module_dependencies`；exports/tools 以 `id` 为主键。
- 工具卡路径为 `tools/<tool_id>/README.md`；根 README 的 `## 已有工具` 下是列名为“工具 ID / 能力 / 调用方式 / 源码位置 / 接入说明”的 Markdown 表格。
- 当前采用 source-reference，工具条目至少包含：id、name、summary、mode、source_dir、python_import_root、source_docs、guide、interfaces、runtime、configuration、side_effects、source_version、source_files_sha256、verified_at、verification、known_limitations、consumers、owner_project。首次生成时 `mode` 为 `source-reference`，consumers 只登记已明确提供的真实使用方。

你需要先完成语义审核，再生成文件：

1. 判断哪些能力真正适合跨项目复用。不要把整个仓库机械登记成一个工具，不要登记尚未实现的规划。如果当前没有稳定接口，请直接说明不适合接入，不生成会伪造登记的命令文件。
2. 为每个要登记的工具确定唯一的小写 snake_case tool_id、权威 source_dir 和真实 Python/CLI/HTTP 等入口。写清输入、输出、默认值、错误、超时、并发、配置、依赖、副作用和限制。
3. 核对许可证、Git remote、选定 commit/tag 和需要纳入源码基线的精确文件清单。命令运行时必须再次验证本地 remote 和 HEAD；与审核版本不一致时停止，不能继续写 tools。
4. 设计要嵌入命令文件的确定内容：工具卡、registry 工具条目、README 索引行、CHANGELOG 记录和维护方 exports。当前本机文件由命令运行时读取和合并；实际没有使用方时 consumers 保持为空，不虚构接入。

请使用可用的文件生成能力，给我一个真正可下载的文件，文件名使用：

接入_<tool_id>_到_tools.command

不要只把脚本显示在 Markdown 代码块中。生成的文件必须是 UTF-8、LF 换行，并带可执行权限；如果下载导致权限丢失，说明可运行 `chmod +x 文件名`。

这个 `.command` 文件必须满足以下要求：

- 单文件、macOS `/bin/sh` 可启动；只依赖 macOS 自带工具和 Python 3.10+ 标准库，不要求 jq，不下载依赖，不执行 curl 管道，不使用 sudo。
- 将 tools 根目录固定为 `../../tools`。仓库路径可由预设值、命令行第一个参数或把文件夹拖到 `.command` 上提供；写入前验证 tools 和仓库路径都准确存在。
- 把本次审核产生的工具规格、人工工具卡、README 表格行、CHANGELOG 记录、精确源码文件清单、GitHub URL 和完整 commit SHA 作为常量嵌入 `.command`。不得在运行时调用 ChatGPT、OpenAI API 或其他模型，也不得联网重新生成内容。
- 在本机运行时才使用 Python 标准库读取当前 registry.json、projects.json、README.md、CHANGELOG.md 和仓库关系表。先执行上面的本地契约检查，再根据实际现状规划变更；所以生成命令不需要我预先上传这些文件。
- 验证本地仓库的 Git remote 与你审核的 GitHub URL一致，并验证 HEAD 等于你审核的完整 commit SHA。路径、remote、commit、必要文件或 tools schema 不一致时，以非零退出且不写任何文件。
- 运行前检查 tool_id 没有与 registry 中其他来源冲突。已经由同一 source_dir 登记时应做幂等更新；不能重复追加 README 行、CHANGELOG 段或 registry 条目。
- 默认调用 tools 现有的 `scripts/sync_tools.py install --project <仓库根目录>` 完成项目首次接入，而不是自行覆盖仓库已有 AGENTS.md。然后以结构化 JSON 方式合并仓库 tool-dependencies.json 的 exports。
- 只修改完成本次接入所必需的文件。优先使用“特定位置插入”，不必重写整个文件：Markdown 在明确标题、表格结束处或唯一管理标记之间插入；CHANGELOG 在顶层标题后的最新记录位置插入；新工具卡直接创建新文件。为本工具生成唯一标记 `<!-- github-tool:<tool_id>:begin -->` / `<!-- github-tool:<tool_id>:end -->`，首次运行插入，重复运行只更新该标记块，不能重复追加。
- JSON 文件不能在尾端直接拼接文本。registry.json、projects.json 和 tool-dependencies.json 必须由内嵌 Python 使用 `json.load` 解析，按稳定主键结构化插入或更新，再用 UTF-8、两空格缩进和末尾换行写回。registry 工具按 `id` 合并、projects 按 `name` 合并、exports/tools 按 `id` 合并；遇到同 ID 不同 source_dir、同项目名不同 root 等冲突时停止，不能覆盖。
- README 工具索引优先把新行插入“已有工具”表格的最后一行之后；找不到唯一标题或表格边界时停止并提示重新生成脚本，不能猜位置。CHANGELOG 使用带 tool_id 和审核 commit 的唯一标记块插到 `# 变更记录` 之后；找不到唯一标题时停止。保留所有标记块以外的人工内容和未知新内容。
- 在写入前把每个将修改的旧文件备份到 `../../tools/.sync-backups/github-onboard-<UTC时间>/`，写入采用临时文件加原子替换。任何一步失败时回滚本次已经修改的文件；不碰仓库业务源码。
- 工具卡内容和 registry 的接口语义由你审核后作为确定内容嵌入脚本。源码哈希由脚本运行时只对你审核列出的精确相对路径计算；发现清单外新增的公开代码/说明文件时停止并提示重新审核，不能为消除告警盲目纳入所有文件。
- registry 中记录 GitHub URL、审核 commit/tag、许可证、验证范围和未验证事项。不能把 ChatGPT 阅读源码写成真实运行验收。
- 可以运行你确认安全且与接口直接相关的只读/临时测试；不得自动安装依赖、使用密钥、调用付费 API、发送消息、操作登录态、写业务数据库或启动长期服务。未运行的测试明确记录为未验证。
- 完成登记后依次运行：
  `python3 ../../tools/scripts/sync_tools.py update`
  `python3 ../../tools/scripts/check_links.py`
  只要任一命令返回非零，脚本就应显示 tools/updates/latest.md 的位置并以非零退出。脚本不得自动执行 accept 或 acknowledge；首次登记的基线必须来自本次已审核且通过 commit 校验的文件，后续漂移仍交给原流程审查。
- 结束时打印：登记的 tool_id、权威源码目录、commit、修改文件、验证命令、未验证事项和最终检查结果。日志中不得打印密钥或环境变量值。
- 脚本应能重复运行：仓库和 tools 没变化时不产生重复条目；发生人工冲突时停止并保留现场，不静默覆盖。

生成后，请同时给出不超过 8 行的使用说明，说明下载位置、首次运行、如何把仓库文件夹拖到命令上、退出码 0/1/2 的含义，以及该文件只适用于你审核过的 commit。不要声称你在我的电脑上实际运行过这个文件。
```

## 需要提供给 ChatGPT 的内容

公开仓库只需提供 GitHub URL、明确 branch/tag/commit、目标能力和预期本机 clone 路径，不用上传任何 tools 文件。ChatGPT 根据上述稳定契约生成脚本，脚本运行时读取当前本地状态。

私有仓库、GitHub 无法访问的仓库或本地存在未推送修改时，ChatGPT 无法仅靠 URL 审核实际源码，这种情况仍需提供仓库压缩包或相关源码。若本地 tools 的 schema/version 或 README 表格结构与契约不符，生成的命令必须安全停止；更新本提示词后重新生成，不能让旧命令自行猜测新格式。

生成的 `.command` 是一次性接入程序，只适用于 ChatGPT 审核过的仓库版本。以后工具源码更新仍使用 tools 原有的 `全局更新.command`、`accept` 和 `acknowledge` 流程。
