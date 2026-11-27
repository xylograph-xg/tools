# 2026-11-27 工具目录整理

工具说明、OLED 安装包、登记检查和公开导出各占一个一级目录。项目从 AGENTS.md 直接进入工具说明，首次登记与后续更新均已取消 all 分发。同步报告、历史审核及回滚备份迁入 ~/process/tools/。

## 2026-11-27 可迁移路径与公开源码发布

工具清单与项目索引按所在目录解析路径，生成相对链接，兼容已有绝对路径。按五个已提交项目导出公开源码，独立校验公开版索引。见[发布流程](public_export/README.md)。

## 2026-11-27 已删除项目的登记清理

从 projects.json 移除 chatgpt_playwright、lifelog、oled 和 question 的项目入口（规则与依赖清单）。从 codex_desktop_chat 使用方移除 chatgpt_playwright；从 paper 的模块依赖移除该项目提供的 core、qwen、settings、submission、capacity。原项目路径均已删除。历史联动状态中的 chatgpt_playwright 与 oled 相互引用已撤下；旧状态和关系两端可在清理前的 tools 提交 7054d91、paper 提交 3abb8ea 查证。paper 旧代码的 web_gpt 导入在其外部依赖中标记为缺失。

## 2026-11-27 OLED App 模型菜单

受保护的分档派发使用 pro_first=True。allow_pro=False 只在 GPT-6.2 Sol Extra High、High 中按额度选择；allow_pro=True 保留 GPT-6 Pro 优先。明确未发送的模型专属额度错误允许原批继续，其他不确定提交存入复核。

## 2026-11-27 OLED 公式验收优化

[集中安装目录](oled-formulas/README.md) 的公式包升级为 1.0.0+review.1。新增同页冲突隔离、缺字段的裁图待核和代码映射复核。

## 2026-11-27 集中 OLED 公式工具安装包

新增 [OLED 公式安装目录](oled-formulas/README.md)，收录公式整理和全部本地包依赖，通过全新环境安装和公式回归验证。

## 2026-11-27 移除 web_gpt 和 oled_knowledge_tree 登记

移除两项中央登记、工具卡和接口快照，同步维护方及使用方的登记。原项目继续维护源码和业务适配。

## 2026-11-27 OLED 使用 Codex Web GPT

2026-11-27 · codex_web_client 1.3 增加五个定向并行位置、同批防重与并发额度冷却保护。


2026-11-27 · codex_web_client 1.2 增加受保护任务的 Pro、Extra High、High 额度回退及逐次派发回执。


1.1.0 支持冻结有序图片、指定任务领取及发送前守卫。OLED 新批次使用真实 App 队列与专用工单，面板显示 App 原生窗口。

## 2026-11-27 Codex Web GPT Python 接入

新增 codex_web_client 1.0.0。通过真实 Web 任务验证读取、结构化结果核对与同编号防重。

## 2026-10-13 paper物理子项目接口整理

- codex_desktop_chat新增可选api.py/版本化interface.json及独立构建/测试/完整README；原工具11份基线实现与原签名不变，源码位置不变。
- paper跨项目调用改为公开API；article退役旧探索器/制卡应用，仅保留web_gpt适配，消费者登记和调用路径同步。
- 1756项离线回归、305个实际出口身份检查、17个独立构建已通过；后续变动按审查日志记录。本轮没有新的网页/桌面Chat生成、上传或科学验收。

# 变更记录

## 2026-10-09：制卡上传等待与ZIP回执修复

- 权威web_gpt/core.py将上传进度等待沿用调用者timeout，默认60秒；paper传180秒。全部进度条均核对，读取异常阻断发送。
- paper有限重试核对精确原提示＋ZIP通用说明及实际提示/原包/回答指纹，不放宽未知提交或次数限制。
- 61项paper隔离测试通过；真实已有会话只读核对发现4份空最终正文，保留原会话、不重发。本轮没有新真实ZIP上传测试，科学读取仍待验收。

## 2026-10-06：question 一键生成与 web_gpt 输入恢复

- question 将裁剪后的保存、编译、依赖回答、检查与导出合并为一键操作；章节默认保留，关联概念/框架随范围安排，明确排除的前置不自动恢复，执行前显示规模与依赖缺口。
- 修复权威 web_gpt/core.py 的空/不完整剪贴板粘贴，提交前通过 insert_text 重写一次并沿用完整性校验，不放宽 High、不重复提交。原接口说明及工具卡同步。
- question 37项本地测试、web_gpt 17项隔离Chrome测试通过；article/paper调用契约静态兼容，本轮未运行它们的真实生成。

## 2026-10-06：迁移后 tools 与 all 路径复核

- 确认中央根目录为 ../tools；3 个权威工具、7 个登记项目及使用方路径存在，article/crawler/read 位于 paper 下。
- 修正 web_gpt 工具卡和双向联动状态中残留的 project/article 链接，补全七项目入口与 README 当前同步范围。
- 运行全局 update、check 与 check_links.py；同步所有已登记项目的 all 公共文件与规则块。历史审核、备份及业务数据中的来源路径保留；未进行浏览器发送或联网业务验收。

## 2026-09-24：由 ChatGPT 生成仓库专用的一键接入文件

- 新增 `templates/让ChatGPT生成GitHub工具接入命令的提示词.md`。用户向 ChatGPT 提供 GitHub URL、明确 commit 和当前 tools 管理文件；ChatGPT 先审核接口，再生成可下载的、仅适用于该仓库版本的 macOS `.command`。
- 生成文件被要求验证 remote/HEAD、备份和原子写入，幂等维护工具卡、registry、README、CHANGELOG 与维护方 exports，然后调用现有全局 update 和只读检查；不复制仓库源码，不自动 accept/acknowledge。
- 文件更新采用明确位置插入：Markdown 使用工具专属 begin/end 标记块，README 表格按唯一边界插入，CHANGELOG 插在顶层标题之后；JSON 使用 Python 解析后按 id/name 主键合并，禁止在尾端拼接 JSON 文本。重复运行只更新自己的标记块。
- 提示词升级为零上传 tools 文件：ChatGPT 只审核公开 GitHub commit，并把确定的工具规格嵌入命令；命令在本机运行时读取 registry/projects/README/关系表，校验 schema_version=1 和固定结构后再合并。私有仓库、不可访问源码或未推送改动仍需另行提供。
- 移除先前误解需求后创建的固定“接入后更新”入口。固定入口只能在人工登记完成后同步，不能独立完成一个新 GitHub 工具的语义接入。

## 2026-09-18：登记 literature_explorer 文献发现闭环工具

- 新增第三个登记工具 `literature_explorer`（source-reference）：输入研究主题，跨 OpenAlex / Semantic Scholar 搜索、去重、相关性排序产出候选论文池；人工标记 interesting 后自动引文扩展。纯标准库零依赖，权威源码 `~/Desktop/crawler/literature_explorer`。
- crawler 项目完成 all 接入（tool-dependencies.json 声明 exports=[literature_explorer]、AGENTS.md 受管理块、projects.json 登记）。
- 新增工具卡 tools/literature_explorer/README.md、registry.json 条目（25 个源文件指纹）与 README 工具索引行。
- 验证：源码目录 12 项 unittest 通过（Python 3.13.3）；真实 OpenAlex+S2 搜索验收一次（无 key、词袋降级打分，入库 130+ 篇）。交互式 review 会话与真实 embedding provider 未验证。

## 2026-09-18：all 一次接入与全局检查更新

- 新增 all/ 接入包：复制到新项目后运行一次 all/setup.py，自动合并根 AGENTS 公共规则、创建/保留依赖记录并登记中央项目索引。
- 新增 scripts/sync_tools.py 及 Mac 全局更新.command、Windows 全局更新.cmd；提供只读 check、全局 update、首次 install、源码审查 accept 和使用方静态核对 acknowledge。
- 公共规则要求接口修改后调用全局 update。同步范围包含 all 公共文件、AGENTS 受管理块、当前源码指纹、维护方/使用方反向登记、接口结构快照和全局报告；原有业务源码保持单一维护位置。
- 普通更新不刷新已审查源码基线或验收日期。源码变化保留 needs_review；显式登记审查会保存历史验证信息，使用方需另行核对。module_dependencies 的指纹只作变化观察，不当成正式接口验收。
- 更新前备份元数据，防止并发更新，检测本地公共文件修改，写入失败尝试回滚；新项目原有自定义规则保留。
- 验证：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`，20 项通过。覆盖异地启动新项目接入、只读检查、重复运行、源码漂移/审查/使用方核对、规则分发冲突、并发改动和失败回滚；所有测试使用临时目录，不调用业务接口。Windows 入口未实测。
- 实际部署：在 /private/tmp 运行 tools/全局更新.command，首次同步 31 个文件，四项目均完成 all 接入；随后运行同入口 check，待同步文件为 0。`python3 scripts/check_links.py` 通过：4 项目、2 工具、14 个源码基线文件、2 条模块引用；90 个当前文档链接及四个已安装接入包核对通过。article 仍仅静态核对，未执行浏览器生成。

## 2026-09-18：落地四项目双向联动规则

- 在 article、chatgpt_playwright、lifelog、oled 各新增 AGENTS.md 与 tool-dependencies.json；接口变更时要求同一任务同步 tools 和受影响使用方，结束前执行只读检查。
- 新增 projects.json、工具 owner_project 及 article → web_gpt 的 consumers 反向登记；旧 OLED/浏览器模块依赖单独记录为 module_dependencies。article 仅 source_inspected，真实生成未验收。
- 新增 scripts/check_links.py，检查源文件漂移、新文件漏登记、维护方/使用方双向记录、使用方基线及路径；不调用业务接口、不自动刷新摘要、不安装后台监听或 Git hook。
- 首次检查发现 web_gpt 基线实际已漂移：3 个旧文件变化，新增 settings.py、__main__.py。核对全部 Python 源码后，更新工具卡的模式/模型/精确 High/verify_settings/CLI 说明、源码基线和 article 依赖快照；部分回答等待超时的旧限制仍存在。
- 同步 README、联动规范、新增规范、工具卡及模板。历史 audits 保留原快照；本次不修改四项目业务实现、不执行真实网页生成。
- 验证：9 项校验器回归测试全部通过，涵盖源码变化、新文件遗漏、双向登记缺失、过期使用方快照与错误配置。异地执行实际联动检查通过：4 项目、2 工具、14 个基线文件、2 条模块依赖；静态接入状态单独提示。

## 2026-09-18：四项目接口提取审核

- 审核 article、chatgpt_playwright、lifelog、oled 当前主要实现，新增 20 项候选的项目内/综合排名、五维评分、源码证据与分批提取建议；报告入口加入 README。
- 记录 article 已接入 web_gpt 且默认开启摘要补全/卡片生成、OLED 当前配置使用网页模型比较、浏览器核心分叉、材料检索预算可超限及 LifeLog 数据服务未分离等边界。
- 本次 article 37 项测试、OLED 摄入/语义差分/更新历史/桥接 55 项测试通过。LifeLog TypeScript 无输出检查及纯函数抽查通过；chatgpt_playwright 完成 7 组纯逻辑抽查。
- 同日知识树 12 项验证记录通过源码指纹核对继续有效。没有执行真实外部 API 搜索、模型生成或 Supabase 读写；OLED 应用测试使用临时知识库副本。
- 只新增审核资料，未修改四项目源码；候选尚未作为已实现工具加入 registry，已有调用方仍需完成正式接入登记。

## 2026-09-18：建立统一工具目录

- 以源码引用模式登记 `web_gpt` 和 `oled_knowledge_tree`；工具实现仍由原项目维护。
- 新增总入口、两个跨项目调用说明、接入与联动流程、新工具维护规范、本目录 AGENTS.md 及三个使用模板。
- 清单保存源路径、真实接口、依赖/副作用、文件 SHA-256 和验证范围；使用方尚未登记，`consumers` 为空。
- 明确项目侧依赖记录与目录侧 consumers 的双向登记流程；同步为维护约定，目前没有自动监视或复制机制。
- 核对源码后记录 `web_gpt` 原说明差异：部分等待超时只警告或返回现有文本，不能保证完整回答或全流程硬超时。未修改上游实现。

实际验证：

- 在 `~/Desktop/oled` 执行 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest knowledge_tree_tool.test_tool -v`，Python 3.13.3，12 项全部通过。覆盖算法、异地 CLI、本机 HTTP、数据指纹和当前正式知识库。
- `web_gpt` 仅静态核对函数签名、配置与等待/浏览器逻辑；未启动浏览器、发送消息或上传附件，因此尚未确认真实页面兼容性。
- 从知识树调用说明提取完整 Python 示例，在临时目录运行成功，返回 `status=ok`、32 个节点；此数量仅为当前数据下的验证结果。
- 检查两个 JSON 文件可解析、14 个本地文档链接有效、5 个 Python 示例片段语法正确、12 个源文件摘要与登记一致，两个包的导入根均存在。

