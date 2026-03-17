---
name: scienceclaw_meta
description: Describe the ScienceClaw pack version, controlled skill allowlist, and minimum bundle conventions. Use when checking pack contents, governed skills, or deployment metadata.
---

# ScienceClaw：技能包元信息（Meta）

目的：提供 ScienceClaw skills 包的版本信息、包含的技能清单（allowlist），以及最小交付约定。

## 当前版本

- `packVersion`: 0.4.1
- `primaryEntry`: `scienceclaw_orchestrator`

## 受控技能清单（allowlist）

ScienceClaw v1 受控技能（本仓库交付并负责兼容性）：

- `scienceclaw_installer`
- `scienceclaw_selfcheck`
- `scienceclaw_fs_ingest`
- `scienceclaw_http_fetch`
- `scienceclaw_format_convert`
- `scienceclaw_data_profile`
- `scienceclaw_json_validate`
- `scienceclaw_repro_export`
- `scienceclaw_report_compose_md`
- `scienceclaw_pack_validate`
- `scienceclaw_workflow_omics_kickoff`
- `scienceclaw_workflow_vcf_annotate_brief`
- `scienceclaw_bio_vcf_validate`
- `scienceclaw_bio_vcf_annotate`
- `scienceclaw_workflow_lit_brief`
- `scienceclaw_workflow_pdf_brief`
- `scienceclaw_workflow_table_to_csv`
- `scienceclaw_orchestrator`
- `scienceclaw_lit_resolve_id`
- `scienceclaw_lit_pdf_fetch_pmc`
- `literature_pubmed_search`
- `pdf_extract_basic`
- `scienceclaw_pdf_extract_structured`
- `scienceclaw_table_extract_from_pdf`
- `scienceclaw_citation_normalize`
- `scienceclaw_bundle_lint`
- `vendor_openclaw_scientific_skill`

说明：

- 其他出现在 workspace 的 skills 可能来自 OpenClaw 上游或云镜像预装，不纳入 ScienceClaw 的兼容性承诺范围。
- 升级时优先保持 allowlist 内技能的行为稳定（产物包规范、输出字段、路径约定）。
- `employeeVisible` / `internalOnly` 用于平台目录分层与飞书/OpenClaw 上架策略；不改变 allowlist 的工程治理语义。

## 交付约定（v1）

- 每次运行都必须产生：`manifest.json + artifacts/ + logs/`
- v1 主产物：证据链文献简报（`brief.md + citations.bib + evidence.json`）

## 冒烟测试（< 60s）

对 allowlist 与 skills 目录做一致性校验（L5 gate）：

```bash
python3 ../scienceclaw_pack_validate/run.py --strict --no-llm
```
