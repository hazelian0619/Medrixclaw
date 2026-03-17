---
name: scienceclaw_table_extract_from_pdf
description: Extract table-like content from local PDFs into CSV or JSON artifacts with page-linked evidence. Use inside table workflows when converting PDF tables into structured outputs.
---

# ScienceClaw：PDF 表格抽取 -> CSV/JSON + 证据链（Atomic）

## 目的 / 适用场景（when-to-use）

把本地 PDF 里的“表格样式文本块”抽取为结构化表格，并产出可复盘的证据链与产物包。

适合：

- 论文 PDF 中的表格快速转成 `CSV/JSON`
- 需要每个表格能回指到 `file + page` 的审计/复盘场景

不适合：

- 扫描版图片表格（需要 OCR；v1 不覆盖）
- 复杂跨页大表格（可能需要人工后处理）

## 实现策略与取舍

优先路线：使用 PyMuPDF 的页面 blocks 抽取出“table-like 文本块”，用规则解析成行列；在允许时可选用 LLM 进行行列修复（`--no-llm` 时完全离线）。

取舍：

- 不引入 `camelot/tabula`，避免 Ubuntu 上 Java/Ghostscript 等依赖带来的 TTFR 波动与安装复杂度。
- 证据链最小闭环优先：每个表格至少能回指到 `file + page`，并包含原始 block 片段。

## 输入

- `--pdf`（必填）：本地 PDF 路径
- `--project`（可选）：默认 `default`
- `--no-llm`：不调用模型（离线模式）；仍会产出 `tables.json`（可能只包含规则解析/原始块）
- `--workspace`（可选）：默认 `$OPENCLAW_WORKSPACE` 或 `~/.openclaw/workspace`

可选调参：

- `--max-pages`：最多处理前 N 页（默认 50；0 表示全量）
- `--min-rows`：最少多少行才认为是表格（默认 3）

## 输出（产物包）

在 `$OPENCLAW_WORKSPACE/projects/<project>/runs/<runId>/` 下生成：

- `manifest.json`
- `artifacts/tables.json`：结构化 tables（至少包含 `table_id`、`page`、`cells`/`markdown`）
- `artifacts/tables.csv`
  - 若只抽到 1 张表：该文件为真实表格 CSV
  - 若抽到多张表：该文件为索引（table_id,page,csv_path,...），真实 CSV 在 `artifacts/tables/*.csv`
- `artifacts/evidence.json`：每张表都能回指到 `file + page`
- `logs/`

## 运行命令

```bash
python3 run.py --pdf "/path/to/paper.pdf" --project demo --no-llm
```

## 冒烟测试（< 60s）

```bash
python3 - <<'PY'
import pathlib, os, subprocess, sys, tempfile
import fitz

tmp = pathlib.Path(tempfile.mkdtemp())
pdf = tmp / "demo_table.pdf"
doc = fitz.open()
p = doc.new_page()
p.insert_text((72, 72), "Gene    Count    P\nTP53    12       0.01\nBRCA1   5        0.20\n", fontsize=12)
doc.save(str(pdf))
doc.close()

skill = pathlib.Path(os.environ.get("OPENCLAW_WORKSPACE", str(pathlib.Path.home()/".openclaw"/"workspace"))) / "skills" / "scienceclaw_table_extract_from_pdf" / "run.py"
subprocess.check_call([sys.executable, str(skill), "--pdf", str(pdf), "--project", "selfcheck", "--no-llm"])
PY
```

## 依赖

- Python 3
- `pymupdf`（import `fitz`）
- 可选：`requests`（仅在非 `--no-llm` 且使用 MaaS OpenAI 兼容接口时需要）

## 失败模式（常见报错 + 1 行修复命令）

- `ModuleNotFoundError: fitz`
  修复：`python3 -m pip install --user pymupdf`

- `missing MAAS_API_KEY`
  修复：`export MAAS_API_KEY=...` 或改用 `--no-llm`

## 安全约束

- 不启动对外服务（不开端口）
- 不会尝试从 PMC 自动下载 PDF（只处理用户提供的本地 PDF）
