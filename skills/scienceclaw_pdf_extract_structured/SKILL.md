---
name: scienceclaw_pdf_extract_structured
description: Extract structured text content from one or more local PDFs into reproducible JSON artifacts for downstream evidence and briefing workflows. Use when local PDF parsing is needed as a deterministic upstream step.
---

# ScienceClaw：PDF 结构化抽取（Structured Extract）

目的：对 1-N 个本地 PDF 做稳定抽取，输出可复盘的 `extracted.json`（按文件、页、文本组织，并做最小章节粗分）。

适用场景：

- 用户已提供本地 PDF（最稳定路径，不依赖联网抓取）
- 后续需要从 PDF 生成 evidence/brief 的上游步骤

## 输入

- `--pdf`（必填，可重复）：本地 PDF 路径
- `--project`（可选）：项目名，默认 `default`
- `--workspace`（可选）：OpenClaw workspace 目录，默认 `$OPENCLAW_WORKSPACE` 或 `~/.openclaw/workspace`

## 输出（产物包）

在 `$OPENCLAW_WORKSPACE/projects/<project>/runs/<runId>/` 下生成：

- `manifest.json`
- `artifacts/extracted.json`
- `logs/extract.log`

其中 `artifacts/extracted.json` 结构（简化）：

```json
{
  "schemaVersion": 1,
  "files": [
    {
      "path": "/abs/path/paper.pdf",
      "sha256": "...",
      "pages": [{"page": 1, "text": "...", "section": "INTRODUCTION"}],
      "sections": [{"title": "INTRODUCTION", "startPage": 1, "endPage": 2, "heuristic": "heading"}]
    }
  ]
}
```

## 依赖

- Python 3
- `pymupdf`（PyMuPDF / `fitz`）

## 常见失败模式（1 行修复）

- `ModuleNotFoundError: fitz`
  修复：`python3 -m pip install --user pymupdf`

## 安全约束

- 只读本地文件，不启动服务端口，不写入 `artifacts/` 与 `logs/` 之外的路径。

## Smoke Test（< 60s）

```bash
python3 -c "import fitz, pathlib; p=pathlib.Path('/tmp/scienceclaw_smoke.pdf'); d=fitz.open(); pg=d.new_page(); pg.insert_text((72,72),'ABSTRACT\\n\\nThis is a small PDF for ScienceClaw smoke test.\\n\\nMETHODS\\nWe did X.\\n\\nRESULTS\\nWe observed Y.\\n'); d.save(p); print(p)" && python3 run.py --project smoke --pdf /tmp/scienceclaw_smoke.pdf
```
