# 工具登记与检查

从本目录执行以下命令，需要 Python 3.10 或更高版本。源码引用、维护方和使用方见[登记表](../registry.json)，各项目的依赖清单见[项目索引](../projects.json)。

```sh
python3 check_links.py
python3 sync_tools.py check
```

第一条检查源码基线、工具说明及双向关系，第二条还列出待更新的快照。退出码 0 表示通过，1 表示有待处理项，2 表示配置或执行错误。

## 接入项目

调用方在自己的 AGENTS.md 中链接[工具目录](../README.md)或具体工具的 README，按工具说明调用。要登记实际跨项目依赖，可在此运行以下命令，将最后一个参数替换为已有项目目录。

```sh
python3 sync_tools.py install --project ../../项目名
```

登记命令保留项目原有规则，补充工具入口，建立 tool-dependencies.json，并在中央 projects.json 登记项目。新建相邻项目也可以运行本目录的 `./新建项目.command "项目名"`。依赖清单的 exports 填本项目维护的工具，tools 填实际使用的工具，module_dependencies 填跨项目模块引用。

## 更新接口

1. 查登记表中的 owner_project 和 consumers，在权威源码中修改接口。新增工具时按[工具说明模板](工具说明模板.md)编写一级目录的 README，更新总目录和登记表。相对链接按所在文件解析。
2. 同步项目依赖清单、适配代码和验证记录，运行 `python3 sync_tools.py update`。该命令刷新反向登记、各工具目录内的接口快照及报告。它读取各项目的 AGENTS 声明。
3. 出现源码漂移时，对照实现、工具说明和使用方。核对后运行 `python3 sync_tools.py accept --tool ID --note "核对依据"`。使用方确认适配后运行 `python3 sync_tools.py acknowledge --project 项目名 --tool ID --note "核对范围"`。实际业务验收另记验证日期与回执。
4. 再运行 update 和本页开头的两条检查。Mac 和 Windows 也可以用同目录的全局更新启动文件执行 update 或 check。

本机工具箱的报告在 `~/process/tools/updates/`，更新前的备份在 `~/process/tools/backups/`，反向索引见 `~/process/tools/reverse-index.json`。其他检出目录各自使用独立的状态目录，测试和临时导出可用 TOOLS_STATE_DIR 指定隔离位置。
