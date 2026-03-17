---
name: scienceclaw_fs_ingest
description: Ingest local files into the current ScienceClaw run bundle and record hashes, sizes, and mappings for auditability. Use when workflow inputs need to be copied into artifacts/inputs in a controlled way.
---

# ScienceClaw：本地文件导入（FS Ingest）（Base）

## 目的 / 适用场景（when-to-use）

把用户提供的本地文件稳定导入到本次 run 的 `artifacts/inputs/` 下，并生成可复盘的清单（hash/大小/映射关系）。

适合：

- 把 `pdf/csv/json/xlsx/...` 等输入文件纳入 artifact bundle，供后续 workflow/原子技能复用
- 离线环境（不依赖网络，不依赖 LLM）

## 输入

- `--path`（必填，可重复）：本地文件路径
- `--project`（可选）：默认 `default`
- `--workspace`（可选）：默认 `$OPENCLAW_WORKSPACE` 或 `~/.openclaw/workspace`
- `--run-dir`（可选）：写入一个已有 runDir（由 workflow 创建）
- `--no-llm`：兼容统一接口；本技能不使用 LLM

## 输出（产物包）

在 `$OPENCLAW_WORKSPACE/projects/<project>/runs/<runId>/` 下生成：

- `manifest.json`
- `artifacts/inputs/<files...>`：复制后的输入文件
- `artifacts/ingest.json`：导入清单（src/dst/sha256/bytes）
- `logs/ingest.log`

## 运行命令

```bash
python3 run.py --path /path/to/data.csv --path /path/to/paper.pdf --project demo --no-llm
```

## 依赖

- Python 3

## 失败模式（常见报错 + 1 行修复命令）

- `FileNotFoundError`
  修复：确认 `--path` 指向的文件存在且权限可读

## 安全约束

- 只读取本地文件；不访问网络；不启动端口
- 只写入本次 run 的 `artifacts/` 与 `logs/`

## Smoke Test（< 60s）

```bash
python3 - <<'PY'
import os, sys, json, tempfile
from pathlib import Path
tmp = Path(tempfile.mkdtemp())
p = tmp / "hello.txt"
p.write_text("hello\\n", encoding="utf-8")
skill = Path.cwd() / "scienceclaw" / "skills" / "scienceclaw_fs_ingest" / "run.py"
os.environ["OPENCLAW_WORKSPACE"] = str(tmp / "ws")
import subprocess
out = subprocess.check_output([sys.executable, str(skill), "--path", str(p), "--project", "selfcheck", "--no-llm"], text=True).strip().splitlines()[-1]
print(out)
PY
```
