# Codex App Chat：跨项目调用说明

工具 ID：`codex_desktop_chat`，版本1.0.0，source-reference。权威源码位于 [/Users/xiaoyanhao/project/paper/codex_desktop_chat](/Users/xiaoyanhao/project/paper/codex_desktop_chat)，原创实现使用 Apple 公共 AX/Unicode API，不依赖探索阶段的 npm/GitHub 工具。

完整契约、并发示例、错误恢复见[调用说明](/Users/xiaoyanhao/project/paper/codex_desktop_chat/调用说明.md)，参数见[input.schema.json](/Users/xiaoyanhao/project/paper/codex_desktop_chat/input.schema.json)。

运行条件：macOS、Python >=3.11、Swift编译器、已登录 Codex App Chat、辅助功能权限。首次编译按源码哈希缓存；无第三方 Python 依赖。将 `/Users/xiaoyanhao/project/paper` 加入调用方 PYTHONPATH。

```python
from codex_desktop_chat import ask_once
answer = ask_once("只回复 OK", foreground=True, state_dir="/absolute/private/receipts")
```

```bash
PYTHONPATH=/Users/xiaoyanhao/project/paper python3 -m codex_desktop_chat status
```

`ask_once`/`ask`返回完整字符串；`submit`返回持久回执、`collect`只收取原窗口。默认 GPT-6 High、10秒轮询、收取900秒；显式可选 GPT-5.6 Sol High，无自动回退。错误抛 DesktopChatError，包含 code/receipt_id/may_have_sent；CLI单JSON、成功0/错误2。未给 foreground=True 的新建/发送返回 foreground_required，不作隐式前台操作。

允许多会话同时生成；新建、切换、输入、提交用跨进程短锁。默认创建独立窗口，总原生窗口最多20（包括用户窗口），已有草稿和未知请求受保护。Unicode输入不使用剪贴板，发送前核对完整输入和模型。完成窗口保留可复用，不自动关窗；状态与回答写私有目录。超时预算仅收取阶段；未知回执只核对原窗口和指纹，禁止重发。`files`支持最多10个绝对路径；每文件本地保护64MiB，总128MiB。上传就绪需名称集合一致、无进度/失败和发送可用，稳定两次；真正发送前原生再次核对，上传等待不持锁。文本/附件/回答指纹私有留存，匿名图片核对原用户消息图片数量并绑定前述完整上传/发送证据。

2026-10-08：16项隔离测试通过；单窗口中文和双窗口同时生成/分别完整收取通过；其他工作目录 CLI status/已完成回执收取通过。0.1.0当时附件、科学质量、20路与长期无人值守未验收；主制卡通道未切换。后续修改须更新权威说明、本卡、registry、CHANGELOG及消费方，运行全局 update/accept/acknowledge/check_links。

## 0.2.0 附件验证

2026-10-08：32项原接口/附件合同测试通过；两个独立真实窗口各自上传不同PNG，返回对应token并完整收取。早先unknown请求仅在原窗口核对收取，没有重发。图片正式回执不显示文件名，采用已验证不可变图片输入+上传就绪/发送前集合检查+原用户消息的图片数量核对。PDF、多附件真实回答、20路及常驻仍未验收。

```python
receipt = chat.submit("读取附件", files=["/absolute/A.pdf", "/absolute/A.png"], upload_timeout=180)
answer = chat.collect(receipt, answer_timeout=900)
```

文件面板入口使用已核对控件位置的原生点击，前台操作需要明确授权。文件副本和回执保留私有目录用于未知请求核对。已观察App附件额度用完，`channel/issue.json`持久记录并阻止继续附件提交；显式 `verify_attachment_channel()` / CLI `verify-attachments --window-id ... --state-dir ...`只核对原提示窗口，提示消失才解除本地阻止，不能保证网站上传恢复。原生失败/超时不自动清除草稿或重试。

## 0.3.0 默认单ZIP

用户要求附件集中预存ZIP，新增prepare_upload_bundle与CLI prepare，默认 `<python_import_root>/data/app-upload-zips`，可用bundle_dir/CODEX_CHAT_ZIP_DIR设置。同一材料集合按内容指纹复用，不覆盖旧包，临时包失败清理；包中原字节+名称/大小/哈希清单，无机器路径。已有ZIP校验后直接预存，不套ZIP。

