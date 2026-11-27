# Codex Web GPT 的 Python 工具包

用 Python 提交任务、查询状态并读取回答。队列保存在本机 SQLite，默认逐笔使用 GPT‑6.2 Sol High。支持 macOS，Python 3.9+，运行时只使用 Python 标准库。网页和 MCP 的实际执行需要已启动并登录的 Codex Web GPT、Full 模式、已连接的 Codex Native2，以及 PATH 中可运行的 Codex CLI。实测桌面版 6.2.0。网页临时聊天可开启。本地 Codex 使用常规任务记录，供应用核对权限。

## 从任意目录使用

在自己的 Python 环境执行一次安装，或在项目根目录直接运行以下模块命令。

```sh
python3 -m pip install .
python3 -m codex_web_client status
python3 -m codex_web_client submit example-001 --prompt 'Return exactly WEB-OK' --expected WEB-OK
python3 -m codex_web_client work --once
python3 -m codex_web_client get example-001
```

持续处理队列可运行 `python3 -m codex_web_client work`，Ctrl-C 退出。应用暂时离线时，已排队的任务保存在磁盘，工作进程按 1、2、4 秒递增至最多 30 秒再次探测。工作进程重启后继续读取相同队列。退出终端或电脑重启后需再次启动工作进程。已登录时，桌面显示 **No active task** 表示当前没有显示任务页；`status` 返回应用是否就绪、正在处理的网页任务数，以及本工具包各状态的任务数。

## Python 调用

```python
from codex_web_client.api import Client

client = Client()
client.submit("check-paper-A", 'Return only this JSON object {"paper":"A","page":2}',
              json_match={"paper": "A", "page": 2})
receipt = client.run_once()  # 领取队列中最早的任务
result = client.get("check-paper-A")
print(result["state"], result["answer"])
```

`Client(state_dir=..., port=17841, timeout=240)` 只连接本机回环地址，端口范围 1–65535，每次 Codex 运行超时 1–86400 秒。默认状态目录为 `~/.local/state/codex-web-client`，必须私有（0700）。所有生产者和工作进程应使用同一状态目录和端口。CLI 同名全局选项放在子命令之前。默认工作目录为每笔任务单独创建的目录。给 `submit` 指定 `workdir` 或 CLI 的 `--workdir` 可读取已有文件；调用者负责保持输入文件版本稳定。输入提示可从 UTF-8 文件使用 `--prompt-file` 读取。测试文件或目录由你选择，应用会按提示处理所请求的内容。

### 验收和任务状态

| 状态 | 含义 |
|---|---|
| queued | 已持久入队，等待派发 |
| sending | 已写入派发意图，正在执行或等待重启核对 |
| answered | 收到完整且与本地回答文件一致的文本 |
| executed | 要求命令执行，观察到至少一条成功完成的本地命令，并收到了完整回答 |
| verified | 完整回答满足调用者指定的验收条件。若同时要求命令执行，也已满足 |
| review | 回答、工具执行、收取或退出证据不足，保留结果及原回执供核对 |
| not_sent | 已确认启动失败，或领取前发现指定工作目录不存在 |

`--expected` 逐字核对回答（忽略回答首尾空白）。`--json-match '{"paper":"A","page":2}'` 要求回答是无重复键的 JSON 对象，逐项核对指定顶层字段与值，允许其他字段。两者任选其一。需要命令证据时额外加 `--require-command`，仅识别 Codex 的成功本地命令事件。公式、引用或业务完整性还需由调用方按原文验收。

重复提交相同任务编号和相同参数会返回原记录。编号冲突会报错；输出未知或不合格的记录保留在 review，工具包不会为它再次发起任务。不同编号表示不同任务。一笔进入 review 后，随后尚未发送的任务先冷却 30 秒。连续出现问题时逐次加倍，最多 300 秒。冷却时间跨进程重启保留，一次成功收取后复位。每个状态目录通过跨进程文件锁只派发一笔。进程中断后，下一次 work 优先核对遗留回执。确认客户端正常退出、收到结束事件且两个回答副本一致时，才可按原验收条件结算。

`health()` 查询应用，`counts()` 汇总队列，`dispatch_status()` 返回连续待核对数及最早下次派发时间（Unix 秒），`get(key)` 读取持久回执。空队列的 work 返回 idle，另一进程持锁返回 busy，依赖缺失或服务未就绪返回 unavailable。work --once 成功处理或空队列退出 0，阻塞或需要复核退出 1，非法参数与未知编号退出 2。每笔任务保留原始事件、回答、诊断文件以及 SQLite 中的请求和结果，目录内可能含业务内容。磁盘空间需按实际任务量管理。

## 文件与验证

| 文件 | 用途 |
|---|---|
| api.py、__init__.py | Python 入口、持久化、派发、结果验收 |
| __main__.py | 状态、入队、单次或连续工作、查询命令 |
| interface.json、pyproject.toml、setup.cfg | 接口清单、版本及安装配置 |
| tests/test_client.py、tests/__init__.py | 回归测试与测试包入口 |
| README.md | 运行依赖、调用示例和验收规则 |

离线测试可在项目根目录运行 `python3 -m unittest discover -s codex_web_client/tests`。上游源码核对版本为 232cddd，许可证 MIT。本包从正常客户端入口调用应用。[上游项目](https://github.com/miuuyy/codex-chatgpt-web)

1.1 支持 `submit(images=[...], guarded=True)` 冻结有序图像指纹，`run_once(key=..., before_send=...)` 定向领取并在发送前重核。回调返回原因时任务保留排队。受保护任务通过普通命令行领取时不会发送。

受保护的分档派发使用 pro_first=True。allow_pro=False 只在 GPT-6.2 Sol Extra High、High 中按额度选择；allow_pro=True 保留 GPT-6 Pro 优先。明确未发送的模型专属额度错误允许原批继续，其他不确定提交存入复核。
App 返回明确的账户或附件额度错误时，整个公式 App 队列至少冷却 15 分钟，保留原批回执。

OLED 公式队列在同一 App 所有者下使用五个并行位置。run_once(key=..., before_send=..., pro_first=True, parallel_slot=0..4) 分别锁定批号和位置，默认串行工作进程与并行模式互斥。各批独立收取，所有者依次发布单篇结果，并在空位补入待办。实际 App 活动数读取 /healthz 的 active_browser_turns。
