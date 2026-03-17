# ScienceClaw Phase 3 计划与 Skills 架构（Bioinformatics Differentiation）

定位复述（避免跑偏）：
ScienceClaw 是“基于 OpenClaw 的科研发行版”。OpenClaw 提供 control-plane（会话、模型路由、工具调度、渠道），ScienceClaw 的差异化沉到 Skills/Workflow 层，交付可复盘、可审计、可重复运行的产物包（artifact bundle）。

Phase 2 已把科研公共层（文献/PDF/表格/证据链/引用）打到可交付基线。Phase 3 的目标是做一个可演示、可复用、能形成付费意愿的 L4 领域包（Domain Pack），并且不破坏 Phase 2 的产物/治理约束。

本文件只定义 Phase 3 的主线与架构，不在此阶段扩展为“大而全的生信平台”。

## 0) Pantheon 与 Claw 的分工（按你说的“恰恰相反”版本）

一句话：
**Claw（OpenClaw/ScienceClaw）负责“更浅、更高频的入口与轻执行”，Pantheon 负责“更深、更重的执行引擎”（多智能体/skills 注入/Notebook/长链路分析）。**

更具体的分层是：

- Claw 层（浅，默认路径）：
  - 用户入口与会话（渠道/命令/路由）
  - “轻任务”直接跑 ScienceClaw 的 workflow/atomic skills
  - 输出仍然必须是 ScienceClaw 的 runDir 产物包（manifest + artifacts + logs）
- Pantheon 层（深，升级路径）：
  - 多智能体协作与深度分析（例如单细胞/空间组学的 best practices skills、Notebook 交互式分析、复杂工具链）
  - 执行时间长、步骤多、需要反复探索的任务
  - 最终也要回落到“可交付物”层：把关键结果写入 ScienceClaw 的 artifacts（或产出一个可被 ScienceClaw 收敛/封装的结果目录）

因此我们真正要做的不是“迁移技能”，而是把“升级路径”做成一个明确接口：

- Claw orchestrator 判断任务深度：浅任务走 ScienceClaw；深任务触发 Pantheon team。
- Pantheon 跑完以后，把结果以确定路径/文件名落盘，供 Claw 读取并封装成 runDir（或直接让 Pantheon 写入指定 runDir 的 artifacts）。

说明：我之前做的 “ScienceClaw -> Pantheon package tools” 仍然有价值，但它更适合作为：

- 本地验证与开发 harness（在 Pantheon UI 里快速调用 ScienceClaw 看 artifacts）
- 或者当你希望 Pantheon 主导交互时的备选形态

如果你的产品主线是“Claw 主导交互”，那 Phase 3 的重点应转为 “Claw 调 Pantheon 的 bridge”，而不是反向调用。

## 1) Phase 3 的主线（Mainline）

只做 1 个“能卖、能 demo、能复盘”的工作流包：

**Variant Annotation & Brief（变异注释与简报包）**

- 输入：用户提供本地 `*.vcf`（可选：样本元信息、候选基因列表、参考数据库路径）
- 输出（必出）：`variants.tsv/json + evidence.json + citations.bib + brief.md + manifest.json + logs/`
- 离线优先：不依赖外网即可跑出“可用的注释与简报”。
- 在线增强（可选）：网络可用时补充更多数据库字段或链接，但不能改变离线产物结构。

选择这个主线的原因（工程现实约束）：

- scRNA/空间组学工作流链条长、依赖重，Phase 3 做不出稳定 TTFR。
- 变异注释 workflow 更短、更可控，更容易在“云端 + 本地文件输入”场景闭环。
- 当前仓库已 vendoring 了 `openclaw-scientific-skill`，包含可复用脚本（例如 `scripts/vcf_annotate.py`）。Phase 3 可以“复用实现细节”，但对外输出必须服从 ScienceClaw 的 artifact contract。

## 1.2) Phase 3 的第二主线（同样重要）：Omics 深度能力的交付壳（QC + 注释）

如果你们的 Phase 3 同时想覆盖单细胞/空间组学（而不仅是 VCF），推荐把 Omics 作为“第二主线”，先交付“可复盘壳”，再逐步自动化执行：

- Workflow：`scienceclaw_workflow_omics_kickoff`
- 交付：固定 artifacts 模板（analysis_plan/environment/perf/qc/annotation/figures）+ 非空 citations/evidence

这样做的好处是：

- 不阻塞 TTFR（不强依赖 scanpy/scvi/rapids 的安装成功）
- 深度分析可以先在 Pantheon/notebook 做，但产物结构与审计标准从第一天就统一

执行版 playbook 见：

- `docs/SCIENCECLAW_P3_OMICS_PLAYBOOK.md`

