# ScienceClaw 技能包（MVP）

这个目录是一个“受控的科研技能包”，目标是安装到 OpenClaw workspace：

`~/.openclaw/workspace/skills/`

MVP 目标：

- 产品优先：优化首次成功时间（TTFR, Time-to-first-result），并确保产物可预测、可复盘。
- 科研级输出：每次运行必须落一个可审计的产物包（artifact bundle）：`artifacts/ + manifest.json + logs/`。
- 核心保持“薄”：技能尽量原子化（atomic skill）；用编排器（orchestrator）做路由与组合。

## 安装（云端服务器）

在服务器（root）上，假设 OpenClaw workspace 在 `/root/.openclaw/workspace`：

```bash
mkdir -p /root/.openclaw/workspace/skills
```

把本仓库 `scienceclaw/skills/` 下的子目录复制到服务器的 skills 目录即可。

## MVP 内置技能

- `scienceclaw_orchestrator`：对用户意图做路由，选择合适的原子技能（后续可扩展为 workflow pipeline）。
- `literature_pubmed_search`：PubMed 检索 -> 结构化 JSON + BibTeX 引用。
- `pdf_extract_basic`：PDF 抽取 -> 基础文本结构化输出。
- `scienceclaw_fs_ingest`：把用户提供的本地文件导入到 `artifacts/inputs/` 并生成 hash 清单（Base）。
- `scienceclaw_http_fetch`：带 allowlist 的安全下载；离线模式输出结构化下载计划（Base）。
- `scienceclaw_format_convert`：办公/数据常见格式转换（PDF->text, CSV<->JSON 等）（Base）。
- `scienceclaw_data_profile`：CSV/JSON 数据画像（profile.json + profile.md）（Base）。
- `scienceclaw_json_validate`：对常见 JSON 产物做快速校验（manifest/evidence/profile/...）（Base）。
- `scienceclaw_repro_export`：导出可复现性 bundle（commands.sh + checksums.sha256 + environment.txt）（Base）。
- `scienceclaw_report_compose_md`：生成可交付报告（汇总 inputs/commands/artifacts，并嵌入关键产物片段）（Base）。
- `scienceclaw_workflow_omics_kickoff`：Phase 3（Omics）交付壳：生成 runDir 模板产物包（P3）。
- `scienceclaw_workflow_vcf_annotate_brief`：Phase 3 主线 Domain Pack：本地 VCF -> 注释结构化 -> 简报 + 证据链/引用 + L5 gate（P3）。
- `scienceclaw_workflow_lit_brief`：证据链文献简报（v1 主闭环工作流）。
- `scienceclaw_installer`：一键安装依赖 + smoke test。
- `scienceclaw_selfcheck`：自检（验证产物包最低要求）。
- `scienceclaw_meta`：技能包版本信息与 allowlist。
- `scienceclaw_lit_resolve_id`：PMID -> PMCID 映射（为 PDF 获取做准备）。
- `scienceclaw_lit_pdf_fetch_pmc`：从 PMC 获取 PDF（给定 PMCID/PMID）。
- `scienceclaw_workflow_pdf_brief`：本地 PDF -> 证据链 -> 简报（Phase 2）。
- `scienceclaw_pdf_extract_structured`：本地 PDF 结构化抽取（Phase 2 原子技能）。
- `scienceclaw_table_extract_from_pdf`：从 PDF 抽取表格（Phase 2 原子技能）。
- `scienceclaw_workflow_table_to_csv`：表格抽取工作流（Phase 2）。
- `scienceclaw_citation_normalize`：引用与证据链规范化（Phase 2）。
- `scienceclaw_bundle_lint`：对 runDir 做产物完整性与最小质量门槛校验（L5 gate）。
- `vendor_openclaw_scientific_skill`：第三方科研技能库（MIT，作为可选能力包导入）。

## 设计文档

- Skills 架构（v1 提案）：`docs/SCIENCECLAW_SKILLS_ARCHITECTURE.md`
- Skills Catalog（v1，员工/平台分层目录）：`docs/SCIENCECLAW_SKILLS_CATALOG_V1.md`
- Cloud/内测发布手册：`docs/SCIENCECLAW_CLOUD_INTERNAL_BETA_RUNBOOK.md`
- 产物包规范（v1）：`docs/SCIENCECLAW_V1_ARTIFACT_SPEC.md`
- 技能契约（v1）：`docs/SCIENCECLAW_SKILL_CONTRACT.md`
- L3 科研公共技能库（完成版）：`docs/SCIENCECLAW_L3_SKILL_LIBRARY.md`
- Phase 3 计划与架构（领域差异化）：`docs/SCIENCECLAW_PHASE3_PLAN_AND_ARCHITECTURE.md`
- Phase 3：Pantheon skills 迁移清单：`docs/SCIENCECLAW_P3_PANTHEON_SKILLS_ADOPTION.md`
- Phase 3：Omics Playbook（执行版）：`docs/SCIENCECLAW_P3_OMICS_PLAYBOOK.md`

## Pantheon 集成（深度执行引擎）

如果你们的产品主线是“用 Claw 更多、更浅”，而“深度调用（多智能体/skills 注入/Notebook/长链路分析）用 Pantheon”，那么推荐分工是：

- Claw（OpenClaw/ScienceClaw）：主入口与轻执行，负责产物包标准（runDir）。
- Pantheon：深度执行引擎，负责复杂分析的多智能体协作与知识技能注入。

本仓库当前提供的是一个最小可用的集成落地（更偏“开发/验证 harness”）：在 Pantheon 里把 ScienceClaw workflow 暴露成可调用工具（无需迁移 ScienceClaw 代码）：

- Pantheon package tools：`.pantheon/packages/scienceclaw/`
  - 通过 `packages.scienceclaw.phase2_pdf_brief/phase2_table_to_csv/...` 调用 ScienceClaw workflow，并返回 `runDir + artifacts 路径`。
- Pantheon skill 指南：`.pantheon/skills/scienceclaw_workflows.md`
- 本地启动脚本：`start_pantheon_ui_local.sh`

下一步如果要完全对齐“Claw 主导交互”，我们需要补一个反向桥接：由 ScienceClaw/Claw orchestrator 触发 Pantheon team，并把 Pantheon 的输出收敛到 ScienceClaw 的 runDir artifacts（保持审计与交付一致）。

## Phase 2 验收（云端 VM，一条脚本）

部署完成后，在 VM 上运行：

```bash
bash /root/.openclaw/workspace/skills/scienceclaw_installer/run.sh
```

或用标准验收脚本（建议作为交付凭证保留 runDir）：

```bash
bash /root/.openclaw/workspace/skills/scienceclaw_meta/phase2_acceptance_vm.sh
```

Phase 3（Domain Pack）验收：

```bash
bash /root/.openclaw/workspace/skills/scienceclaw_meta/phase3_acceptance_vm.sh
```

一键全量（Phase2+Phase3）验收：

```bash
bash /root/.openclaw/workspace/skills/scienceclaw_meta/phase_all_acceptance_vm.sh
```
