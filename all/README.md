# all：新项目只需携带的工具接入包

把本目录完整复制到新项目根目录，保留名字 `all`，然后在新项目执行一次：

```bash
python3 all/setup.py
```

脚本保留已有文件内容，自动在根目录 AGENTS.md 加入受管理的联动规则块，创建或保留 tool-dependencies.json，并在 tools/projects.json 登记项目。无需再手工复制模板或修改中央索引。仅复制目录不会执行程序，也不会让目录内规则自动作用于外部业务文件，所以首次接入要运行上述命令。

实际代码仍在权威源码项目维护，all 不包含工具源码、模型、登录态或业务数据。项目特有规则放在根 AGENTS.md 的受管理块之外；不要改本目录的受管理文件，需要通用修改时改 tools/all 后执行全局更新。

## 修改接口后必须运行

```bash
python3 ../scripts/sync_tools.py update
```

在当前 Mac 也可直接运行或双击 tools 根目录的 `全局更新.command`。只检查、不写文件：

```bash
python3 ../scripts/sync_tools.py check
```

具体开发规则见 [RULES.md](RULES.md)。换电脑或移动 tools 后，设置 TOOLS_HOME，或修改 hub.json 中的 tools_root；规则和命令的实际路径在安装时由中央脚本生成。

## 更新做什么

自动扫描所有已登记工具和项目，分发最新 all 公共规则、修复派生的反向登记、生成源码接口快照和 updates/latest.md 报告。不会执行工具业务、自动改业务适配代码或把未测试版本标记为已验收。

源码变化时，先运行 update，检查报告和真实实现，更新对应工具卡及原接口说明，完成必要验证后执行：

```bash
python3 ../scripts/sync_tools.py accept --tool 工具ID --note "具体变更、已核对的说明、实际验证与限制"
python3 ../scripts/sync_tools.py update
```

accept 表示开发者已经完成源码/说明审查，不自动宣称业务验收；全局使用方会标为需要重新核对。使用方确认适配后，按 RULES.md 完成依赖核对。不能只执行 accept 来清除告警。

例如登记某使用方的静态适配核对：

```bash
python3 ../scripts/sync_tools.py acknowledge --project 项目名 --tool 工具ID --note "适配层已核对的内容与未验证的限制"
```

命令需要 Python 3.10+。更新前自动保存元数据旧文件到 tools/.sync-backups；重复运行且内容无变化时不写文件。本地修改的公共规则会被保留并报冲突，合并后重试。hub.json 是安装位置配置，接入/更新时会按实际 tools 位置重写。

exit 0：本轮更新/检查完成且无待办；exit 1：有待审查、接入核对或尚未同步的内容；exit 2：配置、权限或文件冲突。更新已执行但仍有待办时也返回 1，详细结果看报告。
