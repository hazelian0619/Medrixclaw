---
name: scienceclaw_bio_vcf_validate
description: Validate the structure and basic statistics of a local VCF or VCF.GZ file and write the results into the run bundle. Use before downstream variant workflows to catch malformed inputs and record evidence.
---

# ScienceClaw：VCF 质量校验（VCF Validate）（L4 Atomic）

## 目的 / 适用场景（when-to-use）

对用户提供的 `*.vcf`（或 `*.vcf.gz`）做快速结构校验与统计画像，尽早暴露数据问题，避免后续 workflow “静默失败”。

本技能不依赖 LLM；离线可跑。

## 输入

- `--vcf <path>`（必填）：VCF 文件路径（支持 `.vcf` / `.vcf.gz`）
- `--run-dir <path>`（可选）：写回已有 runDir（workflow 模式）
- `--project/--workspace/--no-llm`：标准参数

## 输出（产物包）

- `artifacts/vcf.stats.json`：统计与校验结果（variants、samples、contigs、warning/error 列表）
- `artifacts/evidence.json`：追加最小证据条目（指向输入 VCF 与少量样例行）
- `logs/vcf_validate.log`

## 运行命令

```bash
python3 run.py --vcf /abs/path/sample.vcf --project demo --no-llm
```

## Smoke Test（< 60s）

```bash
python3 - <<'PY'
from pathlib import Path
import os, sys, subprocess, tempfile

tmp = Path(tempfile.mkdtemp())
vcf = tmp / "t.vcf"
vcf.write_text(
  "##fileformat=VCFv4.2\n"
  "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
  "1\t100\t.\tA\tG\t.\tPASS\t.\n",
  encoding="utf-8",
)
ws = tmp / "ws"
os.environ["OPENCLAW_WORKSPACE"] = str(ws)
skill = Path.cwd() / "scienceclaw" / "skills" / "scienceclaw_bio_vcf_validate" / "run.py"
out = subprocess.check_output([sys.executable, str(skill), "--vcf", str(vcf), "--project", "selfcheck", "--no-llm"], text=True).strip().splitlines()[-1]
print(out)
PY
```
