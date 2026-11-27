# 独立桌面Chat与通用ZIP接口

原生文本/附件、窗口归属、模型核对、未知提交保护、完整收取、附件额度及内容寻址ZIP。

这是独立源码与接口文件夹，正式包名为 `codex_desktop_chat`。跨项目只调用 `codex_desktop_chat.api` 或本项目声明的CLI/JSON接口；不存在跨目录源码链接。

## 为什么选择、为什么保留

主科学任务使用GPT网页；此登记工具保留，因为制卡/核验的ZIP准备和核对实际依赖它。桌面交互仍须原显式前台授权，不随整理启动。原工具源码与公开根导入保持兼容。

## 接口与运行

- [interface.json](interface.json)：版本、依赖、全部公开出口及真实实现签名。
- [api.py](api.py)：接口入口，返回原函数/类对象，保留参数、异常与共享对象身份，不另复制实现。
- [pyproject.toml](pyproject.toml)：可单独构建/安装的Python子项目。

公共符号以 `模块__符号` 命名，避免各模块的 `status`、`enabled` 等同名函数冲突；模块出口用于保留已有有状态接口。调用参数、返回值与异常见真实函数签名及源码，不由适配层改写。

```python
from codex_desktop_chat.api import bundles__prepare_upload_bundle
```

运行依赖：不依赖其他业务子项目；ZIP缓存位置使用原bundle_dir / CODEX_CHAT_ZIP_DIR合同。

从 paper 根目录按需运行：

```sh
PYTHONPATH=infrastructure/bootstrap:.:../chatgpt_playwright infrastructure/environments/test/bin/python infrastructure/maintenance/test_runner.py --project codex_desktop_chat
make check
```

可用支持PEP 517/660的安装器按本目录 `pyproject.toml` 独立安装。独立安装时显式提供bundle_dir / CODEX_CHAT_ZIP_DIR及桌面回执state_dir；宿主负责安装声明的接口依赖；当前运行环境沿用现有虚拟环境，避免目录整理触发依赖重装或服务重启。

## 内部全部实现与功能

以下清单列出本项目每份实现及其顶层函数、类和类方法；测试、说明与配置在下节单列。辅助内部函数不是跨项目授权出口。

| 文件 | 功能 | 内部函数 / 类方法 | 保留原因 |
| --- | --- | --- | --- |
| [backend.py](backend.py) | Private macOS transport. JSON over stdin; no shell interpolation or clipboard. | `NativeBackend[__init__, _helper, call, snapshot, press, type_text, escape]` | 当前公开接口或生产链使用；避免复制实现 |
| [调用说明.md](调用说明.md) | 接口、配置或启动入口 | 静态资源 / 声明 / 执行入口 | 当前公开接口或生产链使用；避免复制实现 |
| [native.swift](native.swift) | 原生任务面板与按钮 | 静态资源 / 声明 / 执行入口 | 当前公开接口或生产链使用；避免复制实现 |
| [input.schema.json](input.schema.json) | 接口、配置或启动入口 | 静态资源 / 声明 / 执行入口 | 当前公开接口或生产链使用；避免复制实现 |
| [bundles.py](bundles.py) | Local, content-addressed ZIP preparation. Never opens an app or sends data. | `default_bundle_dir`、`_hash_file`、`verify_bundle`、`prepare_upload_bundle` | 当前公开接口或生产链使用；避免复制实现 |
| [core.py](core.py) | Desktop Chat sessions. Each owns a window; only short UI operations serialize. | `_sha`、`_now`、`_label`、`_visible`、`_find`、`_query`、`_answer`、`_busy`、`_complete`、`ChatGPTDesktop[__init__, __enter__, __exit__, _require, _snapshot, _press, _empty_draft, _start_new_chat_locked, start_new_chat, _verify_settings_locked, verify_settings, submit, collect, ask, _stored_attachment_issue, verify_attachment_channel, status]` | 当前公开接口或生产链使用；避免复制实现 |
| [attachments.py](attachments.py) | Attachment snapshots, composer evidence, and native picker selection. | `validate_files`、`snapshot_files`、`verify_snapshots`、`_descendants`、`composer_nodes`、`attachment_names`、`upload_evidence`、`choose_file`、`image_file_names`、`formal_attachment_evidence`、`channel_issue` | 当前公开接口或生产链使用；避免复制实现 |
| [api.py](api.py) | 公开接口入口，延迟返回唯一实现对象 | `__getattr__`、`__dir__` | 当前公开接口或生产链使用；避免复制实现 |
| [errors.py](errors.py) | All failures distinguish whether a request may already have been sent. | `DesktopChatError[__init__, as_dict]` | 当前公开接口或生产链使用；避免复制实现 |
| [__main__.py](__main__.py) | CLI stdout is exactly one JSON result; status never submits or creates a chat. | `main` | 当前公开接口或生产链使用；避免复制实现 |
| [state.py](state.py) | Durable receipts and one global lock for the shared desktop window. | `atomic_json`、`ReceiptStore[__init__, path, save, load, pending]`、`desktop_lock` | 当前公开接口或生产链使用；避免复制实现 |