## 1.5) Phase 3 依赖 Pantheon 自有 skills（在“行业标准前提下”怎么用）

结论：**可以依赖，而且这是更“行业标准”的做法**，但要把依赖放对层级。

推荐的依赖方式（不改变分层）：

- Pantheon skills（`.pantheon/skills/omics/...`）承担“深度任务的方法论与最佳实践”：
  - 单细胞/空间组学的 best practices、分析步骤、常见陷阱、参数选择建议
  - “多智能体协作角色分工”（leader/analysis_expert/biologist/reporter/system_manager）
- ScienceClaw workflow 承担“交付标准与审计”：
  - 真正执行（跑脚本/跑 notebook/跑 pipeline）
  - 产物包落盘（manifest + artifacts + logs）
  - 证据链与引用的结构化输出（evidence.json + citations.bib）

为什么要这样分层：

- Pantheon 的技能注入很强，但它不天然约束“每次运行落包、可复盘、可审计”。
- ScienceClaw 的核心卖点就是“产物包与证据链”，不能为了复用 Pantheon 而牺牲这个。

因此 Phase 3 的“科研能力”可以依赖 Pantheon skills 把深度分析做得更像专家团队，但最终交付必须仍回落到 ScienceClaw 的 artifact bundle（否则很难产品化验收）。

## 1.6) Pantheon Skills 迁移清单（先做什么，后做什么）

本阶段先不做 bridge/daemon，不做“跨系统全自动闭环”。先把 Pantheon 的现成技能体系里“最值钱且可控”的部分迁移成我们 Phase 3 的交付规范与模板。

详见：

- `docs/SCIENCECLAW_P3_PANTHEON_SKILLS_ADOPTION.md`

## 2) Phase 3 的产品交付形态（对齐竞品的“行业一流标准”）

Phase 3 不是“新增几个脚本”，而是交付一个 **Domain Pack**：

- 明确的 workflow 名称与入口（一个命令即可跑出产物包）
- 明确输入契约（flags、文件、可选配置）
- 明确输出契约（artifacts + manifest + logs，schema 可演进）
- 明确“离线 baseline”和“在线增强”的边界
- 明确自检（selfcheck）与回滚（rollback）策略

## 3) Skills 架构（建议分解）

目标：每个原子 skill 都“薄且可测”，workflow 只做编排，避免变成单体大脚本。

### 3.1 Workflow Skill（L4 领域包工作流）

1. `scienceclaw_workflow_vcf_annotate_brief`
- 负责：串联原子技能，统一落产物包，生成最终 `brief.md`
- 不负责：复杂解析/注释实现细节（全部下沉到原子技能）

### 3.2 Atomic Skills（L4 原子能力）

2. `scienceclaw_bio_vcf_validate`
- 输入：`--vcf`
- 输出：`artifacts/vcf.stats.json`（样本数、变异数、字段缺失统计、格式问题列表）
- 目的：把“数据问题”在最前置暴露，避免后续 silent failure

3. `scienceclaw_bio_vcf_annotate`
- 输入：`--vcf`，可选 `--reference-dir`（本地数据库目录）
- 输出：
  - `artifacts/variants.annotated.tsv`
  - `artifacts/variants.annotated.json`
  - `artifacts/evidence.json`（至少能回指到本地 vcf 文件与注释来源）
  - `logs/annotate.log`
- 实现策略：
  - 优先复用 vendored 脚本实现细节（如 `vendor_openclaw_scientific_skill/scripts/vcf_annotate.py`）
  - 但对外输出字段、文件名、manifest 记录必须服从 ScienceClaw 规范

4. `scienceclaw_bio_variant_prioritize`（Phase 3 可选，但推荐）
- 输入：`variants.annotated.*` + 可选候选基因列表（`--genes`）
- 输出：
  - `artifacts/variants.prioritized.tsv`
  - `artifacts/priority_rationale.json`（可复盘规则：过滤条件、阈值、原因）

5. `scienceclaw_report_variant_brief`
- 输入：`variants.prioritized.tsv`（或 annotated.tsv）+ evidence + citations
- 输出：`artifacts/brief.md`（结构化模板，LLM 仅做可选增强）

### 3.3 Shared Lib（仅限 skill 内部复用）

Phase 3 禁止跨 skill 直接 Python import 共享业务代码（会导致版本治理崩溃）。

允许的复用方式：

- 复制极小的纯函数（< 200 行）到各 skill 的 `lib/`
- 或者把复用逻辑做成 1 个原子 skill，通过 artifacts 作为接口复用

## 4) Phase 3 产物包规范（在 Phase 2 基础上扩展，不破坏）

沿用：

- `manifest.json`（schemaVersion=1）
- `artifacts/evidence.json`（EvidenceItem[] v1）
- `artifacts/citations.bib`

