"""Export reviewed commits into an empty directory for the public project repository."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import shutil

HUB = Path(__file__).resolve().parents[1]
PROJECTS = ("paper", "plot", "tools", "oled_doi_downloader", "oled_literature_traverser")
# These are private evidence, machine setup, binary releases, or independently sourced packages.
OMIT = {
    "paper": ("audit_reports", "reports", "infrastructure/docs", "infrastructure/data-contract",
              "fetch/dependencies/fetchpdf", "workbench/vendor/runtime-status.json",
              "oled_formulas/unavailable-slot-authorization.json", "oled_formulas/audit-review-items.json",
              "infrastructure/config/review_samples.json", ".github"),
    "tools": ("audits", "updates", "distributions", "CHANGELOG.md", "scripts/export_public.py",
              "docs/公开源码发布.md"),
    "plot": ("AUDIT-2026-11-21.md",),
}
REPORT_SOURCE = {"__init__.py", "api.py", "release.py", "pyproject.toml", "Makefile"}
SESSION = re.compile(r"(https?://(?:chatgpt\.com|chat\.openai\.com)/(?:c|share)/)([0-9a-fA-F-]{32,36})")
MANIFEST_KEYS = {"schema_version", "project_name", "project_root", "registry_path", "projects_index_path",
                 "rules_path", "exports", "tools", "module_dependencies", "external_dependencies", "check_command"}


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def included(project, name):
    if project == "paper" and name.startswith("reports/"):
        return name.removeprefix("reports/") in REPORT_SOURCE or name.startswith("reports/tests/")
    if project == "paper" and name.startswith("fetch/dependencies/fetchpdf/"):
        return name.split("/")[-1] in {"UPSTREAM.json", "LICENSE"}
    if any(name == item or name.startswith(item + "/") for item in OMIT.get(project, ())):
        return False
    parts = Path(name).parts
    return (Path(name).name != "AGENTS.md" and "AUDIT_RUNS" not in parts
            and not any(x.startswith(".env") for x in parts)
            and Path(name).suffix.lower() not in {".zip", ".whl", ".pdf", ".db", ".sqlite", ".sqlite3", ".log", ".pem", ".key"})


def public_text(project, name, text):
    if name.endswith("/tool-dependencies.json"):
        data = json.loads(text)
        data = {k: v for k, v in data.items() if k in MANIFEST_KEYS}
        for row in data.get("tools", []):
            row.pop("verification_history", None)
        text = dump(data)
    elif project == "paper" and name == "infrastructure/config/first_round.json":
        data = json.loads(text)
        data["pdf_retrieval"]["contact_email"] = ""
        for key in ("automatic_schedule_enabled", "tailscale_enabled", "workbench_passwordless"):
            data[key] = False
        for section in ("web_cards", "automatic_issue_handling", "manual_literature"):
            data[section]["enabled"] = False
        for key in ("original_put_http1", "manual_seed_trials"):
            data["web_cards"][key] = {"enabled": False}
        text = dump(data)
    elif project == "tools" and name == "registry.json":
        data = json.loads(text)
        for row in data["tools"]:
            row.pop("wheel_distribution", None)
            row.pop("verification_history", None)
        text = dump(data)
    # Test fixtures keep stable identities without publishing the original conversation IDs.
    text = SESSION.sub(lambda m: m[1] + "00000000-0000-4000-8000-" +
                       hashlib.sha256(m[2].encode()).hexdigest()[:12], text)
    return text


def copy_sources(project, destination):
    repo = HUB.parent / project
    commit = subprocess.check_output(["git", "-C", repo, "rev-parse", "HEAD"], text=True).strip()
    raw = subprocess.check_output(["git", "-C", repo, "archive", commit])
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for entry in archive:
            name = entry.name
            if not entry.isfile() or not included(project, name):
                continue
            if Path(name).is_absolute() or ".." in Path(name).parts:
                raise ValueError(f"非法归档路径 {name}")
            target = destination / project / name
            target.parent.mkdir(parents=True, exist_ok=True)
            content = archive.extractfile(entry).read()
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                if target.suffix not in {".woff2", ".png"}:
                    raise ValueError(f"需审核的二进制文件 {name}")
            else:
                content = public_text(project, name, text).encode()
            target.write_bytes(content)
            target.chmod(0o755 if entry.mode & 0o111 else 0o644)


def rebuild_index(destination):
    """Index only source files present in the public edition, leaving private baselines intact."""
    hub = destination / "tools"
    registry_file = hub / "registry.json"
    registry = json.loads(registry_file.read_text())
    for tool in registry["tools"]:
        source = hub / tool["source_dir"]
        hashes = {name: hashlib.sha256((source / name).read_bytes()).hexdigest()
                  for name in tool["source_files_sha256"] if (source / name).is_file()}
        tool["source_files_sha256"] = hashes
        for consumer in tool["consumers"]:
            manifest = hub / consumer["project_root"] / consumer["dependency_file"]
            data = json.loads(manifest.read_text())
            row = next(r for r in data["tools"] if r["id"] == tool["id"])
            field = "verified_source_files_sha256" if row["status"] == "verified" else "observed_source_files_sha256"
            row[field] = hashes
            manifest.write_text(dump(data))
    registry_file.write_text(dump(registry))
    # Generate in isolation. Only the resulting tracked files enter the published tree.
    subprocess.run(["python3", hub / "scripts/sync_tools.py", "update"], check=True)
    backups = hub / ".sync-backups"
    if backups.exists():
        shutil.rmtree(backups)
    subprocess.run(["python3", hub / "scripts/sync_tools.py", "check"], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="新的空目录")
    destination = parser.parse_args().destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        parser.error("导出目标必须为空，已有文件请保留")
    for project in PROJECTS:
        copy_sources(project, destination)
    launcher = destination / "tools/templates/新建项目.command"
    if launcher.read_bytes() != (HUB.parent / launcher.name).read_bytes():
        raise ValueError("顶层启动脚本与工具箱中已提交的副本有差异")
    shutil.copy2(launcher, destination / launcher.name)
    rebuild_index(destination)
    (destination / "README.md").write_text(
        "# Project\n\n五个项目的公开源码，可在 GitHub 中直接浏览。\n\n"
        "- [paper](paper/) · 文献获取、阅读与 OLED 公式处理\n"
        "- [plot](plot/) · 绘图与光谱分析应用\n"
        "- [tools](tools/) · 工具登记、跨项目接口与双向引用检查\n"
        "- [oled_doi_downloader](oled_doi_downloader/) · 按 DOI 下载文献\n"
        "- [oled_literature_traverser](oled_literature_traverser/) · 从种子 DOI 遍历相关文献\n\n"
        "克隆整个仓库后，从根目录运行 `python3 tools/scripts/check_links.py` 检查工具关系。"
        "文献、运行数据库、浏览器登录状态、审批回执、第三方抓取工具实现与本地安装包由运行方单独配置。"
        "配置中的 `~/process/paper/archive-volume` 指向运行方选定的归档盘。\n")


if __name__ == "__main__":
    main()
