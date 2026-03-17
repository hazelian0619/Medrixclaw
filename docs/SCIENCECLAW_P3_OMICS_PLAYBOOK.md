# ScienceClaw Phase 3（Omics）Playbook v1（执行版）

目标：把 Pantheon `omics` skills 的“深度科研方法论”迁移成 ScienceClaw Phase 3 的**可交付标准**（runDir 产物包），并给工程实现提供一个唯一的落地入口（不要散在很多文档里）。

本 playbook 解决的问题：

- 做单细胞/空间组学时，“怎么做才算行业标准”。
- 即便深度分析发生在 Pantheon/notebook 里，最终如何落到 ScienceClaw 的 artifacts（可复盘、可审计、可验收）。

非目标：

- v1 不追求一键跑完所有 omics 流程（依赖太重，TTFR 会崩）。
- v1 先把“产物结构 + 决策记录 + 证据链”立住，再逐步自动化执行。

## 1) P3 Domain Pack（Omics）最小交付包

每次 Phase 3 Omics 运行必须产出（runDir 下）：

- `manifest.json`
- `artifacts/analysis_plan.md`（本次分析计划与决策记录）
- `artifacts/environment.md`（环境信息与复现实务）
- `artifacts/perf_env.json`（性能相关 env 与资源信息）
- `artifacts/qc_summary.md`
- `artifacts/annotation_table.tsv`
- `artifacts/figures/`（至少有 1 张图；v1 允许占位，但建议真实输出）
- `artifacts/citations.bib`（非空）
- `artifacts/evidence.json`（非空）
- `logs/`

说明：

- `citations.bib` 与 `evidence.json` 是你们“行业标准底座”的延续，不可缺。
- “深度能力”可以在 Pantheon 的 notebook/多智能体里完成，但最终必须把关键结果写回这些 artifacts。

## 2) 迁移来源（Pantheon skills -> 我们的结构）

我们不直接把 Pantheon 原文代码块全拷贝进 scienceclaw（维护成本高）。迁移策略是：**迁移 checklist/决策点/模板**。

P0 必迁移（Phase 3 第一周就用）：

- `environment_management` -> `environment.md` + 可复现文件（requirements/environment.yml）
- `parallel_computing` -> `perf_env.json` + 资源记录
- `quality_control`（瘦身版）-> `qc_summary.md` + `figures/qc_*.png`
- `cell_type_annotation` -> `annotation_table.tsv` + `figures/annotation_*.png`

可选（主线需要时再引入）：

- `trajectory_inference` -> `trajectory_summary.md`（如果研究问题需要）
- `single_cell_spatial_mapping` -> `mapping_metrics.json`（如果空间映射是主线）
- `database_access/*` -> 作为在线增强，不阻塞离线 baseline

完整清单见：
- `docs/SCIENCECLAW_P3_PANTHEON_SKILLS_ADOPTION.md`

## 3) 写作与产物模板（工程必须按这个落）

### 3.1 `analysis_plan.md`（必须）

最小结构（建议直接复制）：

1. 输入与目标
2. 环境策略（conda/venv，是否 GPU）
3. 性能策略（n_jobs、NUMBA/OMP/BLAS）
4. QC 计划（阈值如何决定、哪些步骤必做）
5. 注释计划（marker vs reference，输出表结构）
6. 可选模块（trajectory / spatial mapping / database fetch）
7. 交付清单（本 runDir 产物一览）

### 3.2 `qc_summary.md`（必须）

必须包含：

- 数据基本信息：cells/genes、样本批次字段（如有）
- QC 指标：counts、genes、MT%
- 过滤阈值：阈值数值 + 选择理由（引用图或统计）
- 过滤前后统计：before/after

### 3.3 `annotation_table.tsv`（必须）

TSV 表头固定为：

`cluster_id\tcell_type\tevidence_ref\tnotes`

其中 `evidence_ref` 是对 `evidence.json` 的引用（例如 `E1`/`E2`），避免注释不可复盘。

### 3.4 `citations.bib`（必须非空）

v1 允许先放占位条目，但必须非空。建议至少包含：

- Scanpy/Seurat/CellTypist/SCVI 等你实际用到的工具
- 关键数据库或 best practice 参考（如 gget / CELLxGENE Census）

后续统一用 `scienceclaw_citation_normalize` 收敛治理。

### 3.5 `evidence.json`（必须非空）

v1 最小要求：至少 1 条 evidence 记录“关键决策依据”，例如：

- QC 阈值依据（引用某张 QC 图或统计）
- root cell/cluster 的选择依据（轨迹）
- mapping 参数选择依据（空间映射）

Locator v1 可以先用 `file:` + `offset:`，后续再升级结构化 locator。

## 4) 工程落地顺序（两周可执行）

Week 1（先把交付壳跑起来）：

1. 新增 `scienceclaw_workflow_omics_kickoff`：生成 runDir + 上述模板 artifacts（可离线）。
2. 允许 Pantheon 深度分析在外部完成，但要求把输出文件写回 runDir。

Week 2（开始自动化一部分执行）：

1. 增加 `scienceclaw_omics_qc_scanpy`（可选）：在有依赖的环境里跑最小 QC 并输出图/表。
2. 增加 `scienceclaw_omics_annotation`（可选）：输出 marker 表与 annotation_table.tsv。

验收标准（pass/fail）：

- 任意一次运行都能生成完整 runDir 结构（即使深度分析未跑完也要落包）。
- `citations.bib` 与 `evidence.json` 永不为空。
- `analysis_plan.md` 必须能复盘本次决策与参数。

