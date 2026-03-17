---
name: scienceclaw_workflow_lit_brief
description: Search PubMed and produce an evidence-backed literature brief with citations and artifacts. Use when the user asks for a query-driven literature summary or paper brief.
---

# ScienceClaw：证据链文献简报（Workflow v1）

这是 ScienceClaw v1 的主闭环工作流（primary workflow）：给定一个研究问题/关键词，产出一份带证据链与引用的简报产物包。

## 输入

- `--query`（必填）：检索 query
- `--limit`（可选）：默认 10
- `--project`（可选）：默认 `default`
- `--pdf`（可选，可重复）：本地 PDF 路径（推荐方式，用于生成更强证据链）
- `--no-pdf`：跳过“远程 PDF 获取”（仍会处理 `--pdf` 指定的本地文件）
- `--no-llm`：不调用模型（只生成结构化结果与模板简报，适合自检/离线）

## 输出（产物包）

在 `$OPENCLAW_WORKSPACE/projects/<project>/runs/<runId>/` 下生成：

- `manifest.json`
- `artifacts/brief.md`
- `artifacts/citations.bib`
- `artifacts/evidence.json`
- `logs/`

## 运行命令

```bash
python3 run.py --query "openclaw glm-5" --limit 5 --project demo
```

## 给 OpenClaw 的执行步骤（推荐）

当用户在对话里请求“给我做一份带引用的文献简报”时，按以下步骤执行并把结果回传：

1. 执行 workflow：
   `python3 run.py --query "<用户 query>" --limit 10 --project <project>`
2. 读取并返回：
   `cat <runDir>/artifacts/brief.md`
3. 若用户需要下载：
   提供 `<runDir>` 路径，并说明 `artifacts/` 里包含 `citations.bib` 与 `evidence.json`。

## 常见报错（1 行修复）

- `ModuleNotFoundError: requests`
  修复：`python3 -m pip install --user requests`

- `ModuleNotFoundError: fitz`
  修复：`python3 -m pip install --user pymupdf`

## 冒烟测试（< 60s）

说明：本 workflow 依赖 PubMed（外网）。如果仅想离线验证产物包链路，请用 `scienceclaw_selfcheck --offline` 或 `scienceclaw_workflow_pdf_brief --no-llm`。

```bash
python3 run.py --query "openclaw glm-5" --limit 2 --project selfcheck --no-llm --no-pdf
```
