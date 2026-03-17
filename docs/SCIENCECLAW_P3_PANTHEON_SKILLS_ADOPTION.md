# ScienceClaw Phase 3：Pantheon Skills 迁移与微调清单（Draft）

目标：回到主线，快速判断 Pantheon 现成 skills 哪些“值得迁移/微调”来支撑 ScienceClaw 的 Phase 3（科研深度能力），并明确迁移方式与改造边界。

这里的“迁移”不等价于“全文拷贝进 scienceclaw/”。更推荐的工程做法是：

- **先复用结构与方法论**（Checklist/步骤/关键决策点），把“交付标准（artifact bundle）”补进去；
- 对需要对外发布/开源的内容，再做 **重写（rewrite）** 或在确认 license/provenance 后再 vendoring。

## 0) 前置共识（不争论）

- Phase 2 已经建立行业标准底座：`runDir = manifest.json + artifacts/ + logs/`，并且有 `evidence.json + citations.bib` 的规范。
- Phase 3 的“深度科研能力”可以依赖 Pantheon 的 skills（尤其 omics skillbook）来提供 best practices 与分析流程，但最终交付仍要回落到 ScienceClaw 的 artifact bundle（否则无法验收/复盘/产品化）。

## 1) Pantheon omics skills 总体盘点（按可迁移价值分级）

### P0（Phase 3 必须采用，直接提升可交付性）

1. 环境与可复现（必须）
- Pantheon skill: `environment_management`
- 文件：`.pantheon/skills/omics/environment_management.md`
- 价值：把“环境创建/导出/复现”标准化，是深度科研能力的地基。
- 微调建议（迁移到 ScienceClaw 的规则）：
  - 强制在 ScienceClaw runDir 里落：`artifacts/environment.yml`（conda）或 `artifacts/requirements.txt`（venv）。
  - 在 `manifest.json` 的 `environment` 字段记录：python 路径、conda env 名称、关键包版本。

2. 性能与资源（必须）
- Pantheon skill: `parallel_computing`
- 文件：`.pantheon/skills/omics/parallel_computing.md`
- 价值：大型单细胞数据分析的“默认成功条件”之一就是性能策略。
- 微调建议：
  - 把关键环境变量（NUMBA/OMP/BLAS）写进 ScienceClaw 的 `artifacts/perf_env.json`（用于复盘）。
  - 在 run 日志里记录：CPU 核数、n_jobs、峰值内存（可选）。

3. QC（强建议 P0，但要做“瘦身版”）
- Pantheon skill: `quality_control`
- 文件：`.pantheon/skills/omics/quality_control.md`
- 价值：QC 的强约束 checklist 很像我们 Phase 2 的“证据链硬标准”风格。
- 风险：原文依赖链很重（SoupX/rpy2/R 等），直接迁移会拖垮 TTFR。
- 微调建议（我们迁移“决策结构”，不迁移全部实现）：
  - 定义 ScienceClaw 的 **QC v1 最小闭环**：
    - 必做：QC metrics + 可视化 + 过滤前后计数对比
    - 可选：doublet
    - 延后：ambient RNA（作为增强，不作为 v1 阻塞项）
  - 迁移后输出必须包含：
    - `artifacts/qc_summary.md`（包含阈值、决策理由、过滤前后统计）
    - `artifacts/figures/qc_*.png`
    - `artifacts/evidence.json`：至少记录“阈值决策依据”（引用图/表/统计值作为 quote）

4. 注释（P0）
- Pantheon skill: `cell_type_annotation`
- 文件：`.pantheon/skills/omics/cell_type_annotation.md`
- 价值：把“marker -> 证据 -> label”流程写得很标准。
- 微调建议：
  - 强制输出 `artifacts/annotation_table.tsv`（cluster->cell_type->evidence_ref）。
  - 证据链要求：markers 的截图/表格必须能回指（evidence locator 可以先用 `file:` + `offset:` 或 `page:`）。

### P1（Phase 3 可选采用，取决于你们的主线选型）