待后续实际接入时处理：填入使用方和接入验证记录；根据需要建立版本化发布；改进 web_gpt 的超时/完整性契约后再依赖其严格保证。

- 2026-10-04：源码审查 web_gpt。迁移核对：仅调用说明.md 中 Desktop 路径改为 project；备份哈希与原基线一致，Python 实现未变，目标包存在，未运行浏览器生成。（命令未执行业务验收。）

- 2026-10-04：源码审查 oled_knowledge_tree。迁移核对：仅 README.md 路径变化，备份哈希与原基线一致，核心实现未变；新目录 CLI 查询 TADF 成功，未验证其他业务服务。（命令未执行业务验收。）

- 2026-10-04：使用方核对 article → web_gpt。article/src/web_gpt_adapter.py 默认导入目录已改为 project/chatgpt_playwright，目标包存在，适配代码语法通过；仅静态路径核对，未发送浏览器消息。（命令未执行业务验收。）

## 2026-10-04 项目目录迁移

所有桌面项目和资料移至 `~/project`；同步固定导入路径、工具登记、项目依赖、公共规则和现行说明。知识树 CLI 读取验证成功，浏览器生成未验收。

## 2026-10-05 paper 统一编排层

article、crawler、read 当前目录迁至 project/paper 下，登记路径与 literature_explorer 工具卡同步。新增 paper 使用方，以模块关系引用 crawler 连接器、read 处理器和 article 数据 schema，未新增公共工具导出，未修改原有工具函数。统一流程禁用网页 GPT，使用本地 Ollama。静态核对与离线测试完成，真实网络/模型验收范围由 paper/docs/重构验收记录.md 记录。

## 2026-10-05 paper PDF 多来源后备获取

paper 接入固定提交 fetchpdf 的独立公开 HTTP 获取器；项目内保存上游 MIT 源码、依赖锁和外部依赖记录。未修改已登记公共工具接口，registry 与工具卡无需重新定义。9 篇待办真实重试未新增 PDF；公开对照 PDF 通过 Crossref 获取并校验。Unpaywall 无邮箱尚未启用，学生 Cookie、浏览器和外部 LLM 获取关闭。根目录 23 项测试通过；详细证据见 ../paper/docs/重构验收记录.md。

## 2026-10-05 paper durable-v2 后台修复

paper 内部编排增加持久待下载池、逐查询游标、PDF身份与版本核验、失败隔离、独立获取/阅读worker及Python进程监督。用户要求在现有队列完成后切换，不打断进行中任务。未修改 crawler/read/article 公共接口或导出定义。44项离线测试通过；实际升级激活状态见 paper/data/handover.json，验收说明见 paper/docs/后台平滑升级.md。

## 2026-10-05 paper 接入网页卡片评审

paper 新增 pipeline/web_feedback.py，复用 article 的 gpt_session 与权威 web_gpt 工具，不修改工具源码。三类样本串行上传，保存回答、评分、实际模型设置、会话地址、附件指纹与现场截图；不确定提交后禁止盲目重发。使用关系已登记并全局同步，4 项离线测试与 check_links 通过。专用 Chrome 连接检查成功；真实附件评审尚未完成，保持 source_inspected，不标记生成验收通过。

## 2026-10-05 web_gpt 网页控件兼容

在唯一权威 settings.py 中兼容新版 Chat/Work 按钮、模型菜单和强度视图，并处理按钮加载延迟；固定模型与发送前模式/强度检查不放宽。原 12 项离线回归通过，真实网页模型检查、四个附件上传及首轮评审提交已确认。paper 自动衔接进程已触发；回答未完成前不标记完整网页生成验收。使用方 paper/article 适配需按更新后的指纹重新登记核对。

- 2026-10-05：源码审查 web_gpt。已核对 settings.py 新旧模式控件与模型/强度菜单适配及 paper/article 使用边界；原12项离线回归通过，真实 Chat/GPT-5.6 Sol/Medium 设置检查、四附件上传与首轮提交通过，完整回答仍待完成。（命令未执行业务验收。）

- 2026-10-05：使用方核对 article → web_gpt。静态核对 article gpt_session 仍使用 ChatGPTWeb(new_chat=True,thinking_high=False) 与同样同步返回契约；原12项设置/发送保护回归通过，新控件兼容不改变接口。article业务卡片生成未执行。（命令未执行业务验收。）

- 2026-10-05：使用方核对 paper → web_gpt。paper三类评审复用原锁和同步接口，真实设置、四附件上传、首类请求提交已确认；5项反馈保存/异常离线测试通过，完整回答和其余两类仍待完成。（命令未执行业务验收。）

同日追加：修复 core.py 新版回答正文/停止按钮定位，__init__.py 首段等待遵循调用者参数。保留旧页面与未完成回答的边界。paper 首类真实反馈已从原请求恢复并保存，得分56.45/100，未通过；其余两类正在继续。新增 tests/test_web_gpt_modern.py 三项回归，原测试支持通过环境变量使用现有 Chrome。

- 2026-10-05：源码审查 web_gpt。审查settings新旧菜单兼容、core新版assistant正文和停止按钮、首段等待采用answer_timeout；旧版12和新版3项本地回归通过，paper首类四附件实际提交并从同一请求恢复有效反馈56.45分，其余样本尚待完成。（命令未执行业务验收。）

- 2026-10-05：使用方核对 article → web_gpt。静态核对gpt_session同步接口和锁仍兼容；首段等待现在使用调用者answer_timeout，完整返回仍由使用方验证。article生成未执行。（命令未执行业务验收。）

- 2026-10-05：使用方核对 paper → web_gpt。paper六项反馈验证测试通过，首类真实上传提交及原请求反馈恢复完成，无重复发送；其余两类自动继续，未标全部完成。（命令未执行业务验收。）

- 2026-10-05：web_gpt 已有 /c/ ChatGPT 专用菜单验证兼容；新增已有模式组缺失接受与通用菜单拒绝回归。paper 三类真实评审反馈全部留存，格式失败在原会话修正，不重复上传。

- 2026-10-05：源码审查 web_gpt。核对settings已有/c会话ChatGPT专用菜单识别，通用选择模型仍拒绝；旧版12与新版5项本地测试通过。paper三类真实附件反馈均已留存，第二类在原会话重取JSON格式，无重复上传；新卡片第二轮质量尚未验收。（命令未执行业务验收。）

- 2026-10-05：使用方核对 article → web_gpt。静态核对gpt_session的同步构造、锁、实际设置验证与ask接口，已有/c菜单修复兼容，无新增发送；article文章生成未运行，paper三类评审不能替代article业务验收。（命令未执行业务验收。）

- 2026-10-05：使用方核对 paper → web_gpt。paper三类真实附件评审和原会话格式恢复已留存；v4完成事件监听复用gpt_session串行锁和严格设置验证，独立单轮任务自动续接，不改变普通抓取。新版卡片及第二轮评分仍待完成。（命令未执行业务验收。）

- 2026-10-06：使用方核对 question → web_gpt。2026-10-06：核对 ChatGPTWeb 新建独立会话、High设置验证、ask返回文本与异常语义；question 保存原文、材料指纹与不确定状态，13项离线测试及CLI示例闭环通过。未连接真实浏览器或发送研究请求，生成质量尚待验收。（命令未执行业务验收。）

- 2026-10-06：源码审查 web_gpt。核对core.py仅在提交前粘贴检查失败时复用_retype/insert_text一次，失败仍拒绝发送；原调用说明、工具卡已同步，签名、High和提交前verify保持。question37项本地回归与web_gpt原17项隔离Chrome回归通过；article/paper同步ask方式兼容，未运行本轮真实综述生成。（命令未执行业务验收。）

- 2026-10-06：使用方核对 article → web_gpt。2026-10-06：核对本项目同步ChatGPTWeb/ask调用与core提交前输入恢复兼容；公开签名及模型High策略未变，17项隔离Chrome回归及question37项本地验证通过，本项目真实业务生成本轮未跑。（命令未执行业务验收。）

- 2026-10-06：使用方核对 paper → web_gpt。2026-10-06：核对本项目同步ChatGPTWeb/ask调用与core提交前输入恢复兼容；公开签名及模型High策略未变，17项隔离Chrome回归及question37项本地验证通过，本项目真实业务生成本轮未跑。（命令未执行业务验收。）

- 2026-10-06：使用方核对 question → web_gpt。2026-10-06：核对本项目同步ChatGPTWeb/ask调用与core提交前输入恢复兼容；公开签名及模型High策略未变，17项隔离Chrome回归及question37项本地验证通过，本项目真实业务生成本轮未跑。（命令未执行业务验收。）

2026-10-06：web_gpt独立CDP标签页、submit/collect及跨进程提交锁；question按依赖并联，默认2上限4；兼容原ask，真实并发待验收。

- 2026-10-06：源码审查 web_gpt。核对独立CDP标签页、submit/collect匹配待收取请求、全局提交锁与原ask兼容。question41项离线测试（双进程实际重叠、依赖时序、collect不持锁、独立页），权威原17项隔离Chrome回归通过；真实账号并发尚未验收。（命令未执行业务验收。）

- 2026-10-06：使用方核对 question → web_gpt。适配submit/collect、High与多进程依赖调度；41项本地测试通过，不确定请求禁止自动重发。当前旧作业未中断，真实并发尚未验收。（命令未执行业务验收。）

- 2026-10-06：使用方核对 article → web_gpt。静态核对paper/article/src/web_gpt_adapter.py仍使用ChatGPTWeb(new_chat=True,thinking_high=False)及同步ask；签名兼容，现会话改独立CDP页，提交自动使用公共锁。原项目锁保留；未运行真实业务。（命令未执行业务验收。）

- 2026-10-06：使用方核对 paper → web_gpt。静态核对pipeline/web_feedback.py经article.gpt_session串行多轮ask含files与answer_timeout，兼容分阶段内部实现；未启用paper并联，未运行真实附件评审。（命令未执行业务验收。）

2026-10-06：question默认并行3，可选3–5；同级先最少批次再均分，依赖分级与批间等待。公共web_gpt代码及签名未变。

2026-10-06：question自动关闭原文已保存且验收通过的任务标签页，失败/不确定保留；公共web_gpt源码与退出契约不变。

2026-10-06：question多研究共享3–5名额、按提问顺序优先、自动全量大纲研究；大输入完整文本附件；公共web_gpt源码不变。

