---
name: scienceclaw_data_profile
description: Profile CSV or JSON tabular data and produce a structured summary with missingness, inferred types, and ranges. Use when a workflow needs a quick deterministic data overview before reporting or analysis.
---

# ScienceClaw：数据概览与画像（Data Profile）（Base）

## 目的 / 适用场景（when-to-use）

对 CSV/JSON（array-of-objects）做快速画像，输出：

- 结构化 `profile.json`（行数、列、缺失率、类型推断、数值范围）
- 人类可读的 `profile.md`（用于办公汇报/交付）

离线可跑，不依赖 LLM（`--no-llm` 为接口对齐）。

## 输入

- `--input`（必填）：CSV 或 JSON 文件
- `--format`（可选）：`auto|csv|json`，默认 `auto`
- `--max-rows`（可选）：最多扫描多少行，默认 5000（大文件可控 TTFR）
- `--project`（可选）：默认 `default`
- `--workspace`（可选）：默认 `$OPENCLAW_WORKSPACE` 或 `~/.openclaw/workspace`
- `--run-dir`（可选）：写入一个已有 runDir（由 workflow 创建）
- `--no-llm`：兼容统一接口；本技能不使用 LLM

## 输出（产物包）

- `manifest.json`
- `artifacts/profile.json`
- `artifacts/profile.md`
- `logs/profile.log`

## 运行命令

```bash
python3 run.py --input /path/to/data.csv --project demo --no-llm
```

## 依赖

- Python 3

## 失败模式（常见报错 + 1 行修复命令）

- JSON 不是 array-of-objects
  修复：先用 `scienceclaw_format_convert --mode json_pretty` 或把 JSON 转为 array-of-objects

## 安全约束

- 不访问网络，不启动服务端口
- 只写入本次 run 的 `artifacts/` 与 `logs/`

## Smoke Test（< 60s）

```bash
python3 - <<'PY'
import os, sys, tempfile, subprocess
from pathlib import Path
tmp = Path(tempfile.mkdtemp())
p = tmp / "a.csv"
p.write_text("a,b\\n1,2\\n,3\\n4,\\n", encoding="utf-8")
os.environ["OPENCLAW_WORKSPACE"] = str(tmp / "ws")
skill = Path.cwd() / "scienceclaw" / "skills" / "scienceclaw_data_profile" / "run.py"
out = subprocess.check_output([sys.executable, str(skill), "--input", str(p), "--project", "selfcheck", "--no-llm"], text=True).strip().splitlines()[-1]
print(out)
PY
```