## 测试、说明及配置清单

- [pyproject.toml](pyproject.toml)：当前接口使用说明或配置；实际规则以AGENTS和实现为准。
- [interface.json](interface.json)：当前接口使用说明或配置；实际规则以AGENTS和实现为准。
- [tests/__init__.py](tests/__init__.py)：离线/隔离回归，验证当前合同。
- [tests/test_codex_desktop_chat.py](tests/test_codex_desktop_chat.py)：离线/隔离回归，验证当前合同。
- [tests/test_codex_desktop_bundles.py](tests/test_codex_desktop_bundles.py)：离线/隔离回归，验证当前合同。
- [tests/test_codex_desktop_attachments.py](tests/test_codex_desktop_attachments.py)：离线/隔离回归，验证当前合同。
- [tests/test_audit_regressions.py](tests/test_audit_regressions.py)：真实文件与模拟AX回归，验证错误缓存、并发发布、多轮、历史完成、延迟锚点与授权。
- [examples/ask_codex_chat.py](examples/ask_codex_chat.py)：当前接口使用说明或配置；实际规则以AGENTS和实现为准。

## 数据、并发和权限边界

ZIP接口只做文件打包/校验；桌面交互接口需要显式授权，未知提交不重发。 原文、卡片、冻结输入、回执与人工决定保留原存储位置。暂停、原文/版本身份、真实领取、未知提交不重发及科学验收要求不变。接口导入、测试或文档阅读不构成启动/外发授权。

当前配置入口是 [config](../../../paper/infrastructure/config/README.md)，共享状态合同见 [data](../../../paper/infrastructure/data/README.md)。共用Catalog通过core API持有事务；不复制数据库、锁或共享浏览器所有者。

## 已删除与保留的证据

旧独立模型实验、旧Streamlit/旧article应用、重复符号链接、旧平铺测试和旧一次性迁移脚本已删除；本项目测试已使用正式包名。逐文件删除原因与指纹见 [清理审查](../../../paper/reports/physical-isolation-cleanup.json)。历史评审和原授权用于追溯原请求，保留不表示可恢复旧任务。

## 八项目布局下的ZIP目录

bundles.default_bundle_dir仍优先使用CODEX_CHAT_ZIP_DIR；在此工作区默认使用 ~/process/app-upload-zips。独立拷贝工具且没有workspace.json时仍使用原data/app-upload-zips，不依赖core或其他业务实现。未进行新的桌面调用或上传。


## 2026-10-14 审计修复

依据[复核与整改记录](AUDIT_REVIEW.md)实施缓存来源绑定、原轮次收取、延迟锚点等待、双层UI授权、ZIP类型检查、回执阶段校验与安装资源打包。verify_bundle新增manifest_files（无manifest时null），原签名保持。Python要求3.11+，包版本1.0.0；接口与回执协议仍为1。

新增文件：
- [tests/test_audit_regressions.py](tests/test_audit_regressions.py)：真实文件与模拟AX回归，验证错误缓存、并发发布、多轮、历史完成、延迟锚点与授权。
- [AUDIT_REVIEW.md](AUDIT_REVIEW.md)：逐项真实性、调整方案、验证范围与实机限制。

新增内部实现：bundles._publish以独占硬链接原子发布；core._response_span绑定原轮次，_authorize_ui阻断副作用；state.Receipt/Stage/TRANSITIONS声明回执合同。原有组件保留理由不变。