- 2026-10-06：使用方核对 question → web_gpt。question共享研究名额池、按创建顺序优先、自动规划至全量导出；原deep/shallow保留，长输入完整附件，58项本地测试及隔离Chrome模拟交互通过。真实双研究生成已启动，整体及长附件收取未验收；旧研究深度修正待用户授权。权威工具代码和签名未改变。（命令未执行业务验收。）

2026-10-06：question保守本地恢复JSON反斜杠/渲染引用引号，保留原文及哈希；9项实际恢复后关页，截断仍拒绝，不重发。

## 2026-10-06 paper 12:46共享模块整改

read权威证据准备、实际输入/引文核验、结构化生成及原子写入接口与paper/article适配同步；两端说明和模块引用记录已维护，global update及check_links通过。246项本地回归和隔离浏览器验证完成，登记工具接口未改变，外部网页GPT验收仍未完成。详见[模块适配核对](../../process/tools/updates/2026-10-06-paper-1246-module-review.md)。

最终复验更新至250项（65.068秒）；本地源码/状态备份和逐项证据已保存。登记工具接口和外部验收状态不变。

- 2026-10-06：使用方核对 paper → web_gpt。已核对 submit/collect 与 ask 公开接口，paper 消费端恢复四篇明确授权诊断送审、SHA 去重和不确定提交保留；43 项回归通过，实际 PRB 网页已收到提示并生成中，科学质量及完整反馈尚未验收。（命令未执行业务验收。）

- 2026-10-07：web_gpt权威core隐藏历史正文过滤、新会话空白确认及首次停止按钮30秒上限；签名不变，21项隔离Chrome回归通过。paper新增评审URL归属拒绝并恢复同一5页网页卡片明确授权评分；真实新报告待收取，其他使用方仅静态兼容核对。

- 2026-10-07：源码审查 web_gpt。审查权威core可见回答过滤、新会话空白确认、首次停止按钮等待上限30秒；原17项及新增4项隔离Chrome回归共21通过；paper实际四附件已上传且新请求生效，报告待收取；公开ask/submit/collect签名不变，其他使用方仅静态兼容核对。（命令未执行业务验收。）

- 2026-10-07：使用方核对 paper → web_gpt。paper仍复用article.gpt_session与同步ask；新ANSWER可见过滤同步用于review_tabs，评审跨材料URL拒绝保持；11项反馈/关页回归通过，真实四附件新请求已生效且唯一标识在新URL可见，正式报告待收取。（命令未执行业务验收。）

- 2026-10-07：使用方核对 article → web_gpt。静态核对article/src/web_gpt_adapter.py仍用ChatGPTWeb(new_chat=True,thinking_high=False)，ask签名兼容；共享会话隔离/可见正文修复生效，现有已加载进程不会追溯升级；未运行article新业务生成。（命令未执行业务验收。）

- 2026-10-07：使用方核对 question → web_gpt。静态核对question/src/web_gpt_adapter.py仍用ChatGPTWeb(new_chat=True,thinking_high=True)及匹配submit/collect；公开签名、High及提交锁保持，回执计数改为可见正文；现有已加载进程不追溯升级，本轮未运行question业务。（命令未执行业务验收。）

- 2026-10-07本次paper真实核验完成：网页5页卡片纠正评审83.55分、0critical、归属标识/哈希/URL匹配，评审页已关闭；科学未通过，其他使用方只做静态适配核对。

## 2026-10-07 web_gpt 显式 Qwen 网页选项

新增 create_session/provider、Qwen独立CDP原生思考、精确模型、附件回执与分阶段收取；GPT默认和原接口保留。paper/article适配和question兼容核对同步；权威说明、工具卡与registry追加配置/副作用/验证边界。国际站Free合成三附件已从原页首次发送并完整收取；当前科学循环仍GPT，国内站/科学质量/账号并联不宣称验收。最终测试、版本指纹与不确定页面留存见paper/data/interface_changes/20261007_qwen。

用户追加提取后自动关闭：Qwen在成功收取后的with退出时按唯一URL、正文和完成状态自动close；未知/未收取页保留，失败仅记录不重发。Qwen16项隔离回归通过。真实旧页补关时CDP返回零页面且连接失败，未重启浏览器或宣称已实际补关。

- 2026-10-07：源码审查 web_gpt。核对权威factory默认GPT与旧签名保持；Qwen原生思考/精确模型、附件回执、单次提交、完整收取、退出核验关页。GPT21项及Qwen16项隔离回归、paper23项通过；国际站Free新会话三附件实际完整收取。国内站/科学质量/真实自动关页未验证；真实补关时CDP零页面且连接失败，未重启或重发。原说明、工具卡、registry及article/paper适配已同步，question静态兼容核对。（命令未执行业务验收。）

- 2026-10-07：使用方核对 paper → web_gpt。paper session_factory经article边界显式选择Qwen，默认GPT和现有科学任务不迁移；21项反馈/关页/限额和2项provider回归通过，Qwen国际站合成三附件真实收取；Qwen退出自动关页隔离验证，真实关页未验收。（命令未执行业务验收。）

- 2026-10-07：使用方核对 article → web_gpt。article默认ChatGPTWeb(new_chat=True,thinking_high=False)保持；显式Qwen转create_session并传精确模型/site/原生思考。两项适配回归通过；未运行article真实业务。（命令未执行业务验收。）

- 2026-10-07：使用方核对 question → web_gpt。静态核对question适配器直接调用ChatGPTWeb(new_chat=True,thinking_high=True)及submit/collect，原签名、High和退出行为保持；未启用Qwen或运行真实业务。（命令未执行业务验收。）

- 2026-10-07：源码审查 web_gpt。追加核对CLI：Qwen smoke完整提取后不另导航空白页，保留已收取指纹供退出核验关页；GPT smoke原新会话行为保持。语法通过，其余源码及16项Qwen/21项GPT回归结果不变。（命令未执行业务验收。）

- 2026-10-07：使用方核对 paper → web_gpt。追加仅CLI Qwen测试退出关页，不改paper显式provider调用和现有GPT科学任务；先前23项消费端回归保持。（命令未执行业务验收。）

- 2026-10-07：使用方核对 article → web_gpt。追加CLI Qwen测试退出关页与article会话边界无关；原默认GPT和显式Qwen适配已核对，两项回归保持。（命令未执行业务验收。）

- 2026-10-07：使用方核对 question → web_gpt。追加CLI仅Qwen smoke；question仍直接使用ChatGPTWeb及原submit/collect，未运行业务。（命令未执行业务验收。）

- 2026-10-07：web_gpt统一GPT/Qwen每家20页预算并阻止复用跨站页和额度错误匿名兜底；paper常驻30%精选网页队列、额度/网络切换、错误归档关页及迁移工作台；question/article原公开签名与模型策略保持，静态复核，不触发其他业务。

- 2026-10-07：源码审查 web_gpt。核对capacity新增与GPT/Qwen创建预算各20页、额度错误不匿名兜底、复用只选GPT页；工厂/ask/submit/collect签名保持，权威说明与工具卡一致；40项隔离Chrome回归通过，paper消费端34项回归通过。账户科学生成质量不在此静态验收范围。（命令未执行业务验收。）

- 2026-10-07：使用方核对 paper → web_gpt。常驻网页消费端显式独立页及内部定位/设置守卫、公共提交锁，每家20页计入其他项目，额度/网络切换只允许证明未发送；错误归档关页、原始回答先落盘、迁移资料卡路径和科学未核验状态，34项消费端回归通过。主拉取和网页服务已启用，科学结果未验收。（命令未执行业务验收。）

- 2026-10-07：使用方核对 article → web_gpt。核对article默认GPT和显式Qwen工厂/ask保持兼容，新容量校验每家20页；open_gpt环境路径指向现有Playwright环境，未恢复article初筛或执行其科学业务。（命令未执行业务验收。）

- 2026-10-07：使用方核对 question → web_gpt。静态核对src/web_gpt_adapter.py原ChatGPTWeb(new_chat=True,thinking_high=True)与submit/collect兼容，增加全局GPT20页容量守卫不改变High或采用Qwen；未启动question业务。（命令未执行业务验收。）

2026-10-07 web_gpt：新版上传优先原生文件入口，避免照片入口吞掉 PDF；登记已暂停的 DeepSeek 显式候选及视觉验证限制。默认 GPT 不变。

- 2026-10-07：源码审查 web_gpt。已核对原生文件输入优先选择与禁用提示、显式暂停的 DeepSeek 候选及默认 GPT 契约。实机模型设置成功，上传菜单明确限额1小时；本轮真实上传未通过，视觉未核验，不宣称科学验收。（命令未执行业务验收。）

- 2026-10-07：使用方核对 paper → web_gpt。核对 transport factory/submit/collect；GPT单通道，原生上传配额保存并定时恢复；未知提交不重发。（命令未执行业务验收。）

- 2026-10-07：使用方核对 article → web_gpt。静态核对 provider 适配和默认 GPT 参数；未启动独立 article 科学生成。（命令未执行业务验收。）

- 2026-10-07：使用方核对 question → web_gpt。静态核对保持 ChatGPTWeb/High 默认契约，未启动 question 或新供应商任务。（命令未执行业务验收。）

2026-10-07 web_gpt：显式后台标记下模型/附件菜单使用DOM操作和DOM Escape关闭；默认守卫不变。paper修复常驻连接、原会话归属、原始回答落盘与页面池释放。

- 2026-10-07：源码审查 web_gpt。核对core/settings显式后台标记DOM点击和Escape关闭，默认参数与身份守卫不变；52原共享回归与13菜单回归通过，paper实机补收落盘并在同页生成下一篇，科学质量未验收。（命令未执行业务验收。）

- 2026-10-07：使用方核对 paper → web_gpt。常驻no_defaults CDP连接、唯一材料回执、正式回答保存hash与池释放；28消费端回归和实际下一篇落盘通过；未知提交不重发，科学合同未验收。（命令未执行业务验收。）

- 2026-10-07：使用方核对 article → web_gpt。静态核对默认调用未使用内部后台标记，原工厂及模型守卫兼容；不恢复独立article任务。（命令未执行业务验收。）

- 2026-10-07：使用方核对 question → web_gpt。静态核对原ChatGPTWeb/High调用与默认前台操作未变，不启用后台标记，不恢复question生成。（命令未执行业务验收。）

- 2026-10-08：使用方核对 paper → web_gpt。2026-10-08 治理整改：静态核对 create_session、ChatGPTWeb submit/collect、共享 submission_lock 及消费端常驻 no_defaults CDP/DOM 提交路径；统一暂停/通道授权上限/不确定请求保护与原提示额度证据，不改变公共 web_gpt 源码、签名和网页模型设置。本轮只做隔离合成材料、临时数据库/HTTP与独立无头浏览器回归；未上传真实论文、未恢复本地模型或验收科学质量。完整测试结果记录于 paper/docs/治理整改_20261008.md。（命令未执行业务验收。）

- 2026-10-08：使用方核对 paper → web_gpt。2026-10-08 新审计首批：静态核对 paper 消费端同页引文核验、CDP单页故障隔离/连接释放、后台队列恢复与实际上传视觉附件保留；公共 web_gpt 源码与签名不变。工作区504项离线回归通过，使用合成PDF、临时数据库/HTTP与独立无头浏览器；未访问生产浏览器、未上传真实材料、未运行模型或重启常驻服务。read.literal_match 新增默认兼容的可选case_sensitive，网页显式开启；原文引文匹配不代表科学或生产合同验收。详见paper/docs/新审计首批整改_20261008.md。（命令未执行业务验收。）

