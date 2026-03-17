---
name: scienceclaw_orchestrator
description: Route a ScienceClaw request to the appropriate workflow or atomic skill and preserve artifact-bundle outputs. Use when the requested task is ambiguous or when ScienceClaw should choose the main execution path.
---

# ScienceClaw 编排器（Orchestrator）

目的：把科研请求路由到正确的原子技能（atomic skill），并确保每次运行都在 OpenClaw workspace 下生成可复盘产物包（manifest + artifacts + logs）。

本 skill 同时提供一个可执行入口：`run.py`（CLI router + 最小后处理：引用规范化/交付报告/可复现导出/lint）。

## 适用场景

作为 ScienceClaw 的默认入口，尤其当用户请求不明确（文献 vs PDF vs 表格 vs 写作）时使用。

## 路由规则（MVP）

除非用户明确要求“跑完整流程”，否则只路由到 1 个主技能。

- 通用基座（办公/数据）：
  - 下载 URL / “把链接下载下来”：
    使用 `scienceclaw_http_fetch`（注意：默认需要 `--allow-domain`；离线可用 `--offline` 输出计划）
  - 转换格式 / “CSV 转 JSON” / “PDF 转文本”：
    使用 `scienceclaw_format_convert`
  - 数据概览 / “看看这个 CSV/JSON 有多少列、缺失率”：
    使用 `scienceclaw_data_profile`
  - 导入本地文件到产物包 / “把这些文件纳入本次 run”：
    使用 `scienceclaw_fs_ingest`
  - 校验 JSON 产物 / “检查 evidence.json 是否符合 schema”：
    使用 `scienceclaw_json_validate`
  - 导出可复现性 bundle / “生成 commands.sh + checksums.sha256”：
    使用 `scienceclaw_repro_export`
  - 生成交付报告 / “把本次 run 的产物汇总成一份 report.md”：
    使用 `scienceclaw_report_compose_md`

- 需要“综述/简报/证据链 + 引用”的文献工作流：
  使用 `scienceclaw_workflow_lit_brief`
- 文献检索 / “找论文” / PMID / DOI / “PubMed”：
  使用 `literature_pubmed_search`
- PDF 抽取 / “总结 PDF” / “抽表格” / “参考文献”：
  使用 `pdf_extract_basic`

## 输出契约（必须满足）

每次运行必须创建：

- `projects/<project>/runs/<runId>/manifest.json`
- `projects/<project>/runs/<runId>/artifacts/*`
- `projects/<project>/runs/<runId>/logs/*`

若缺依赖，必须停止并输出 1 行修复命令（可复制粘贴）。

## 示例

如果用户说：“在 PubMed 搜 GLM-5 + OpenClaw，给我 10 篇论文”，则执行 `literature_pubmed_search` 并传参：

- `project`：短 slug（例如 `demo`）
- `query`：用户 query
- `limit`：10

## CLI 用法（可直接跑）

```bash
# 文献简报
python3 run.py --query "openclaw glm-5" --limit 5 --project demo --no-llm --no-pdf

# PDF 简报
python3 run.py --pdf /abs/path/to/paper.pdf --project demo --no-llm

# 抽表格
python3 run.py --pdf /abs/path/to/paper.pdf --tables --project demo --no-llm

# Phase 3: VCF 注释与简报（Domain Pack）
python3 run.py --vcf /abs/path/to/sample.vcf --project demo --no-llm

# P3 模板（omics kickoff）
python3 run.py --omics-kickoff --project demo
```

## 冒烟测试（< 60s）

离线稳定的最小链路（不依赖外网/不调用模型）：

```bash
python3 run.py --omics-kickoff --project selfcheck --no-llm
```
