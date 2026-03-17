# ScienceClaw Skills 架构设计（v1 提案）

定位：ScienceClaw 是“基于 OpenClaw 的科研发行版”。OpenClaw 提供 control-plane（会话、模型路由、工具调度、渠道），ScienceClaw 的价值沉到 Skills/Workflow 层，交付“可复盘、可审计、可重复运行”的科研产物。

本文目标：

- 参考竞品（sciClaw / ClawBio / LabClaw 等）的可验证做法，设计一套可扩展的 Skills 架构。
- 明确分层、命名、依赖、产物契约（artifact bundle）、治理策略与演进路线。

非目标：

- v1 不追求“覆盖所有科研领域”，先把一个主闭环打到行业一流 baseline。
- v1 不做重平台（多租户计费、完整权限系统），先用最小治理集把风险关住。

## 1) 我们从竞品学到的三条硬标准（必须抄）

1. **产物包是第一等公民（artifact bundle as first-class）**
   - sciClaw 把审计与策略通过 hooks 写进运行环路，并把产物集中到单目录，天然适配复盘与审计。
   - ClawBio 把可复现包（命令/环境/校验）作为每次分析的默认输出。
   - 结论：ScienceClaw 的“技能成功”定义必须是“产物包落地”，而不是“模型回了一段话”。

2. **技能是可组合的 workflow building blocks，而不是功能清单**
   - LabClaw/ClawBio 都体现出：原子技能 + 编排器（orchestrator）+ 统一模板，是可规模化的。
   - 结论：我们必须避免 `openclaw-scientific-skill` 那种“单一超大 skill”，那条路不可测试、不可治理、不可演进。

3. **安装/升级要像产品（TTFR 可控）**
   - LabClaw 强调一条命令装完整 skill library，TTFR 直接产品化。
   - 结论：ScienceClaw 必须提供“一键安装 + 自检”的 installer（脚本或 skill），把依赖安装、版本锁定、回滚做成默认能力。

## 2) Skills 分层（L0-L5 对齐法）

这不是目录结构，是职责边界。目录命名只是落地手段。

- **L0 控制层（OpenClaw）**：gateway、session、模型路由、工具执行沙箱、日志。
- **L1 入口层（Channels/UI）**：Web/飞书/Telegram 等入口，v1 建议主入口先只保留 Web（dashboard + SSH tunnel/反代），飞书在 Phase 2 做。
- **L2 通用基础能力层（Foundation Skills）**：文件/目录/项目管理、下载、缓存、格式转换、通用数据结构化。
- **L3 科研公共能力层（Research-Common Skills）**：文献检索、PDF 抽取、引用管理、证据链、表格抽取、报告模板。
- **L4 领域能力层（Domain Packs）**：生信（单细胞/空间/变异注释）、药物发现等，必须以“工作流包”方式交付，而不是散技能。
- **L5 治理与运营层（Governance/Ops Skills）**：技能白名单、版本锁定、升级/回滚、健康检查、自检、运行统计。

关键规则：

- v1 必须把 L3 做扎实，并且用 L5 把风险关住。
- L4 不做“泛化平台”，只做 1 个可演示工作流包即可（后续扩展）。

## 3) ScienceClaw v1 的“技能树”设计（不薄弱的版本）

### 3.1 核心原则

- 原子技能只做一件事，输入/输出明确，失败可 1 行修复。
- Workflow 技能只负责串联，不做复杂解析逻辑。
- Orchestrator 只负责路由与状态机，不直接写产物细节。
- 每个技能都必须落 `manifest.json + artifacts/ + logs/`（见 `SCIENCECLAW_V1_ARTIFACT_SPEC.md`）。

### 3.2 v1 核心技能（10 个，建议）

L2（基础）：

1. `project_init`：初始化项目目录与元数据（project slug、研究主题、默认输出模板）。
2. `artifact_bundle_init`：创建 run 包目录与 manifest（可作为公共库或轻量技能）。
3. `http_fetch`：安全下载（带 allowlist、重试、缓存、hash）。
4. `format_convert`：常用转换（PDF->text/json、docx->md、html->md）。

L3（科研公共）：

5. `literature_pubmed_search`：PubMed 检索（已存在骨架）。
6. `literature_resolve_id`：DOI/PMID/PMCID 互转与规范化（为 fetch 做准备）。
7. `literature_pdf_fetch`：从 DOI/PMCID/URL 获取 PDF 并落盘（缺，必须补）。
8. `pdf_extract_basic`：PDF 抽取（已存在骨架）。
9. `citation_normalize`：统一引用导出（BibTeX/RIS），并对来源做去重与合并。
10. `review_brief_compose`：把 evidence + citations 合成 `brief.md`（缺，必须补）。

L5（治理/运维，v1 最小）：

11. `scienceclaw_installer`：一键安装依赖 + 自检（也可用 bash 脚本实现，建议同时提供）。
12. `scienceclaw_selfcheck`：跑 2-3 个 smoke tests，输出可复制的排障建议。

说明：

