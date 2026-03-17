---
name: scienceclaw_workflow_table_to_csv
description: Extract tables from a local PDF and export them as CSV/JSON with evidence artifacts. Use when the task is to turn PDF tables into structured tabular outputs.
---

# ScienceClaw：表格抽取工作流（Workflow）

## 目的 / 适用场景（when-to-use）

把“PDF 表格 -> CSV/JSON + 证据链”打包成一条可演示的工作流技能，输出稳定的产物包（artifact bundle）。

该 workflow 是薄封装：

- 创建 workflow 自己的 run 包（`manifest.json + artifacts/ + logs/`）
- 在同一个 runDir 内调用原子技能 `scienceclaw_table_extract_from_pdf` 写入产物

## 输入

- `--pdf`（必填）：本地 PDF 路径
- `--project`（可选）：默认 `default`
- `--no-llm`：离线模式
- `--workspace`（可选）：默认 `$OPENCLAW_WORKSPACE` 或 `~/.openclaw/workspace`

## 输出（产物包）

在 `$OPENCLAW_WORKSPACE/projects/<project>/runs/<runId>/` 下生成：

- `manifest.json`
- `artifacts/tables.json`
- `artifacts/tables.csv`
- `artifacts/evidence.json`
- `logs/workflow.log`（记录原子技能 stdout/stderr）

## 运行命令

```bash
python3 run.py --pdf "/path/to/paper.pdf" --project demo --no-llm
```

## 冒烟测试（< 60s）

同原子技能的冒烟测试（生成一个小 PDF 并跑 `--no-llm`）。

## 依赖

- Python 3
- `pymupdf`
- 可选：`requests`（非 `--no-llm` 的 LLM 路径）

## 失败模式（常见报错 + 1 行修复命令）

- `atomic skill not found`
  修复：确认该目录存在：`$OPENCLAW_WORKSPACE/skills/scienceclaw_table_extract_from_pdf/`

## 安全约束

- 不启动对外服务（不开端口）
- 不会尝试自动下载 PDF（只处理本地输入）
