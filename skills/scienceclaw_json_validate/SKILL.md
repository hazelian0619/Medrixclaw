---
name: scienceclaw_json_validate
description: Validate a ScienceClaw JSON artifact such as manifest or evidence and emit a structured validation report. Use when checking whether generated JSON files meet the expected schema and quality gate.
---

# ScienceClaw：JSON 校验（JSON Validate）（Base）

## 目的 / 适用场景（when-to-use）

对 ScienceClaw 常见结构化产物做快速校验，产出可复盘的验证报告，作为治理层的最小质量门槛。

支持类型（v0）：

- `manifest`：`manifest.json`
- `evidence`：`evidence.json`（EvidenceItem[]）
- `profile`：`profile.json`
- `conversion`：`conversion.json`
- `fetch_plan`：`fetch.plan.json`
- `fetch_results`：`fetch.results.json`
- `citations_normalized`：`citations.normalized.json`

本技能不依赖 LLM；支持离线运行。

## 输入

- `--json <path>`（必填）：JSON 文件路径
- `--type <name>`（必填）：上述类型之一
- `--strict`：严格模式（若校验失败则退出非 0；默认始终落包但返回 0）
- `--project/--workspace/--no-llm`：标准参数

## 输出（产物包）

- `manifest.json`
- `artifacts/validation.json`：`{ ok, errors[], warnings[] }`
- `logs/validate.log`

## 运行命令

```bash
python3 run.py --json /path/to/evidence.json --type evidence --project demo --strict --no-llm
```

## 依赖

- Python 3（标准库）

## 安全约束

- 不访问网络；不启动对外服务
- 只写入本次 run 的 `artifacts/` 与 `logs/`

## Smoke Test（< 60s）

```bash
python3 - <<'PY'
import json, os, sys, tempfile, subprocess
from pathlib import Path
tmp = Path(tempfile.mkdtemp())
f = tmp / "evidence.json"
f.write_text(json.dumps([{\"source\":\"PMID:1\",\"locator\":\"abstract\",\"quote\":\"x\",\"usedIn\":[\"s\"]}], indent=2) + \"\\n\")
os.environ[\"OPENCLAW_WORKSPACE\"] = str(tmp / \"ws\")
skill = Path.cwd() / \"scienceclaw\" / \"skills\" / \"scienceclaw_json_validate\" / \"run.py\"
out = subprocess.check_output([sys.executable, str(skill), \"--json\", str(f), \"--type\", \"evidence\", \"--project\", \"selfcheck\", \"--strict\", \"--no-llm\"], text=True).strip().splitlines()[-1]
print(out)
PY
```