- 2026-10-08：使用方核对 paper → web_gpt。2026-10-08 用户授权主GPT制卡失败有限重试：消费端严格等待附件进度结束，点击前持久记录阶段与暂停回调；先本地JSON语法重解析，只有明确未点击或完整落盘且指纹一致的失败才能归档重排，额外最多2次、退避5/15分钟，未知回执不重发。公共web_gpt源码/签名未改。独立暂存源码497项回归完成（490通过、7私人原文/旧实验驱动跳过），含合成PDF与独立无头浏览器。正在正常重载现有主制卡服务，真实重试次数与落盘结果另记录；未恢复本地模型、未宣称科学验收。见paper/docs/制卡失败重试.md。（命令未执行业务验收。）

## 2026-10-08：codex_desktop_chat 0.1.0

新增原生 App Chat 文本接口、独立窗口并行生成和短 UI 提交锁；持久请求/回答指纹，未知回执禁止重发。16项隔离测试、单中文文本、真实双窗口同时生成及完整收取、跨工作目录只读 CLI 通过。仅独立适配示例，主文献制卡未切换；附件、科学质量、20路及常驻未验收。

- 2026-10-08：源码审查 codex_desktop_chat。核对原创AX/Unicode实现、Python与JSON CLI、调用说明与独立示例；16项隔离合同测试通过。单中文文本与双窗口同时生成/完整收取已实测；跨工作目录CLI读取通过。短UI锁不阻塞生成，未知请求不重发，收取异常携带原回执。附件、20路、常驻及科学验收未通过或未测试，不接入主制卡。（命令未执行业务验收。）

- 2026-10-08：使用方核对 paper → codex_desktop_chat。核对独立 examples/ask_codex_chat.py 显式前台与状态目录；接口保留原回执与窗口，文本限定。仅独立示例使用，不更改主网页制卡；实际双会话文本证据已保存。（命令未执行业务验收。）

- 2026-10-08：源码审查 codex_desktop_chat。最终核对逐字符前台原窗口保护、发送前完整输入和模型核对；最终默认编译助手跨目录真实文本 TEST_FINAL_OK 完整收取，16项合同测试通过，先前双窗口同时生成分别收取通过。仅文本独立工具，附件/20路/常驻/科学生产未验收。（命令未执行业务验收。）

- 2026-10-08：使用方核对 paper → codex_desktop_chat。独立示例适配静态核对完成；最终默认助手跨目录真实文本与原回执收取已测试；主文献流程未接入。（命令未执行业务验收。）

## 2026-10-08：codex_desktop_chat 0.2.0

新增原生多附件路径选择、不可变输入副本/指纹、上传等待与实际发送前进度/集合保护。上传等待释放短UI锁；匿名图片绑定原上传/发送记录和原用户消息图片数量。两个独立窗口各带不同PNG完整收取，未知请求未重发；32项隔离测试通过。新增显式附件通道观察/额度持久阻止；PDF、多文件真实回答、20路及常驻未验收，不接入主文献制卡。

- 2026-10-08：源码审查 codex_desktop_chat。核对0.2.0 Python/CLI/schema、原生文件面板真实点击、上传等待释放UI锁、不可变输入/原生发送进度与集合检查、匿名图片原用户消息数量与已验证上传记录绑定。32项隔离测试和双PNG实际完整收取通过；unknown未重发。额度观察持久阻止，明确核对原窗口才能解除；PDF、多附件真实回答、20路与常驻未验收。（命令未执行业务验收。）

- 2026-10-08：使用方核对 paper → codex_desktop_chat。独立示例已添加--file，核对新增files/upload_timeout及verify_attachment_channel契约；32项测试通过、两路不同PNG完整收取、跨目录CLI核对原回执与真实额度提示。不接入主网页版制卡；PDF等范围未验收。（命令未执行业务验收。）

## 2026-10-08：codex_desktop_chat 0.3.0

按用户授权新增本地ZIP预存、按内容指纹复用和单ZIP上传路由；已有ZIP不嵌套，完整性校验、临时包原子发布。38项隔离测试与跨目录prepare通过。本次无新上传；ZIP服务端读取未验收，历史0.2.0双PNG不视为ZIP验收。主网页版流程未改变。

- 2026-10-08：源码审查 codex_desktop_chat。核对本地内容指纹ZIP、原子发布、重用与损坏/路径/大小校验；submit/ask仅上传一个ZIP且不回退。38项隔离测试与跨目录prepare通过，无新上传。ZIP服务端读取未验收，额度与原回执保护不变。（命令未执行业务验收。）

- 2026-10-08：使用方核对 paper → codex_desktop_chat。独立示例files输入自动打包到单ZIP，本地prepare支持预存/复用，38项测试通过。未更改主网页版流程，ZIP读取未验收，本轮无上传测试。（命令未执行业务验收。）

- 2026-10-08：源码审查 codex_desktop_chat。已审查最终快照：通用ZIP解压/文件列表读取要求，不能读取须明示；问题/wire分开留存。38项隔离测试、本地prepare通过，无新上传；ZIP读取尚未验收。（命令未执行业务验收。）

- 2026-10-08：使用方核对 paper → codex_desktop_chat。核对最终单ZIP与原接口调用适配，38项测试、本地预存通过；主网页版未改动，无新上传。（命令未执行业务验收。）

## 2026-10-08：web_gpt共用ZIP

ChatGPT附件入口改成共享ZIP预存与单附件上传，新增本地prepare_upload_bundle，引用唯一paper打包器。paper主材料准备和新的受保护提交接入，同步包/实际prompt指纹；原已发/未知请求不重发、Qwen/DeepSeek不变。75项paper/ZIP和22项web_gpt离线回归通过，无真实上传或强制服务重载；ZIP内容读取未验收。article/question仅静态适配核对。

- 2026-10-08：源码审查 web_gpt。核对共享ZIP源码引用、单附件上传、进度未结束阻断、通用解压说明与实际包metadata；75项paper/ZIP和22项权威web_gpt离线回归通过，新增进度失败保护测试通过。无新真实上传，ZIP解压/科学读取未验收。（命令未执行业务验收。）

- 2026-10-08：使用方核对 chatgpt_playwright → codex_desktop_chat。zip_uploads只引用本地打包，不调用App；导入根和共享目录显式配置，单ZIP无散文件回退。本地合成文件上传控件测试通过，无真实上传。（命令未执行业务验收。）

- 2026-10-08：使用方核对 paper → web_gpt。新的受保护提交仅ZIP，原输入/实际prompt/包分别指纹留存；已发未知请求不重发。75项离线回归和新增上传进度阻断测试通过，无新真实上传，ZIP内容读取未验收。（命令未执行业务验收。）

- 2026-10-08：使用方核对 article → web_gpt。静态核对gpt_session适配及公开ask/submit原签名兼容；ChatGPT附件现在单ZIP，Qwen/DeepSeek不改。未运行article真实业务，ZIP读取未验收。（命令未执行业务验收。）

- 2026-10-08：使用方核对 question → web_gpt。静态核对complete-input.txt附件和无附件submit路径原参数兼容；TXT会包入ZIP并附通用解压说明，实际业务读取未验收，不启动question任务。（命令未执行业务验收。）

- 2026-10-09：源码审查 web_gpt。核对上传timeout传递至进度等待、全部进度条与读取异常阻断；默认60秒及公开签名保持。paper传180秒，61项隔离上传/回执/观察/重试测试通过。原调用说明与工具卡同步；没有新真实ZIP上传，科学读取未验收。（命令未执行业务验收。）

- 2026-10-09：使用方核对 article → web_gpt。静态核对article/src/web_gpt_adapter.py与cards/card_worker的gpt_session/ask原参数兼容；上传默认60秒保持，状态读取失败阻止发送。未运行article新业务或ZIP科学读取。（命令未执行业务验收。）

- 2026-10-09：使用方核对 paper → web_gpt。核对pipeline/web_card_transport传180000毫秒并保留上传失败在点击前；ZIP重试只接受精确冻结提示与通用说明、原包及回答指纹。61项隔离测试与既有会话只读核对通过；正常重载原运行后台，原未知页不关闭、不重发。科学读取未验收。（命令未执行业务验收。）

- 2026-10-09：使用方核对 question → web_gpt。静态核对src/web_gpt_adapter.py的submit/collect及complete-input.txt路径原参数兼容；公开上传默认60秒保持，异常时保守阻断。未启动question或运行其真实ZIP业务。（命令未执行业务验收。）

- 2026-10-09：使用方核对 paper → web_gpt。2026-10-09：独立原文核验复用常驻CDP所有者与共享提交锁；默认4路、当前持久设置10路，共享20页且回执不确定不重发。核验0–100分与文献分独立；已收取报告本地解析并显示，实际图像进入单ZIP。公共工具源码未改，本轮科学验收未宣称完成。（命令未执行业务验收。）

- 2026-10-09：使用方核对 paper → codex_desktop_chat。2026-10-09：原文核验只复用本地bundles.prepare_upload_bundle，图像PDF、净化原文、全页证据、上下文和卡片文本预存单ZIP；指纹校验及隔离测试通过，不使用App前台或开展App科学核验。（命令未执行业务验收。）

- 2026-10-09：使用方核对 paper → web_gpt。网页派发审计整改：核对权威core/submission正文提取与提交锁，页池CAS、原账本保护、核验精确归属及共享模式拒绝遗留双连接；1166项完整隔离测试通过。公共工具源码未改；原所有者20页运行观测不等于真实上传或科学验收。（命令未执行业务验收。）

- 2026-10-09：使用方核对 paper → web_gpt。2026-10-09 14:18审计复核：实读submission_lock与_message_text权威实现，锁为跨进程flock；与观测器均按textContent/innerText及JSON优先取正文。paper新请求隔离旧回答引用、保留原证据；deferred需明确未点击，重试另核归档及CAS。201项定向回归和新增139项共享窗口/超时相关回归通过；本轮无真实网页上传/发送或科学验收。公开web_gpt签名及源码未改。（命令未执行业务验收。）

- 2026-10-13：源码审查 codex_desktop_chat。核对新增独立api/interface/pyproject/README和工具内测试，305个全项目公开出口对象身份及1756项全项目离线回归通过。原11份登记实现SHA256逐一未变，原ask/submit/collect/ZIP签名与默认行为保持；未进行新的桌面Chat、网页发送、ZIP服务端读取或科学验收。（命令未执行业务验收。）

- 2026-10-13：使用方核对 paper → codex_desktop_chat。paper通过公开API复用同一ZIP准备/核对实现；当前科学任务仍GPT网页，桌面入口不自动运行。全项目1756离线回归及API对象身份检查通过，本轮无新真实上传/发送或科学验收。（命令未执行业务验收。）

- 2026-10-13：使用方核对 chatgpt_playwright → codex_desktop_chat。实读web_gpt/zip_uploads.py，仍按原WEB_GPT_BUNDLE_IMPORT_ROOT引用codex_desktop_chat.bundles.prepare_upload_bundle；11份原登记实现SHA逐项未变，原签名/ZIP预算/缓存路径保持，无消费端业务源码修改。只登记静态兼容，无新真实上传或科学读取验收。（命令未执行业务验收。）

## 2026-10-14 paper八项目完整归并

更新article/crawler/read的真实源码位置和paper基础运行项目登记根；全局all规则归infrastructure。codex_desktop_chat源码根不变，只适配ZIP默认存储归属，外部web_gpt源码与调用签名保持。paper用户明确授权维护原服务并完成全部归并，数据备份删除并禁用。1761离线回归、307接口身份与18构建通过；真实科学验收独立。