files输入自动先打包，实际仅上传一个ZIP，回执保存包/输入证据，失败不回退散文件。默认行为取代0.2.0逐个附件上传，原示例中的files仍可使用。38项隔离测试与跨目录本地prepare通过；本次没有新上传。ZIP服务端解压及读取尚未验收，历史双PNG不代表ZIP验收；额度和未知回执保护继续有效。

## 2026-10-13 独立子项目与API入口

原根导入、ask/submit/collect签名和唯一源码位置保持。新增可选 `codex_desktop_chat.api`，接口与完整实现清单见 [源码项目README](/Users/xiaoyanhao/project/paper/codex_desktop_chat/README.md) 和 [interface.json](/Users/xiaoyanhao/project/paper/codex_desktop_chat/interface.json)。网页制卡/核验只复用ZIP准备/校验，桌面操作仍需原显式授权。测试已迁入工具自己的tests；本轮只有离线回归、接口身份和构建验证，没有新真实桌面Chat、ZIP上传或科学验收。

## 八项目归并下的ZIP目录

公开签名和独立工具源码根保持。默认ZIP目录从workspace.json的physical_roots.data取得，当前为paper/infrastructure/data/app-upload-zips；无工作区清单时保留原data/app-upload-zips，CODEX_CHAT_ZIP_DIR仍优先。工具不依赖core。1761项离线回归及307接口对象身份检查通过；本轮没有新的桌面调用、上传或科学验收。


## 2026-10-14 审计整改

缓存命中同时核对当前源清单/ZIP整体哈希，独占发布不覆盖旧证据；verify_bundle新增manifest_files字段。ZIP特殊条目拒绝。桌面回答按原轮次收取，历史完成标志无效，缺锚点仅只读等待；Python/Swift均在UI副作用前要求授权，回执阶段禁止倒退。Wheel显式分发native.swift与schema。50项离线回归、Swift编译、14组件/307出口检查通过，真实App/复杂AX保真/ZIP读取未新验收。详情见[复核记录](/Users/xiaoyanhao/project/paper/codex_desktop_chat/AUDIT_REVIEW.md)。

## 2026-10-14：paper剩余页面恢复合同

paper/browser通过codex_desktop_chat公开verify_bundle只读核对已登记、从未提交nonce候选恢复的ZIP清单、内容与包名指纹，支持Chrome数字后缀；原请求有账本时必须核对原packet绑定，不能借公共缓存绕过。review公开check_packet统一核对旧核验ZIP证据，新账本记录upload_bundle，旧冻结字节保留。空换行与真实草稿区别处理，已验证原ledger-before归档保持相同SHA/target；未知材料不重发。第05槽新创建epoch仍需具体单次授权，默认禁用。本轮无新增桌面Chat调用或科学验收。

2026-10-14 文档路径核对：paper 八项目归并后，模块 README 的离线测试命令改用 infrastructure/environments/test 与 infrastructure/maintenance/test_runner.py；全局边界检查为 make check。工具公开参数及使用方适配未改，本轮没有新的桌面外发或上传。

2026-10-14：源码目录新增[AUDIT.md](/Users/xiaoyanhao/project/paper/codex_desktop_chat/AUDIT.md)，属于静态审计材料；本次登记仅核对新增说明，公开实现、ZIP接口和消费方参数均未变化，不表示报告建议已实施或桌面实机验收通过。

2026-10-18 登记维护：已删除的历史审计 MD 依 paper 删除指纹清单退出当前源码清单；历史验证叙述仍保留，生产 Python/Swift/ZIP 接口不因此变更。本项无新增 UI/上传验收。

## 2026-10-23：只读审计材料登记

源码目录新增两份`AUDIT_RUNS/20261023-134830-a2a94b/AUDIT.md`与`AUDIT_RUNS/20261023-140721-ff0c07/AUDIT.md`，均为只读静态审计记录。与原工具基线逐文件核对：既有源码、测试、接口和说明字节全部相同，没有删除文件或改变调用合同。将新增材料登记为历史报告，不据此执行其中建议或宣称建议已验证。paper与chatgpt_playwright既有调用无需代码适配，本轮没有新增桌面App、附件或模型业务验收。

本工具的 OLED 配套 wheel 可从[集中安装目录](../../distributions/oled-formulas/README.md)取得。
