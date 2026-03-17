---
name: scienceclaw_workflow_omics_kickoff
description: Create the standard Phase 3 omics runDir shell with template artifacts, evidence, and citation placeholders. Use when starting a governed omics analysis bundle before deeper downstream computation.
---

# ScienceClaw：Omics Kickoff（Phase 3）

目的：生成 Phase 3（Omics）Domain Pack 的**标准 runDir 产物壳**，把深度分析的“交付结构”固定下来。

这个技能本身不做重计算（不依赖 scanpy/scvi）。它的价值是：

- 每次运行都落 `manifest.json + artifacts/ + logs/`
- 提供可复制的模板文件：`analysis_plan.md / qc_summary.md / annotation_table.tsv`
- 保证 `citations.bib` 与 `evidence.json` **非空**（符合你们的行业标准底座）

## 输入

- `--project`：项目名（默认 `default`）
- `--workspace`：OpenClaw workspace（默认 `$OPENCLAW_WORKSPACE` 或 `~/.openclaw/workspace`）
- `--dataset`：可选，数据集路径（h5ad/mtx/loom 等，本技能仅记录 hash，不解析）

## 输出（runDir）

在 `$WORKSPACE/projects/<project>/runs/<runId>/` 下生成：

- `manifest.json`
- `artifacts/analysis_plan.md`
- `artifacts/environment.md`
- `artifacts/perf_env.json`
- `artifacts/qc_summary.md`
- `artifacts/annotation_table.tsv`
- `artifacts/figures/`（目录占位）
- `artifacts/citations.bib`（非空）
- `artifacts/evidence.json`（非空）
- `logs/kickoff.log`

并在 stdout 打印 `runDir`（最后一行）。

## Smoke Test（< 10s）

```bash
python3 run.py --project smoke --workspace "$PWD/../../.."  # 在仓库内运行时
```

## 备注（与 Pantheon skills 的关系）

Pantheon `omics` skills 提供深度分析的方法论与步骤；本技能负责把“交付结构”固定为 ScienceClaw 的 artifact bundle。深度分析可以在 Pantheon/notebook 中完成，但最终应把关键输出写回本 runDir 的 artifacts。