- 2026-10-14：源码审查 codex_desktop_chat。八项目归并核对：仅ZIP默认目录读取workspace.json物理存储，独立工具无core依赖；原公开签名、大小预算、指纹及发布保护保持。候选1761离线回归、307对象身份及18构建通过；原11文件中只有bundles默认定位实现调整，其余实现hash保持。无新桌面调用/上传/科学验收。（命令未执行业务验收。）

- 2026-10-14：使用方核对 paper → codex_desktop_chat。使用方源码通过公开API准备/核对同一ZIP；读取旧冻结路径先经WorkspacePath，不改旧回执或重发未知请求。源码归属/配置/导入核对与1761候选离线回归通过；无新的ZIP外发或科学验收。（命令未执行业务验收。）

- 2026-10-14：使用方核对 chatgpt_playwright → codex_desktop_chat。实读web_gpt/zip_uploads.py，WEB_GPT_BUNDLE_IMPORT_ROOT仍指向paper，codex_desktop_chat源码根和签名保持；默认ZIP目录由工具适配为infrastructure/data，未修改网页工具源码。只静态兼容核对，无新上传或科学读取验收。（命令未执行业务验收。）

- 2026-10-14：源码审查 literature_explorer。逐项核对20261014审核修复与工具卡：来源独立延期/强身份隔离/向量对齐/当前主题关键词/HTTP冷却，20项临时SQLite与模拟HTTP回归通过；登记consumers为空，主fetch仅公开解析API静态兼容，无外网或历史库重扫。（命令未执行业务验收。）

## 2026-10-14 literature_explorer审核修复

来源独立引文回执与持久延期、强DOI冲突隔离、稳定ID、严格向量对齐/维度、当前波次查询和Retry-After冷却。工具卡同步新的可选参数与增量存储合同；主fetch仅解析调用边界静态核对。20项离线标准库回归通过；未执行外网、历史库迁移、服务恢复或科学验收。

- 2026-10-14：源码审查 literature_explorer。20261014审核修复和工具卡逐项核对，20项临时SQLite/模拟HTTP回归通过；登记consumers为空，主fetch仅公开解析API兼容，无外网或历史库重扫。（命令未执行业务验收。）


## 2026-10-14 codex_desktop_chat 审计整改

核实并修复来源缓存、轮次归属、延迟锚点、双层UI权限、Wheel资源与ZIP特殊条目；新增回执阶段约束。公开签名保持，verify_bundle新增manifest_files。静态核对paper与chatgpt_playwright消费方使用既有字段，无需业务适配修改。50离线测试与Swift编译通过；实机外发未运行。

- 2026-10-14：源码审查 codex_desktop_chat。核对源码、工具卡、当前快照与新增12项回归；50离线测试、Swift编译及隔离Wheel安装资源/helper编译通过，无真实UI或上传验收。（命令未执行业务验收。）

- 2026-10-14：使用方核对 paper → codex_desktop_chat。实读cards/web_card_inputs、delivery/structure_repair和review/card_review_queue，签名与原字段保持；新增manifest_files不影响消费。仅静态核对。（命令未执行业务验收。）

- 2026-10-14：使用方核对 chatgpt_playwright → codex_desktop_chat。实读web_gpt/zip_uploads.py，公开prepare签名及bundle_dir保持；缓存身份不符拒绝且不回退。仅静态核对。（命令未执行业务验收。）

- 2026-10-14：源码审查 codex_desktop_chat。补充审计实测结果：50离线测试、Swift编译、隔离Wheel安装与资源helper定位通过；全库受沙箱与test_runner/workspace不一致阻碍，未宣称全库或实机验收。（命令未执行业务验收。）

- 2026-10-14：使用方核对 paper → codex_desktop_chat。原ZIP消费字段与签名已实读保持；新增审计文档仅记录验证限制，无新业务适配或外发。（命令未执行业务验收。）

- 2026-10-14：使用方核对 chatgpt_playwright → codex_desktop_chat。已实读zip_uploads公开适配；新增审计记录不改签名与既有字段，无新网页外发。（命令未执行业务验收。）

- 2026-10-14：源码审查 codex_desktop_chat。最终复核：本工具50项、包含cards/review消费方379项离线隔离测试通过；Swift及安装Wheel资源/helper通过。只读阶段保护保持，复杂AX/正式会话与全库验收限制见AUDIT_REVIEW。（命令未执行业务验收。）

- 2026-10-14：使用方核对 paper → codex_desktop_chat。制卡与核验ZIP消费方实读，379项隔离回归通过；无新真实提交。（命令未执行业务验收。）

- 2026-10-14：使用方核对 chatgpt_playwright → codex_desktop_chat。实读zip_uploads调用签名与字段兼容，消费方379项离线模拟回归通过，无真实网页外发。（命令未执行业务验收。）

## 2026-10-14：paper任务面板与原所有者观测停滞修复

2026-10-14 paper原任务面板停滞维护：使用方修复已迁移面板路径，原CDP事件循环内并行只读健康快照、每页3秒期限；本地回执索引移到文件线程，无新连接。诊断hash缓存保持文件身份/mtime/ctime与原回执唯一性/CAS校验；未知提交不重发、暂停优先及P85原值不变。web_gpt源码与公开签名未修改，静态适配和128项针对性测试通过；不作为真实网页或科学验收。

## 2026-10-14：paper剩余页面恢复合同

paper/browser通过codex_desktop_chat公开verify_bundle只读核对已登记、从未提交nonce候选恢复的ZIP清单、内容与包名指纹，支持Chrome数字后缀；原请求有账本时必须核对原packet绑定，不能借公共缓存绕过。review公开check_packet统一核对旧核验ZIP证据，新账本记录upload_bundle，旧冻结字节保留。空换行与真实草稿区别处理，已验证原ledger-before归档保持相同SHA/target；未知材料不重发。第05槽新创建epoch仍需具体单次授权，默认禁用。本轮无新增桌面Chat调用或科学验收。

## 2026-10-14：paper迁移后的SSD运行链接验收

新增原data几何关系到infrastructure/data的真实SSD链接验收：8032个失效相对链接已按目标SHA/版本及链接CAS修复，目标字节不写入、不备份。16个仅本地文件缺失且无当前请求的原文修正准备任务，经原文、冻结输入、回执、暂停和任务绑定校验恢复原FIFO，重试计数不重置。第05槽一次新epoch已获具体用户批准并消费，原nonce仍保持未知证据。实测专窗20/20，制卡、核验、修正均已实际生成；历史未知回执不重发，真实缺失的历史目标不补造。1850项离线回归通过，科学验收独立。

## 2026-10-14：paper 近期恢复与文档路径核对

- paper 新增本地归档链接移动接口、核验准备候选与源码版本缓存恢复，修正版本发布绑定、严格 JSON 包装和原提示展开；web_gpt/codex_desktop_chat 调用参数及原唯一 CDP 所有者保持。
- codex_desktop_chat README 仅修正物理归并后的离线测试路径，工具卡同步；paper 最终1859项隔离回归和14组件边界检查通过。没有新的桌面请求或科学验收。

- 2026-10-14：源码审查 codex_desktop_chat。仅README测试路径从旧.venv-test/maintenance更新为infrastructure环境/维护入口；核对工具卡、自动快照和公开参数无变化，paper1859项隔离回归通过；未新增桌面外发或科学验收。（命令未执行业务验收。）

- 2026-10-14：使用方核对 paper → codex_desktop_chat。README测试路径调整；现有调用参数及适配代码未变，1859项隔离回归与14组件边界检查通过；不启用桌面通道、不声称新真实上传。（命令未执行业务验收。）

- 2026-10-14：使用方核对 chatgpt_playwright → codex_desktop_chat。逐项核对本次仅README测试命令路径变化，公开参数、返回及导入路径未变，适配无需修改；仅静态核对，本轮没有新的桌面调用。（命令未执行业务验收。）

2026-10-14 补充验收：paper 完整原核验源渲染、未冻结候选持久隔离归档与Catalog初始化复用最终1876项隔离回归通过，14组件/223源码/310出口边界检查通过。已登记工具的公开调用参数和provider源码未变。原GPT网页流程按原窗口/暂停/额度运行，不代表新的桌面上传或科学验收。

## 2026-10-14 paper核验通过修正持续优先

paper内部core统一置顶真实通过报告关联的修正和后继核验，保留原文章分数/FIFO与暂停；13项旧排版阻塞完整保存证据后分流，正式发布目录按Catalog/原回执核对。未修改4项登记工具的公共源码或新增常驻。最终工作区1885项隔离测试通过，14组件/224源码/311出口检查通过，global update/check_links通过；真实外发仍受原回执及附件额度保护。

## 2026-10-14 paper当前网页停滞恢复

paper原所有者修复有UI出处的未发送主页加载错误误判，已结束工作台移窗日志不再争用提交锁，固定页健康快照补输入区/模型控件诊断。4项登记工具公共源码不变。1887项隔离回归、14组件接口与全局联动检查通过；原20页专窗实机恢复已验证生成，未知请求不重发，科学验收独立。

## 2026-10-14 paper原网页所有者自动监督

paper新增maintenance公开监督/验收登记接口，原HTTP-only watcher在已验收源码及原LaunchAgent/PID/令牌核对后请求正常交接，旧PID退出后只kickstart同一入口；暂停、未知请求及固定20槽不变。4项已登记工具源码与调用参数未变。1897项隔离测试、14组件/225源码/313出口检查与全局联动检查通过，实机自动交接另记paper报告。

- 2026-10-14：源码审查 codex_desktop_chat。本轮源码差异仅新增AUDIT.md静态审计报告，已读全文；所有原实现/接口SHA保持不变。工具卡记录报告归属及未实施/未实机验收边界，不采纳报告结论为业务验收。（命令未执行业务验收。）

- 2026-10-14：使用方核对 paper → codex_desktop_chat。只新增AUDIT.md报告，公开ZIP实现和调用参数未变，paper适配无需改变；仅静态核对，不启动桌面通道。（命令未执行业务验收。）

- 2026-10-14：使用方核对 chatgpt_playwright → codex_desktop_chat。源码只新增静态审计报告，现有ZIP适配函数及参数未变，无实现修改；仅静态核对，没有新外发或桌面验收。（命令未执行业务验收。）

## 2026-10-14 paper真实停滞溯源

paper新增原所有者首页复用公开接口；补页按本槽/全局身份和各槽SHA区分真实冲突与其他槽更新，原账本路径移走只读核对唯一字节一致history回执；composer真实上传进度保护优先于客户端超时重开。152专项、28无网络真实DOM、1908全量测试和14组件/226源码/314出口检查通过。工具公开实现未变；新增AUDIT.md静态报告已单独登记，不采纳其建议为实机验收。实机自动交接与生成另记paper报告。

补充最终验收：paper上传保留租约在原协程结束时立即保留target预算，新鲜完整原生停止证据才释放；原监控避免提交锁无限延期，仅请求正常退出、不强杀。最终1915全量、200专项、28无网络真实DOM检查通过，原专窗20槽完整、暂停指纹保持，实机曾核对到5项生成。剩余CDN PUT HTTP2协议错误已由原连接实证；HTTP1候选只有6项合同/本机TLS二进制验收，未应用、未真实上传，需要限定实际上传保护例外，未冒称全恢复。

- 2026-10-15：源码审查 codex_desktop_chat。本次漂移仅新增AUDIT_RUNS/20261015-002603-196f0f/AUDIT.md静态报告；已核对自动快照，生产Python/Swift、ZIP接口与schema相对原登记无变化。仅登记不可变文档，不接受报告建议为实现或实机验收。（命令未执行业务验收。）

