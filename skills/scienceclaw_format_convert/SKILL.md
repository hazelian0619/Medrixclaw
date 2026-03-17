---
name: scienceclaw_format_convert
description: Convert common document and data formats such as PDF, CSV, and JSON into deterministic downstream-ready artifacts. Use when a workflow needs stable file format conversion without relying on an LLM.
---

# ScienceClaw：格式转换（Format Convert）（Base）

## 目的 / 适用场景（when-to-use）

把常见办公与数据文件做确定性转换，输出稳定的结构化产物，便于后续分析、汇报与审计。

当前 v0 支持：

- `pdf_to_text`：PDF -> `extracted.text.json` + `extracted.txt`
- `csv_to_json`：CSV -> JSON（array of objects）+ `preview.md`
- `json_to_csv`：JSON（array of objects）-> CSV
- `json_pretty`：JSON pretty print

全部支持 `--no-llm`（不使用 LLM），离线可运行。

## 输入

- `--input`（必填）：本地文件路径
- `--mode`（必填）：`pdf_to_text|csv_to_json|json_to_csv|json_pretty`
- `--project`（可选）：默认 `default`
- `--workspace`（可选）：默认 `$OPENCLAW_WORKSPACE` 或 `~/.openclaw/workspace`
- `--run-dir`（可选）：写入一个已有 runDir（由 workflow 创建）
- `--no-llm`：兼容统一接口；本技能不使用 LLM

## 输出（产物包）

- `manifest.json`
- `artifacts/conversion.json`：转换元信息（in/out、计数、hash）
- `artifacts/*`：转换产物（因 mode 不同而异）
- `logs/convert.log`

## 运行命令

```bash
python3 run.py --input /path/to/data.csv --mode csv_to_json --project demo --no-llm
```

## 依赖

- Python 3
- `pymupdf`（仅 `pdf_to_text` 需要；import `fitz`）

## 失败模式（常见报错 + 1 行修复命令）

- `ModuleNotFoundError: fitz`
  修复：`python3 -m pip install --user pymupdf`

## 安全约束

- 不访问网络，不启动服务端口
- 只写入本次 run 的 `artifacts/` 与 `logs/`

## Smoke Test（< 60s）

```bash
python3 - <<'PY'
import os, sys, tempfile, subprocess, json
from pathlib import Path
tmp = Path(tempfile.mkdtemp())
csvp = tmp / "a.csv"
csvp.write_text("x,y\\n1,2\\n3,4\\n", encoding="utf-8")
os.environ["OPENCLAW_WORKSPACE"] = str(tmp / "ws")
skill = Path.cwd() / "scienceclaw" / "skills" / "scienceclaw_format_convert" / "run.py"
out = subprocess.check_output([sys.executable, str(skill), "--input", str(csvp), "--mode", "csv_to_json", "--project", "selfcheck", "--no-llm"], text=True).strip().splitlines()[-1]
print(out)
PY
```
