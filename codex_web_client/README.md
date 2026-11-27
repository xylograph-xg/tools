# Codex Web GPT 的 Python 客户端

工具编号为 `codex_web_client`，维护方为 paper，采用唯一源码引用。版本 1.3.0+proprobe.1 提供持久提交、默认串行和定向并行派发、原回执查询和可选结果核对。[权威使用说明](codex_web_client/README.md)　[接口清单](codex_web_client/interface.json)

在 macOS 使用 Python 3.9+，运行时只依赖标准库。实际网页任务由 PATH 中的 Codex CLI 和已登录、Full 模式且已接入 Codex Native2 的桌面应用执行。默认本机端口 17841，可设置状态目录、端口、超时。状态目录由当前用户独占。

```sh
python3 -m pip install codex_web_client
python3 -m codex_web_client status
python3 -m codex_web_client submit probe-001 --prompt 'Return exactly OK' --expected OK
python3 -m codex_web_client work --once
python3 -m codex_web_client get probe-001
```

Python 使用 `from codex_web_client.api import Client`。重复编号与相同参数返回原回执。默认工作进程串行。待复核后的新派发跨重启冷却 30 秒，连续故障最长延至 300 秒。空队列返回 idle，服务离线返回 unavailable 并保留队列，证据缺失的请求进入 review。常驻循环由调用者显式运行。输入和证据保存于本机，派发会在真实网页产生任务。

2026-11-27 实测桌面 6.2.0。核对了随机文件读取和 JSON 预期字段，实测错误字段被保留待复核。12 项离线回归通过，覆盖短时单机运行，未做全天耐久测试。上游为 MIT 许可证，本包通过正常客户端入口调用。[上游源码](https://github.com/miuuyy/codex-chatgpt-web/tree/232cddd)

OLED 客户端逐批传递冻结图页并指定任务编号，`before_send` 在实际发送前检查账户、原文、临时聊天和暂停状态。

受保护的分档派发使用 pro_first=True。allow_pro=False 只在 GPT-6.2 Sol Extra High、High 中按额度选择；allow_pro=True 保留 GPT-6 Pro 优先。明确未发送的模型专属额度错误允许原批继续，其他不确定提交存入复核。
App 返回明确的账户或附件额度错误时，整个公式 App 队列至少冷却 15 分钟，保留原批回执。

OLED 公式队列在同一 App 所有者下使用五个并行位置。run_once(key=..., before_send=..., pro_first=True, parallel_slot=0..4) 分别锁定批号和位置，默认串行工作进程与并行模式互斥。各批独立收取，所有者依次发布单篇结果，并在空位补入待办。实际 App 活动数读取 /healthz 的 active_browser_turns。

本工具的 OLED 配套 wheel 可从[集中安装目录](../oled-formulas/README.md)取得。