- 2026-10-15：使用方核对 paper → codex_desktop_chat。新增静态审计报告不改变API或ZIP行为；paper仍仅调用公开ZIP打包/校验，现有冻结输入和未知回执保护保持。仅静态适配核对，不声称新桌面或科学验收。（命令未执行业务验收。）

- 2026-10-15：使用方核对 chatgpt_playwright → codex_desktop_chat。新增静态审计报告，ZIP prepare_upload_bundle/verify_bundle实现与参数未变；已读web_gpt工具卡及接口快照，无适配代码变更或新外发。只记录静态兼容性。（命令未执行业务验收。）

- 2026-10-15：源码审查 web_gpt。S001 逐文件核对：core.py 新增 implementation_identity/upload_files_detailed/_uploads_settled_state/_wait_attachment_state/_visible_progress 与失败分类常量，upload_files 改为返回详细结果的 ['ok']，逐分支离线比对旧返回值与异常文案一致；__init__.py 仅新增具名导出 upload_files_detailed；调用说明.md 增 2026-10-15 阶段归因段并更正 2026-10-09 的“读取异常视为失败”表述。工具卡 README 增同一节与 API 行。旧 chatgpt_core 未改动。真实网页上传、网络协议与科学验收未运行，本次只记录源码审查。（命令未执行业务验收。）

- 2026-10-15：使用方核对 paper → web_gpt。paper 消费方静态核对：browser/web_card_transport.submit_gpt_background 改走 upload_files_detailed＋upload_trace 具名出口（lane/job/target、ZIP SHA/大小、内核 SHA 与 SDK 版本、failure_kind/retryable_upload）；web_page_observer 按 request 时刻绑定 attempt；cards/web_card_service.code_version 与 maintenance/owner_supervision 把 dependency:web_gpt.* 与 SDK 纳入验收比较；web_gpt.capacity/submission/settings/core 旧用法与异常文案保持，review/web_feedback 与 article/web_gpt_adapter 未改。离线合同与源码隔离测试通过，真实上传未验收。（命令未执行业务验收。）

- 2026-10-15：使用方核对 article → web_gpt。S001 消费方静态核对（article 属其他项目，本次只做兼容性检查）：infrastructure/article/src/web_gpt_adapter.py 只用 ChatGPTWeb(new_chat,thinking_high) 与 create_session，附件经 ChatGPTWeb.submit→upload_files 单入口；upload_files 返回值与异常语义逐分支保持，故 article 无需适配改动。未运行 article 真实网页接入，其原有‘已核对源码，尚未完成真实接入验收’范围不变。（命令未执行业务验收。）

- 2026-10-15：使用方核对 question → web_gpt。S001 消费方静态核对（question 属其他项目，本次只做兼容性检查）：question/src/web_gpt_adapter.py 只用 ChatGPTWeb 会话入口，附件经 submit→upload_files；question/tests/test_web_input.py 只断言 core.send_prompt 的既有异常语义，该函数未改。upload_files 旧返回/异常保持，question 无需适配。未运行 question 真实网页生成或多会话验收。（命令未执行业务验收。）

- 2026-10-15：源码审查 codex_desktop_chat。仅新增 AUDIT_RUNS/20261015-173427-a6db66/AUDIT.md；逐项核对自动接口快照及原说明，生产.py/接口/ZIP调用合同无变化，测试快照中全部codex_desktop_chat源码哈希未漂移；登记文档基线不认可审计结论，不声称桌面AX或真实业务验收。（命令未执行业务验收。）

- 2026-10-15：使用方核对 paper → codex_desktop_chat。仅审计Markdown新增；制卡/核验继续原prepare_upload_bundle与verify_bundle公共API，接口/源码哈希及使用方适配未变，静态核对通过；网页实测和科学验收另记。（命令未执行业务验收。）

- 2026-10-15：使用方核对 chatgpt_playwright → codex_desktop_chat。相对基线仅新增审计Markdown；web_gpt ZIP适配器及生产公共函数签名、返回和源码哈希未变，静态适配无须改动；不等同业务或App实机验收。（命令未执行业务验收。）

- 2026-10-17：源码审查 web_gpt。2026-10-17逐行核对core.py只增加upload_files_detailed可选仅关键字file_writer及赋值处分支；默认None仍原set_input_files，upload_files/ChatGPTWeb/article/question不传新参数，返回/异常和原生回执/结算不变。paper对精确本机Chrome/target/input/ZIP加持久赋值意图和未知不回退保护。工具卡、调用说明及消费方已核对；离线回归通过，实机效果另记，不冒称业务验收。（命令未执行业务验收。）

- 2026-10-17：使用方核对 paper → web_gpt。paper公开submit_gpt_background仅在local_file_paths显式开启时传file_writer；本机进程/端点/target/input/ZIP和暂停守卫两次核对，持久记录意图，未知不回退或重写，180秒与原PUT回执不变。离线验证通过，真实传输效果另记。（命令未执行业务验收。）

- 2026-10-17：使用方核对 article → web_gpt。实读infrastructure/article/src/web_gpt_adapter.py，仍只用ChatGPTWeb/create_session和旧submit入口；本次仅upload_files_detailed新增可选file_writer，默认原赋值且旧会话入口不传参数，消费方兼容无需业务修改。仅静态核对，无新article网页外发或接入验收。（命令未执行业务验收。）

- 2026-10-17：使用方核对 question → web_gpt。实读question/src/web_gpt_adapter.py及test_web_input.py，旧ChatGPTWeb.submit和send_prompt合同未变，不传新file_writer，默认仍原赋值/异常/回执。兼容无需业务修改；仅静态核对，无新question网页生成或真实接入验收。（命令未执行业务验收。）

- 2026-10-18：源码审查 codex_desktop_chat。2026-10-18 仅修正文档路径/测试计数、未用导入、cli_modules 登记；公开 python_exports 与 bundles 签名未变，50 项回归通过（命令未执行业务验收。）

- 2026-10-18：使用方核对 paper → codex_desktop_chat。使用方仅经 codex_desktop_chat.api 调用 bundles__prepare_upload_bundle/bundles__verify_bundle；本次未改 bundles 实现或签名，cards/review/browser 相关回归通过（命令未执行业务验收。）

- 2026-10-18：使用方核对 chatgpt_playwright → codex_desktop_chat。现有适配只使用桌面会话/附件公开接口；本次仅文档与测试导入修正，公开签名未变（命令未执行业务验收。）

- 2026-10-18：使用方核对 paper → codex_desktop_chat。仅移除已按删除清单清理的五个审计文档登记；生产实现与公开调用合同未变，paper 使用适配未改（命令未执行业务验收。）

- 2026-10-18：使用方核对 chatgpt_playwright → codex_desktop_chat。仅移除已删除历史审计文档登记；生产实现及消费接口未变，无新增实机验收（命令未执行业务验收。）

2026-10-18 paper 核验漏斗修复配套：根据 reports/deletion-manifests/20261018-audit-md-deletion.json，清除 codex_desktop_chat 五份已删除历史审计 MD 的陈旧 source_files_sha256 登记；不改变生产实现/公开接口。paper 与 chatgpt_playwright 使用方已登记仅文档删除的静态核对，全局 update/check_links 通过。

## 2026-10-20 paper 文献组织首版接口

- paper登记根infrastructure新增literature业务组件与core只读元信息投影的模块关系；workbench通过literature.api调用，源目录未复制到tools，也未新增通用登记工具。
- 两端合同、组件接口与依赖见 `../paper/literature/README.md`、`interface.json`、`infrastructure/core/interface.json`、`workbench/interface.json` 和 `infrastructure/tool-dependencies.json`。
- 临时SQLite/localhost及独立headless浏览器检查通过；模型、生产Chrome、自动标注和原常驻任务均未调用。全项目回归的修正模块既有失败单独记于paper报告，不冒称全量通过。

### 2026-10-20 paper 自动标签复用设计补充

- 只读盘点Catalog及原任务材料，记录1,838篇可验证冻结逐页文本与6篇重叠细解析；仅文档/接口迁移说明，不启动标注或模型。literature接口明确人工首版需替换及自动标注未实现，未冒称运行时已禁用旧人工接口。参考spaCy/YAKE/GROBID/Docling，未安装运行。

### 2026-10-20 paper 一二级自动标注及10篇评测

- literature 0.2.0新增纯Python两级规则、core公开只读材料指针、read公开本地文本补解析、冻结输入/自动侧库、自动界面；停用新增人工标注，历史决定保持。新增代码与接口在paper登记根infrastructure的模块关系中维护。
- 10篇规则/预测先冻结，同输入助手参考标准单独保存，不进入生产；开放词表一级P100/R54.72/F170.73，二级P81.08/R41.10/F154.55。后续单独增加SI-only通用来源保护，未回改基线。没有模型、生产浏览器或常驻激活；全量测试既有失败另记。

- 2026-10-20 paper/literature 0.3.0：新增focus.py核心标签策略（一级1～3、二级2～5为参考），保存辅助证据与继承分类；workbench列表核心展示、详情留证据、筛选核心/上位分类，依赖声明同步。原10篇同输入开发重评，新核心参考先冻结，主文二级排除已知SI；原宽标签结果不改写。仅本地离线/临时HTTP回归，无模型或原工作流启动；实测见paper/reports/20261020-core-directions-evaluation.md。

- 2026-10-20 literature 0.3.1持续优化首轮：句内研究归属、被动摘要、历史自引、quench歧义及罗马数字章节；benchmark增加开发ID排除、留出不生成预测及延后预测hash/身份校验。新10篇留出冻结未预测，用户明确授权每30分钟由当前聊天heartbeat 30-2跟进；仅离线隔离评测，不启用模型或原网页工作流。详见paper/literature/ITERATION.md。

- 2026-10-20 literature 0.4.0 / directions-rules-1.3.0：词表从38扩到41，增加取向、溶液加工、电荷陷阱的通用概念与边界；评测支持先冻结的一对一同层同维度语义ID对应，不改原gold，不被生产分类读取。原开发集同输入重评，并首次对先冻结候选、先独立gold后预测的新10篇留出作单次比较；查看后不再称未见。沿原30-2离线研发边界，无原常驻或模型启动。

- 2026-10-20 literature 0.4.1 / directions-rules-1.3.1候选：41项语义ID不变，限定spin-vibronic/spin vibronic/spinvibronic显式术语，普通vibronic coupling不再归为自旋振动耦合；新增通用正反例。冻结原标准和输入，已曝光10篇仅作开发回归，第二组留出未开封；全量验证状态见paper/reports/20261020-tagging-iteration-003.md。未启动原服务或模型。

- 2026-10-20 literature 0.4.2 / directions-rules-1.3.2：词表维持41项ID，补DFT名词单复数和英美optimization/optimisation，完整词边界及实际正文使用要求保留；参考与输入不改，已曝光组仅作开发回归，新留出未打开。包/工作台依赖及全局模块记录同步，验证结果见paper/reports/20261020-tagging-iteration-004.md；不启动原服务或模型。

- 2026-10-20 literature 0.4.3 / directions-rules-1.3.3：当前实际方法句可引用既往步骤，仅掩蔽过程引用短语，同局部操作句且无其余历史信号才放行；历史/非方法保护和核心策略不变。可选evidence.procedure_reference留痕，词表仍41项，冻结开发标签/证据输出未变，本轮没有独立成绩；包/使用方及登记同步，验证见paper/reports/20261020-tagging-iteration-005.md。

- 2026-10-20 literature 0.5.0 / directions-rules-1.4.0候选：新增联合色谱/质谱降解产物分析受控流程，42标签；实际方法与产物关联双证据必存，元信息仅用于科学目的的核心性。先冻结同层同维度一对一评价对应，不改gold/输入，不将映射用于生产。使用方与接口登记同步，原文/主库只读，无模型或服务激活；验证见paper/reports/20261020-tagging-iteration-006.md。