- 这里列 12 个是因为 installer/selfcheck 对 TTFR 与交付质量太关键，不能拖到后面。
- L4 领域包（生信）不在 v1 核心技能里，但 v1 末尾可以预留 1 个 demo workflow 包（见下）。

### 3.3 v1 必须能卖的“4 个工作流（Workflow Packages）”

不要卖“技能数量”，要卖“可演示、可复盘、可复制”的工作流。每个工作流都必须产出同一种产物包结构。

Workflow 1：**证据链文献简报（主闭环）**

- 输入：query（可选：用户提供 PDF）
- 链路：`project_init` -> `literature_pubmed_search` -> `literature_pdf_fetch` -> `pdf_extract_basic` -> `citation_normalize` -> `review_brief_compose`
- 输出：`brief.md + citations.bib + evidence.json + manifest + logs`

Workflow 2：**PDF 证据链抽取（用于组会/审稿）**

- 输入：PDF（单篇或多篇）
- 链路：`project_init` -> `pdf_extract_basic` -> `citation_normalize` -> `review_brief_compose`
- 输出：同上，但 evidence.json 更强调页码与引用定位。

Workflow 3：**表格抽取到结构化数据（CSV/JSON）**

- 输入：PDF/图片里的表格
- 链路：`pdf_extract_basic`（或后续 `pdf_extract_tables`）-> `format_convert` -> `artifact_bundle` 落盘
- 输出：`tables.csv/json + evidence.json + manifest`

Workflow 4：**持续监控（每周新文献 digest）**

- 输入：topic query + cron 配置
- 链路：`literature_pubmed_search`（time window）-> `dedupe` -> `brief_compose` -> 通知渠道
- 输出：每周一个 run 包 + digest.md

## 4) 目录与命名约定（落地到 OpenClaw skills）

OpenClaw 技能目录约束：每个 skill 是一个顶层目录，里面有 `SKILL.md`。

建议命名规则（便于排序与治理）：

- `scienceclaw_<domain>_<verb>_<object>`
  - 例：`scienceclaw_lit_pubmed_search`
  - 例：`scienceclaw_pdf_extract_basic`

每个 skill 目录建议结构：

- `SKILL.md`（中文说明 + 1 条 smoke test 命令）
- `run.py`（或 `run.ts`）：可被 shell tool 直接调用的入口
- `lib/`：仅 skill 内部使用的公共代码（避免跨 skill import）
- `tests/`：可选，v1 只要求有 smoke test

## 5) 统一的“产物包/证据链”机制（产品护城河）

我们不做 sciClaw 那套 hooks 系统的全量复制，但必须达到同等效果的最小集合：

- 所有技能都必须调用同一套 `RunContext` 逻辑创建 run 包并写 manifest。
- “证据链”以 `evidence.json` 表达，最小字段：`source + locator + quote + usedIn`。
- 对失败的定义：失败也要落包（logs + 部分 manifest），并输出 1 行修复命令。

## 6) 治理与升级策略（v1 最小可用）

v1 不做重平台，但必须具备可交付的治理能力：

- allowlist：ScienceClaw 只启用 curated skills（我们自己的 + 可信外部库），默认不装未知来源。
- version pin：技能包作为一个版本整体发布（例如 `scienceclaw-pack@0.1.0` 概念），升级按版本。
- rollback：保留上一个版本 skills 目录快照（时间戳或版本号命名），一条命令回滚。
- selfcheck：每次升级后自动跑 smoke tests，失败则提示回滚。

## 7) 与我们当前实现的映射（现状与缺口）

已存在（MVP 骨架）：

- `literature_pubmed_search`
- `pdf_extract_basic`
- `scienceclaw_orchestrator`（目前只写了路由规则文档）
- `manifest/artifacts/logs` 的基础落盘逻辑

必须补齐（才能从“骨架”变成“产品闭环”）：

- `literature_pdf_fetch`
- `review_brief_compose`
- `installer/selfcheck`（脚本或 skill）
- “一键安装到云端 workspace”的交付方式（把 TTFR 产品化）

## 8) 执行计划（下一步怎么做，不跑偏）

第 1 周只做一件事：跑通 Workflow 1（证据链文献简报），并在华为云 OpenClaw 上“一条命令跑出产物包”。

- 补 `literature_pdf_fetch` 与 `review_brief_compose`
- 升级 orchestrator：支持 pipeline 模式
- 验收：5 个 query 端到端跑通，每次产出 `brief.md + citations + evidence.json`

第 2 周做交付质量：

- installer/selfcheck
- allowlist + version pin + rollback
- 失败可复盘（错误提示 1 行修复命令）

## 9) Phase 3 预告（领域差异化怎么做，避免“大而全”）

Phase 3 的原则：只交付 1 个可演示、可复盘、可复用的 L4 Domain Pack（工作流包），不要扩散成“生信脚本集合”。

建议 Phase 3 主线选型与架构见：

- `docs/SCIENCECLAW_PHASE3_PLAN_AND_ARCHITECTURE.md`