新增（Phase 3 workflow 的约定文件名，便于下游工具消费）：

- `artifacts/variants.annotated.tsv`
- `artifacts/variants.annotated.json`
- `artifacts/variants.prioritized.tsv`（如果做 prioritization）
- `artifacts/variants.summary.json`（可选：统计摘要，给 UI/报告用）

证据链（evidence.json）在 Phase 3 的要求：

- 必须包含对输入文件的来源引用：
  - `source: "file:/abs/path/sample.vcf"`
  - `locator: "offset:..."` 或 `locator: "abstract"`（此处更推荐 `offset` 或 “row:<n>” 扩展，后续可升级为结构化 locator）
- 必须包含对“注释数据库版本/来源”的记录方式：
  - v1 推荐写进 `manifest.json.environment` 或 `artifacts/variants.summary.json`
  - evidence.json 可包含 1 条 “database provenance” 类型的 EvidenceItem（quote 里写版本号/日期/文件 hash）

## 5) 离线优先与在线增强（边界要硬）

离线 baseline（必须保证）：

- 在无外网的 VM 上，给定本地 VCF，工作流能在合理时间（建议 < 60s for small VCF）跑完并产出完整 bundle。
- citations 至少包含 1 个“数据来源/工具来源”的条目（可以是 `@misc{...}` 占位），保证 pipeline 永不输出空 citations。

在线增强（可选）：

- 网络可用时可以补充外部数据库链接、补充字段、补充解释，但不能改变 artifacts 的核心文件名与结构。

## 6) 里程碑与验收（两周节奏，强交付）

### Week 1：做出可 demo 的 Domain Pack MVP

- 新增 `scienceclaw_bio_vcf_annotate` 原子 skill：能从 VCF 产出 `variants.annotated.tsv/json`，并落 manifest/evidence/logs。
- 新增 `scienceclaw_workflow_vcf_annotate_brief`：把结果模板化成 `brief.md`。
- 新增 1 个 smoke test 输入（小 VCF）用于 selfcheck。

验收（pass/fail）：

- 在全新 VM（root 用户）上，`installer -> workflow` 一条链路跑通。
- 输出 bundle 内必有：
  - `manifest.json`
  - `artifacts/variants.annotated.tsv`
  - `artifacts/brief.md`
  - `artifacts/evidence.json`（非空）
  - `artifacts/citations.bib`（非空）

### Week 2：治理与质量（把它变成“产品”）

- 引用/证据链收敛：workflow 尾部统一调用 `scienceclaw_citation_normalize`（Phase 2 资产复用）。
- 增加 `scienceclaw_bio_vcf_validate`（前置数据质量门槛）。
- 增加 `scienceclaw_bio_variant_prioritize`（可选，但最好做一个可解释规则版）。
- 在 `pack.json` allowlist 中纳入 Phase 3 skills，并更新 packVersion。

验收（pass/fail）：

- 同一份 VCF 连跑 3 次，每次产生不同 runDir，manifest 合法 JSON，且 `variants.annotated.tsv` sha256 被记录。
- 常见失败（VCF 格式错、缺依赖、缺输入文件）都能给出 1 行修复建议，并且失败也落包（logs + manifest）。

## 7) 风险与决策点（现在就锁）

- 数据库策略：Phase 3 不做“全量 ClinVar/gnomAD 内置”，否则交付周期会炸。
  - 建议：先支持用户传入 `--reference-dir`，并在 `variants.summary.json` 记录参考数据的 hash/version。
  - 后续再做可选的 `scienceclaw_ref_fetch`（下载+缓存+校验），作为 Phase 3.1 或 Phase 4。
- LLM 角色：只做“解释/总结增强”，不能承担注释正确性，避免不可复盘。
- License：只 vendoring 有明确许可（MIT/Apache）。对不清晰 license 的 repo，只学结构，不直接拷代码。

## 8) 下一步建议（最短可落地路径）

如果你的目标是“尽快形成可用的行业标准交互”，建议按两条线并行但不互相阻塞：

1. 交互线（Pantheon）：把 ScienceClaw workflow 做成 Pantheon UI 的一等公民
   - 通过 `packages.scienceclaw.*` 工具，UI 一键触发 Phase 2/Phase 3 workflows。
   - 用 Pantheon 的 team template 把“leader/analysis/reporter”跑起来，但执行落地仍由 ScienceClaw 负责。

2. 能力线（ScienceClaw Phase 3）：只做 1 个 Domain Pack workflow（上文主线）
   - 先保证离线 baseline + 可复盘产物包。
   - 再用 Pantheon skills 去提升分析质量与解释质量（而不是改执行框架）。