- 2026-10-20 literature 0.5.0 / 规则1.4.0保持不变，第7轮首次打开第二组10篇；候选/开发冻结后独立同输入参考先于预测冻结，细标P45.16/R28.00/F134.57，未调参，不宣称泛化可靠。前两组已用，第三组按元信息冻结未见输入且无预测；接口说明与全局模块记录同步，不重启生产服务或模型。

## 2026-10-20 标签迭代8

paper/literature0.5.1候选：一级摘要相邻当前结果指代，精确前句证据及历史/假设/比较保护；三组已曝光开发集，未用第三留出，未重载生产。报告paper/reports/20261020-tagging-iteration-008.md；全局联动随本轮检查记录。未修改已登记工具实现或审查基线。

## 2026-10-20 标签迭代9

paper/literature隔离候选1.5.0区分MR与MR-TADF并检查摘要局部简称，冻结开发标准精确率退化；当前仍1.4.1，未改生产源码版本或工作台依赖、未重载服务。报告paper/reports/20261020-tagging-iteration-009.md。未修改登记工具实现与审查基线。

## 2026-10-20 标签迭代10

paper/literature0.5.2候选1.4.2：摘要有界因果结果归属、逐字链证据及历史/推测/比较中断；42标签不变，MR候选未合入，三组曝光开发，无新独立结果。workbench依赖与全局模块说明同步，未重载生产。报告paper/reports/20261020-tagging-iteration-010.md。登记工具实现和审查基线未改。

标签迭代10修订：初版1.4.2全量软件测试通过后，额外合成否定探针3项误入；初版回执/源码/预测保留。另冻1.4.3 / literature0.5.3补复合否定保护，68项局部测试通过，重新跑完整检查，不改旧参考或登记工具基线。

## 2026-10-20 标签迭代11

paper/literature1.4.3源码未改，第三组同输入独立参考先冻后预测；一级P90.91/R64.52、二级P61.11/R40.74，无事后调参。第四组新留出与40篇无重复并封存。同步评测说明、全局模块与工作台使用边界，无工具实现/审查基线或生产重载。报告paper/reports/20261020-tagging-iteration-011.md。

## 2026-10-20 标签迭代12

paper/literature0.5.4候选1.4.4：二级旁支推测/一般机制保留辅助，不借用邻近贡献词；显式研究目标与另有直接证据可核心。四组曝光开发，第三组FP14→11、TP22/FN32不变，无新独立结果。workbench依赖/模块说明同步，未重载生产或改工具审查基线。报告paper/reports/20261020-tagging-iteration-012.md。

## 2026-10-20 标签迭代13

paper/literature时间分辨发光词形候选1.4.5/v7保留隔离：四组曝光开发核心指标不变，2篇新增辅助方法证据；否定测量反例失败，未提升。当前仍literature0.5.4 / 1.4.4，workbench依赖不变，未重载服务、不改工具审查基线。报告paper/reports/20261020-tagging-iteration-013.md。

## 2026-10-20 标签迭代14

paper/literature0.5.5候选1.4.7仅修方法否定的子句归属，否定原句留存；83项回归通过，四组曝光开发标签/指标及621条证据不变，无新独立成绩。workbench依赖同步，未合入1.4.5词形、未重载服务、不修改工具审查基线。报告paper/reports/20261020-tagging-iteration-014.md。

## 2026-10-20 标签迭代15

paper/literature0.5.6候选1.4.8仅补时间分辨光学方法词形，使用已验收否定守卫；91项标签回归通过，四组开发核心指标不变、2篇新增辅助证据，无新独立成绩。workbench依赖同步，未重载服务、未改工具审查基线。报告paper/reports/20261020-tagging-iteration-015.md。

## 2026-10-20 标签迭代16

paper/literature0.5.7候选1.4.9仅补方法主语明确科学结果归因的核心性；99项回归通过，第三曝光开发补1个正确细标、FP11不变，其余组及一级不变，无新独立成绩。workbench依赖同步，原证据/词表/来源准入不变；未重载服务或改工具审查基线。报告paper/reports/20261020-tagging-iteration-016.md。

## 2026-10-20 标签迭代17

paper/literature0.5.8候选1.4.10仅修方法使用词形，阻断performance等误词干，复用既有明确实验结果句准入；106项回归通过，四组曝光开发核心指标不变，623条证据仍准入、1条旧误准入证据归档，无新独立成绩。workbench依赖同步，未重载服务或改工具审查基线。报告paper/reports/20261020-tagging-iteration-017.md。

## 2026-10-20 标签迭代18

paper/literature1.4.10源码/词表/包0.5.8未改，第四组先冻25/56参考及81精确引文再预测；一级P88.24/R60.00，二级P60.00/R26.79，细标覆盖不足，无事后调参。第五组与50篇无重复并封存。同步评测说明、当前/历史独立接口指标、工作台使用边界及全局模块记录；依赖/工具审查基线不改，未重载生产。报告paper/reports/20261020-tagging-iteration-018.md。

## 2026-10-20 标签迭代19

paper/literature0.5.9候选1.4.11只改引用作者的紧邻被动归属；原证据留mentions并核对逐字前句。115项标签通过，五组曝光开发中第四组两级各少1个误标，TP/FN不变，其他组不变；无当前独立成绩，第五组封存。workbench依赖同步，未重载服务、未改工具审查基线。报告paper/reports/20261020-tagging-iteration-019.md。

## 2026-10-20 标签迭代20

paper/literature0.5.10候选1.4.12只改一级标题beyond局部比较依据，不作全标签否决；弱标题证据独立留mentions并核对原句。125项标签通过，五组曝光开发核心指标不变，1条标题依据转提及，摘要背景词干误判未解决；无当前独立成绩，第五组封存。workbench依赖同步，未重载服务或改工具审查基线。报告paper/reports/20261020-tagging-iteration-020.md。

## 2026-10-20 标签迭代21

paper/literature0.5.11候选最终1.4.14仅收紧元信息摘要/指代前句的develop完整动作；初版全局1.4.13二级退化留档未提升，原fulltext规则保留。136项标签通过，五组开发中第四一级FP1→0、TP/FN不变，二级输出全部原样；无当前独立成绩，第五组封存。workbench依赖同步，未重载服务或改工具审查基线。报告paper/reports/20261020-tagging-iteration-021.md。

## 2026-10-21 标签迭代22

paper/literature1.4.14源码/词表/包0.5.11未改，第五组先冻26/58参考及85条精确证据后预测：一级P83.33/R57.69，二级P59.09/R22.41，细标覆盖不足，无事后调参。第六组与60篇无重复并封存。同步当前/历史独立指标、工作台说明及全局模块记录；依赖/工具审查基线不改，未重载生产。报告paper/reports/20261021-tagging-iteration-022.md。

## 2026-10-21 标签迭代23

paper/literature0.5.12候选1.4.15仅处理错误章节内的编号多作者书目归属，原句/书目区间保留为提及并校验。143项标签通过；六组曝光开发去1二级误标，TP/FN不变，无新独立成绩，第六留出封存。workbench依赖及模块记录同步，不改工具审查基线、未重载生产。报告paper/reports/20261021-tagging-iteration-023.md。

## 2026-10-21 标签迭代24

paper/literature0.5.13候选1.4.16仅补同块截断书目组合结构，精确残段/期刊尾注/后继作者记录保留为提及。152项标签通过，六组60篇核心指标不变，仅清除辅助污染；无新独立成绩，第六留出封存。工作台依赖/说明及模块记录同步，未改工具审查基线或重载生产。报告paper/reports/20261021-tagging-iteration-024.md。

标签第24轮最终1.4.17候选154项回归通过，但固定开发丢1个正确二级标签，未提升；候选/初版/证据保留，活动源码/包/工作台依赖恢复1.4.15 / 0.5.12。无新独立成绩，第六留出封存，等待恢复后全量验收；不保留错误书目来抬高TP，不改gold。

## 2026-10-21 标签迭代25

paper/literature0.5.13最终候选1.4.19 / v9仅效率/EQE滚降复合词单复数，42ID及原词间/来源/核心策略不改；初版1.4.18扩大词间空白造成背景核心误标，留档未提升。155项局部通过，六组曝光开发补回2个正确二级核心、误标不增，无新独立成绩，第六留出封存。工作台依赖及模块记录同步，不改工具审查基线或重载生产。报告paper/reports/20261021-tagging-iteration-025.md。

## 2026-10-21 标签迭代26

paper/literature0.5.14候选1.4.20仅问题泛指背景核心投票归属，保留辅助原句和当前结果；167项局部通过，六组开发科学对象/指标不变，旧1.4.18已曝光误标组件回放降辅助且2条原句不变，不冒称新成绩。工作台依赖/说明及模块记录同步，未改工具审查基线或重载生产，第六留出封存。报告paper/reports/20261021-tagging-iteration-026.md。

## 2026-10-21 标签迭代27

paper/literature0.5.15候选1.4.21 / 词表v10只补efficiency/EQE至滚降复合词间PDF多空白，42ID与1.4.20核心背景/来源守卫不变。177项局部通过，六组60篇核心指标不变；新增辅助原句与历史提及各1条。无新独立成绩，第六留出封存。同步工作台依赖及模块记录，不改工具审查基线或生产服务。报告paper/reports/20261021-tagging-iteration-027.md。

## 2026-10-21 标签迭代28

paper/literature固定1.4.21 / 0.5.15完成第六组10篇单次独立评测，参考26/61及87条引文先冻后预测，一级P80/R30.77/F144.44、二级P62.5/R40.98/F149.5。疑似SI保留计分且不冒称主文通过；无事后调参、源码/包/工作台依赖不改。第六组已用，第七组与70篇身份无重叠、未读无预测。评测接口/说明与模块记录同步，不改工具审查基线或恢复生产。报告paper/reports/20261021-tagging-iteration-028.md。

## 2026-10-21 标签迭代29

paper/literature0.5.16候选1.4.22仅补摘要for the first time被动结果主语，原文FOCUS/来源/核心/42ID不改。189项局部通过，七组70篇曝光开发第六已用组补1个正确一级，误标数不增、二级不变。1087旧接受保留，4旧提及转接受/继承且原件归档，191旧提及不变。无新独立成绩，1.4.21历史保存，第七组封存。同步工作台精确依赖、接口/说明和模块记录，不改工具审查基线或生产服务。报告paper/reports/20261021-tagging-iteration-029.md。

## 2026-10-21 标签迭代30

paper/literature0.5.17候选1.4.23新增一级圆偏振发光（词表v11/43ID），完整发光别名不匹配圆偏振激发光或裸CPL，原42项/归属/来源/核心不改。202项局部通过，七组70篇开发补1个正确一级、误标不增、二级不变。一对一同层同维度评价对应先冻后预测并公开，原26/61gold不变，旧v10基线另存。无新独立成绩，第七组封存。同步工作台精确依赖/说明及模块登记，不改工具审查基线或生产服务。报告paper/reports/20261021-tagging-iteration-030.md。

## 2026-10-21 标签迭代31

paper/literature0.5.18候选1.4.24新增一级机器学习分子逆向设计（词表v12/44ID），要求学习模型/分子/逆向设计目的，不匹配仅前向预测、筛选或非分子器件设计；原43项/归属/来源/核心不改。216项局部通过，七组70篇开发补1个正确一级、误标不增、二级不变。同层同维度评价对应先冻后预测并公开，旧对应和26/61gold不改，旧v11基线另存。无新独立成绩，第七组封存。同步工作台精确依赖/说明及模块登记，不改工具审查基线或生产服务。报告paper/reports/20261021-tagging-iteration-031.md。