5. 轨迹推断（如果 Phase 3 主线是单细胞/发育/状态转变相关）
- Pantheon skill: `trajectory_inference`
- 文件：`.pantheon/skills/omics/trajectory_inference.md`
- 微调建议：
  - 统一落 `artifacts/trajectory_summary.md`（root 选择依据、方法、参数、结果图）。
  - 把关键“root cell/cluster 的选择理由”写入 evidence（避免不可复盘）。

6. 单细胞到空间映射（如果 Phase 3 主线包含空间转录组）
- Pantheon skill: `single_cell_spatial_mapping`
- 文件：`.pantheon/skills/omics/single_cell_spatial_mapping.md`
- 微调建议：
  - 输出 `artifacts/mapping_metrics.json`（confidence 分布、参数、数据 shape）。
  - 输出 `artifacts/figures/mapping_*.png`

7. 数据库访问（P1，但强烈推荐尽早纳入）
- Pantheon skills: `database_access/*`（gget/cellxgene_census/iSeq）
- 文件：
  - `.pantheon/skills/omics/database_access/SKILL.md`
  - `.pantheon/skills/omics/database_access/gget.md`
  - `.pantheon/skills/omics/database_access/cellxgene_census.md`
- 价值：让 Phase 3 “深度科研能力”可持续扩展，而不是只能处理本地数据。
- 微调建议：
  - 把数据库查询当作“可选增强”，默认不阻塞离线 baseline。
  - 只要走过外部查询，必须在 `artifacts/citations.bib` 里补齐工具/数据库引用（可以先 @misc 占位，后续由 `scienceclaw_citation_normalize` 统一治理）。

### P2（暂缓：重依赖/重工程，容易拖垮 Phase 3 TTFR）

8. upstream_processing（nf-core/openst 等）
- 文件：`.pantheon/skills/omics/upstream_processing/*`
- 结论：暂缓。它属于“上游测序处理/HPC 工程”，不适合作为 Phase 3 的第一波交付。

## 2) 迁移策略（怎么“微调成我们的 Phase 3”）

Phase 3 我们要的不是“更多 markdown”，而是把这些方法论变成“可执行交付的标准件”。建议用 3 种迁移形态（按成本从低到高）：

1. **Playbook 迁移（最低成本）**
   - 把 Pantheon skill 的 checklist/决策点重写成 ScienceClaw 的中文 playbook（不拷贝原文大段代码）。
   - 输出是 `docs/` 文档 + 每个 playbook 对应的“产物约定”。

2. **Template 迁移（中成本）**
   - 给每个深度分析补一个固定模板：
     - `analysis_plan.md`（任务拆分）
     - `qc_summary.md` / `annotation_table.tsv` / `trajectory_summary.md`
     - `figures/` 输出约定
     - `citations.bib` 与 `evidence.json` 的最低门槛

3. **Workflow 迁移（高成本，真正工程落地）**
   - 增加 ScienceClaw workflow skill（`run.py`），调用 python/conda/notebook，最终落一个符合 v1 规范的 runDir。

Phase 3 先做 1+2，确认主线后再做 3。

## 3) Phase 3 的“最小可交付包”（建议）

如果 Phase 3 你们主线要走单细胞/空间组学，建议先定义一个最小交付包（不要求一次跑完所有分析，但要求产物结构稳定）：

- `artifacts/analysis_plan.md`：引用哪些 playbook（QC/注释/轨迹/空间）以及本次参数选择
- `artifacts/qc_summary.md` + `artifacts/figures/qc_*.png`
- `artifacts/annotation_table.tsv` + `artifacts/figures/annotation_*.png`
- （可选）`artifacts/trajectory_summary.md`
- `artifacts/citations.bib`（非空）
- `artifacts/evidence.json`（非空）

## 4) 下一步我建议立刻做的两件事（不涉及 bridge）

1. 把 Phase 3 文档主线从“泛领域能力”收敛成一个明确的 Omics Domain Pack（单细胞/空间）交付包定义，并引用本文件的 P0/P1 迁移清单。
2. 在 `scienceclaw/docs/` 新增一个 `SCIENCECLAW_P3_OMICS_PLAYBOOK.md`（中文），把 P0 的 3-4 个技能（环境/性能/QC/注释）重写成“可交付模板 + 产物约定”，作为工程落地的单一入口文档。

已落地：

- `docs/SCIENCECLAW_P3_OMICS_PLAYBOOK.md`
