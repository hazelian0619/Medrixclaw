---
name: scienceclaw_report_compose_md
description: Compose a delivery report from an existing run bundle and summarize key artifacts and rerun information. Use when a run needs a human-readable report for review or handoff.
---

# ScienceClaw：交付报告生成（Report Compose）（Base）

## 目的 / 适用场景（when-to-use）

给定一个 runDir（或在本技能创建的 run 包），生成一份“可交付的汇报报告”：

- 汇总 manifest（inputs/commands/artifacts）
- 汇总关键产物（brief/profile/preview/citations/evidence）
- 给出复盘提示（如何重跑、如何验证 checksums）

本技能不依赖 LLM，离线可跑。

## 输入

- `--run-dir <path>`：将报告写入该 run 的 `artifacts/`（推荐，workflow 内部调用）
- `--title <text>`：报告标题（可选）
- `--max-embed-chars <n>`：嵌入 artifact 文本的最大字符数（默认 4000）
- `--project/--workspace/--no-llm`：标准参数

## 输出（产物包）

在目标 runDir 下生成：

- `artifacts/report.md`
- `artifacts/report.json`
- `logs/report.log`

并更新 `manifest.json` 记录这些 artifacts。

## 运行命令

```bash
python3 run.py --run-dir /path/to/runDir --title "Delivery Report" --no-llm
```

## 依赖

- Python 3（标准库）

## 安全约束

- 不访问网络；不启动对外服务
- 只写入目标 runDir 的 `artifacts/` 与 `logs/`

## Smoke Test（< 60s）

```bash
python3 run.py --project selfcheck --no-llm
```