## 2026-10-21 标签迭代32

paper/literature固定1.4.24 / 0.5.18完成第七组10篇单次独立评测，27/52参考及79条引文先冻后预测。一级P78.95/R55.56/F165.22、二级P42.31/R21.15/F128.21，二级不足。综述与扩展摘要型原文保留计分、范围单列；无事后调参，科学源码/测试/包/工作台精确依赖不改。007已用，008与80篇身份无重叠、未读无gold/预测。同步评测接口/说明及模块登记，不改工具审查基线或生产服务。报告paper/reports/20261021-tagging-iteration-032.md。

## 2026-10-21 标签迭代33

paper/literature0.5.19候选1.4.25补联合LC/GC-MS明确揭示降解产物的结果句实际使用证据，保留编号文献/历史/否定/推测边界及未准入观察；不改一般FOCUS/METHOD_USE、核心排序、词表或输入。227项局部通过，八组80篇开发补1个正确二级、误标不增、一级不变。无新独立成绩，1.4.24独立007仅历史、008封存。同步工作台精确依赖/说明与模块登记，不改工具审查基线或生产服务。报告paper/reports/20261021-tagging-iteration-033.md。

## 2026-10-21 标签迭代34

paper/literature0.5.20候选1.4.26消歧期刊/出版年份上下文中的Soc./SOC，真正物理缩写/全称/同段独立命中保留，消歧证据带逐字区间并验证。239项局部通过；八组80篇开发减少1个二级误标、TP/FN/一级不变，另去除3个辅助同类误识。6个非科学接受记录转为提及，原来源不删；不改全局参考文献规则、核心、词表或输入。无新独立成绩，第八组封存。同步工作台精确依赖/说明和模块登记，不改工具审查基线或生产服务。报告paper/reports/20261021-tagging-iteration-034.md。

## 2026-10-21 标签迭代35

paper/literature固定1.4.26 / 0.5.20完成第八组10篇单次独立评测；30/57参考和87条逐字位置先冻后预测。一级P87.50/R46.67/F160.87、二级P81.25/R22.81/F135.62，漏标明显；来源与参考引文完整性限制分别记录，无事后调参。科学源码/239项测试/包/精确依赖不改。008已用、009与90篇身份无重叠且未读无gold/预测。同步离线评测元信息和文档，不改生产服务或工具审查基线。报告paper/reports/20261021-tagging-iteration-035.md。

## 2026-10-21 标签迭代36

paper/literature0.5.21候选1.4.27只增加受控host-for-OLED材料角色别名，具非材料/历史/否定/假设/比较保护和可重算逐字回执；不放开裸host、不改旧别名、二级/核心/输入。251项局部通过，九组90篇开发补回2个一级正确核心、误标不增；其余8组和全部二级不变。v13仍44语义ID及旧评价对应。1376条旧接受原样保留，1旧背景提及保留于原运行和基线。无新独立成绩，历史1.4.26不沿用、009封存。同步精确工作台依赖和模块登记，不改工具审查基线或生产服务。报告paper/reports/20261021-tagging-iteration-036.md。

## 2026-10-21 标签迭代37

paper/literature0.5.22候选1.4.28只补既有发射偶极取向的emitting/emission dipole名词短语正反向别名，新别名复用有界测量否定守卫与可重算逐字回执。263项局部通过，九组90篇开发补回1个二级正确核心、误标不增；一级/其他核心指标不变，另1辅助观察。1378旧接受与269旧提及原样保留；v14仍44语义ID，旧映射不改。旧取向通配跨句的fixture问题原样留档，改为两块测试独立证据，断言保留，原规则未动。无新独立成绩、009封存。同步工作台精确依赖和模块登记，不改工具审查基线或生产服务。报告paper/reports/20261021-tagging-iteration-037.md。

## 2026-10-22 标签五轮试验1/5

paper/literature directions-rules-1.4.29/0.5.23：激子增殖与高能激子利用主题覆盖，90篇开发整体指标单列，新受控术语与一对一同义评价对应先冻结，旧gold/输入不改。270项局部通过，全量门待完成，009封存，无模型或服务重载。报告paper/reports/20261022-tagging-iteration-038.md。

## 2026-10-22 标签五轮试验2/5

paper/literature directions-rules-1.4.30/0.5.24：溶液多层成膜的溶剂正交与膜层耐溶剂覆盖，90篇开发整体指标单列，新受控术语与一对一同义评价对应先冻结，旧gold/输入不改。276项局部通过，全量门待完成，009封存，无模型或服务重载。报告paper/reports/20261022-tagging-iteration-039.md。

## 2026-10-22 标签五轮试验3/5候选未采用

paper/literature1.4.31主体细标开发+2TP/+1FP，重复页眉误标导致子组退化；保留候选证据，当前仍已验收1.4.30。未改gold，未启用模型或原服务。报告paper/reports/20261022-tagging-iteration-040.md。

## 2026-10-22 标签五轮试验4/5

paper/literature directions-rules-1.4.32/0.5.26：光学出耦的主题、问题、模型和角分辨测量覆盖，90篇开发整体指标单列，新受控术语与一对一同义评价对应先冻结，旧gold/输入不改。288项局部通过，全量门待完成，009封存，无模型或服务重载。报告paper/reports/20261022-tagging-iteration-041.md。

## 2026-10-22 标签五轮试验5/5

paper/literature directions-rules-1.4.33/0.5.27：跨页重复页眉与正文科学证据分离，复核保留的主体细标，90篇开发整体指标单列，新受控术语与一对一同义评价对应先冻结，旧gold/输入不改。310项局部通过，全量门待完成，009封存，无模型或服务重载。报告paper/reports/20261022-tagging-iteration-042.md。

## 2026-10-22 文献核心标签五轮完成

当前paper/literature1.4.33/v19/0.5.27：5轮中4采用、1因退化保留。90篇开发一级F171.57→74.00、二级41.48→42.82；新10篇009前后一级F157.14、二级41.67完全相同，未证实新样本收益。参考先于两版预测冻结，旧gold/输入保留，010新封存未读；无模型/全库发布/服务重启。最终310局部/2693次项目执行PASS，状态与汇总报告登记后复核。报告paper/reports/20261022-core-directions-five-rounds.md。

## 2026-10-23：codex_desktop_chat审计材料静态登记

核对发现变化仅为两份新增AUDIT_RUNS静态报告；既有21项源码/合同/测试/说明指纹与已审查基线一致。登记报告来源，工具运行合同与消费者适配未改；不执行报告行动项，不增加实机验收声明。

- 2026-10-23：源码审查 codex_desktop_chat。仅新增两份AUDIT_RUNS静态报告；逐项比较既有源码/测试/接口/说明全部指纹相同、无删除。已阅读新增材料并登记历史身份，不执行建议，不宣称结论验收或新增桌面业务验收。（命令未执行业务验收。）

- 2026-10-23：使用方核对 paper → codex_desktop_chat。上游只增加两份只读审计报告，既有源码及公开合同指纹完全未变；原ZIP/桌面调用适配不变，未开展新桌面业务验收。（命令未执行业务验收。）

- 2026-10-23：使用方核对 chatgpt_playwright → codex_desktop_chat。上游只增加两份只读审计报告，bundles及其所有既有依赖字节与原基线相同；原单ZIP接口适配不变，无新增业务验收。（命令未执行业务验收。）

- 2026-11-27：源码审查 codex_web_client。逐项核对 Python 接口、命令行和原说明，新增跨重启的失败冷却与状态读取，成功时复位。12 项离线回归通过；当前无业务队列接入。（命令未执行业务验收。）

- 2026-11-27：源码审查 codex_web_client。核对 1.1.0 图片冻结与发送时校验、指定任务领取、缺少或拒绝守卫时不发送。原无图调用和状态契约保留。（命令未执行业务验收。）

- 2026-11-27：使用方核对 paper → codex_web_client。OLED 迁移仅选无旧尝试的原队列材料；原所有者已准备 1521 批并在账户守卫处等待。已核对绑定的图页清单，生产实际外发未验收。（命令未执行业务验收。）

- 2026-11-27：源码审查 codex_web_client。已核对原接口、OLED 定向守卫调用、逐尝试模型与回执、三档额度及未知提交回归；实网额度切换未验收。（命令未执行业务验收。）

- 2026-11-27：使用方核对 paper → codex_web_client。OLED App 路由使用原编号、冻结图页和 before_send，指定 pro_first；已检查原排队数据和回执兼容，已跑离线回归。（命令未执行业务验收。）

- 2026-11-27：源码审查 codex_web_client。已核对原接口和三档选择，App 附件/账户配额错误使用跨重启队列冷却，20 项客户端与 App 路由回归通过。（命令未执行业务验收。）

- 2026-11-27：使用方核对 paper → codex_web_client。公式单所有者使用 App 本身的登录探测与受保护派发，已实测第1521批 Pro 首次派发；真实额度耗尽未测试。（命令未执行业务验收。）

- 2026-11-27：源码审查 codex_web_client。已核对默认串行兼容、五个 slot 与 job 双锁、子进程继承锁、容量准入和并发配额冷却；已运行客户端及公式 App 回归。（命令未执行业务验收。）

- 2026-11-27：使用方核对 paper → codex_web_client。公式所有者使用 0..4 独立位置及原批号、冻结材料和发送守卫。回归验证空位补批和汇总串行发布。（命令未执行业务验收。）

- 2026-11-27：源码审查 codex_web_client。health 返回 App 服务 PID 供会话归属核对；未使用服务健康状态替代登录证据。并发、回退及会话变化测试通过。（命令未执行业务验收。）

- 2026-11-27：使用方核对 paper → codex_web_client。App 专用队列核对服务与启动器身份，忙时以近期同会话已确认登录或本队成功回执补位；服务变化重新核对。（命令未执行业务验收。）

- 2026-11-27：源码审查 codex_desktop_chat。按 1.0.0 打包配置和 bundles.default_bundle_dir 核对 ZIP 目录优先级、公开函数及工具卡；50 项离线回归通过。（命令未执行业务验收。）

- 2026-11-27：源码审查 codex_web_client。按 1.3.0+proprobe.1 的 API、接口清单和分发版本核对 run_once 的 allow_pro 与定向并行参数；19 项离线回归通过。（命令未执行业务验收。）

- 2026-11-27：使用方核对 paper → codex_desktop_chat。核对 formula_pilot、formula_only 的打包入口及 collective_page_restart 的 verify_bundle 调用；旧 ZIP 仍按原路径校验。未进行桌面外发。（命令未执行业务验收。）

- 2026-11-27：使用方核对 paper → codex_web_client。核对 oled_formulas/app_queue.py 按批传入 key、before_send、parallel_slot 和 allow_pro，6 项 App 队列隔离回归通过；未派发真实网页任务。（命令未执行业务验收。）

- 2026-11-27：源码审查 codex_desktop_chat。核对本轮相对路径文档及既有调用签名。桌面工具 50 项、Web 客户端 19 项离线回归通过。（命令未执行业务验收。）

- 2026-11-27：源码审查 codex_web_client。核对本轮相对路径文档及既有调用签名。桌面工具 50 项、Web 客户端 19 项离线回归通过。（命令未执行业务验收。）

- 2026-11-27：使用方核对 paper → codex_desktop_chat。核对本轮相对路径文档及既有调用签名。桌面工具 50 项、Web 客户端 19 项离线回归通过。（命令未执行业务验收。）

- 2026-11-27：使用方核对 paper → codex_web_client。核对本轮相对路径文档及既有调用签名。桌面工具 50 项、Web 客户端 19 项离线回归通过。（命令未执行业务验收。）
