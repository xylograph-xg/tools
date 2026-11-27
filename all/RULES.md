# 可复用接口开发与全局更新规则

1. 开发前读 tools/README.md、registry.json 和相关工具卡，优先复用适合的能力。通用功能与页面/业务流程分离；输入、输出、错误、默认值、超时、并发和副作用写清楚。只将适合复用的能力提取为接口。
2. 项目关系记在根目录 tool-dependencies.json：exports 为维护的登记工具，tools 为使用的登记工具，module_dependencies 为尚未独立登记的模块引用。新工具先按 tools/docs/工具新增与维护规范.md 完成实现、说明和验证，再登记；不要把审核候选当成现成工具。
3. 修改接口、配置、依赖、路径或数据契约时，同一任务更新权威源码与说明、tools 工具卡/registry/CHANGELOG，以及受影响的使用方适配与记录。公共源码只有一个维护位置。历史 audits 是快照，不覆盖旧证据。
4. **修改接口后必须调用全局更新命令**：`python3 ../scripts/sync_tools.py update`，或运行 tools/全局更新.command。命令同步所有已登记项目的公共规则、接口快照和派生登记；根 AGENTS.md 中也会生成当前安装路径下的命令。
5. 发现源码漂移后，逐项审查 updates/latest.md 与 tools/<id>/INTERFACE.generated.md，核对真实实现、原接口说明、工具卡和使用方。完成后执行 `sync_tools.py accept --tool <id> --note "具体核对及验证说明"`。这只记录源码审查；真实生成、网络、数据库等未运行时不得宣称已验收。
6. 使用方重新检查适配层和配置后，执行 `sync_tools.py acknowledge --project <项目名> --tool <id> --note "使用方静态核对结果与限制"`。它只记录静态核对，不触发业务调用；真实端到端验收另由项目记录验证日期、源码版本及结果。
7. 任务结束再运行全局 update 和 `python3 ../scripts/check_links.py`。最终说明列出两端实际修改、检查结果与待办。权限/冲突/未验证部分不能隐藏；不得只刷新摘要绕过核对。
8. all 中的公共文件由 tools 管理；项目定制写到根 AGENTS.md 受管理块之外。全局更新遇到用户改过的公共文件时停止并保留原文件，合并后再运行。命令不监听后台变化、不安装 Git hook、不提交/推送 Git。
