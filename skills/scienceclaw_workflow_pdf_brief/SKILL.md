---
name: scienceclaw_workflow_pdf_brief
description: Turn one or more local PDFs into extracted text, evidence snippets, citations, and a brief. Use when the user provides local PDF files and wants a reproducible evidence package or summary.
---

# ScienceClaw：PDF -> 证据链 -> 简报（Workflow）

目的：用户给 1-N 个本地 PDF 路径，生成可复盘产物包：

- `artifacts/extracted.json`（结构化抽取：按文件/页/文本 + 章节粗分）
- `artifacts/evidence.json`（证据片段带 `file + page locator`）
- `artifacts/brief.md`（可选用 LLM；`--no-llm` 时模板化生成）
- `artifacts/citations.bib`（best-effort，本地 PDF 占位条目）

## 输入

- `--pdf`（必填，可重复）：本地 PDF 路径
- `--project`（可选）：默认 `default`
- `--no-llm`：不调用模型（离线/自检模式，仍会生成 `brief.md`）
- `--workspace`（可选）：默认 `$OPENCLAW_WORKSPACE` 或 `~/.openclaw/workspace`

## 输出（产物包）

在 `$OPENCLAW_WORKSPACE/projects/<project>/runs/<runId>/` 下生成：

- `manifest.json`
- `artifacts/extracted.json`
- `artifacts/evidence.json`
- `artifacts/brief.md`
- `artifacts/citations.bib`
- `logs/`

## 依赖

- Python 3
- `pymupdf`（PyMuPDF / `fitz`）
- 可选：若开启 LLM，总体遵循 OpenAI-compatible `chat/completions`，读取 `MAAS_API_KEY/MAAS_BASE_URL/MAAS_MODEL`

## 常见失败模式（1 行修复）

- `ModuleNotFoundError: fitz`
  修复：`python3 -m pip install --user pymupdf`

## 安全约束

- 不联网抓取 PDF；只处理用户提供的本地路径。
- 不打印密钥；LLM 仅从环境变量读取。

## Smoke Test（< 60s）

```bash
python3 -c "import fitz, pathlib; p=pathlib.Path('/tmp/scienceclaw_smoke.pdf'); d=fitz.open(); pg=d.new_page(); pg.insert_text((72,72),'INTRODUCTION\\n\\nWe studied X.\\n\\nMETHODS\\nWe did Y.\\n\\nRESULTS\\nWe observed Z.\\n'); d.save(p); print(p)" && python3 run.py --project smoke --pdf /tmp/scienceclaw_smoke.pdf --no-llm
```
