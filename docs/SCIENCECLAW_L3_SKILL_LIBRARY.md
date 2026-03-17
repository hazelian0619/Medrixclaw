# ScienceClaw L3 科研公共技能库（完成版 v1）

目标：把 L3 这层做成“行业普遍一流标准”的科研能力底座。不是堆功能点，而是把 **链路、产物、治理、可复现** 做成硬约束。

L3 的定位（对标竞品的共同点）：

- 面向科研通用主链路：文献 -> PDF -> 证据/引用 -> 报告产物
- 产物包（runDir）是第一等公民：`manifest.json + artifacts/ + logs/`
- 差异化点：**证据链（Evidence）+ 引用治理（Citations）+ 离线可跑 + 可审计/可复现**

本文件回答三件事：竞品 L3 怎么做，我们差什么，我们的 L3“完成版”应该长什么样。

## 0) 竞品 L3 的标准形态（我们要对齐什么）

### sciClaw（更像“科研运行时 + 治理层”）

- **Hooks/Audit**：生命周期 hooks，默认写 workspace 级 JSONL 审计日志（不是事后补日志）。
- **Supply-chain**：skills 安装时做 frontmatter 校验、size limit、binary rejection，并写 `.provenance.json`（source URL + sha256 + installedAt）。
- **工具链内置**：把 PubMed/文档审阅/办公工具链当 runtime 标配，TTFR 依赖一次性交付（brew/Docker）。

我们应该借鉴：`provenance + 默认审计 + 安装门槛（验证/限制）`。

### ClawBio（更像“领域 Orchestrator + Repro Contract”）

- **Orchestrator 真实存在**：路由、规划、组装报告、链式调用都在 orchestrator 层解决。
- **Reproducibility Contract**：每次分析都输出 commands/env/checksums/audit（对外可验收）。
- **Local-first + explicit network boundary**：联网是可选增强，不是默认依赖。

我们应该借鉴：`orchestrator 可执行 + repro bundle 强制化 + 默认 report 组装`。

### LabClaw（更像“规模化技能目录与模板”）

- **211 个 SKILL.md**：强一致的模板（when/how/output），按 domain 分目录；一句话 install。
- 但对“产物包/证据链 schema”的强约束较弱（它主要交付的是 skill library，而不是可验收的 workflow bundles）。

我们应该借鉴：`目录信息架构 + 模板一致性 + 一键 install 体验`。

### openclaw-scientific-skill（更像“单体知识包”）

- 覆盖面广，但偏“references 堆叠”，缺乏稳定的产物契约与可验收 workflow。

我们应该借鉴：`可复用的脚本/参考资料`，但 **不抄它的单体结构**（会破坏治理与验收）。

## 1) ScienceClaw 当前 L3 已具备什么（优势项）

我们在 L3 这一层已经有明确的“可验收产物包”硬约束：

- 有 `evidence.json` schema（见 `SCIENCECLAW_V1_ARTIFACT_SPEC.md`），并在 workflow 里落盘。
- 有 `scienceclaw_citation_normalize` 做引用治理的“单点收敛”，并支持 `--run-dir` 写回同一个 runDir。
- 有离线闭环：PDF/表格链路不依赖外网。

额外加分（更像 ClawBio 的 L2 基座能力）：`scienceclaw_json_validate`、`scienceclaw_repro_export`、`scienceclaw_report_compose_md` 等“治理与交付”技能已存在。

## 2) 我们与竞品 L3 的核心差距（必须补齐才能叫 L3 完成版）

按“能否达到行业普遍一流标准”排序，Top 缺口是：

1. **缺 L3 默认质量门槛（lint/gate）**
   - 竞品是“默认产出可验收”；我们目前更多靠约定和人工 review。
   - 现状风险：`evidence/citations` 口径可能分裂，或出现“文件存在但内容不可用”。
   - 现状进展：已补 `scienceclaw_bundle_lint`，但还需要把它变成默认 gate（至少进入 selfcheck 与 workflow 尾处理）。
2. **Orchestrator 入口需要产品化（不只是“会路由”）**
   - ClawBio/sciClaw 的 orchestrator 不仅路由，还承担默认后处理（report/repro/audit）与链式调用的稳定策略。
   - 我们已补 `scienceclaw_orchestrator/run.py`（可执行入口），但还需要把“路由规则/后处理顺序/严格模式”的参数契约固化，并纳入 selfcheck/CI。
3. **缺 workspace 级 provenance / 审计默认机制**
   - sciClaw 在安装与运行环路里默认写 provenance/audit；我们目前主要是 run 级 manifest/logs，缺“安装来源 + 包级治理 + 默认审计策略”。
4. **缺“目录规模与模板化一致性”的产品化表达**
   - LabClaw 的强项是目录结构与模板一致性；我们需要把自己的 skill contract 模板化到每一个 skill（含 smoke test / I/O/失败模式）。

## 3) L3 完成版技能库（我们要交付的“公共科研能力”）

L3 不只是三条链路的 workflow，还必须包含“治理层与交付层”的公共技能，否则达不到竞品的产品标准。

### 3.1 三条科研主链路（每条必须有 workflow）

1. 文献链路：`query -> results -> evidence(abstract/pdf) -> citations -> brief`
2. PDF 链路：`local pdf -> extracted -> evidence(page locator) -> citations -> brief`
3. 表格链路：`pdf -> tables(json/csv) -> evidence(page) -> (optional) brief`

对应 workflow：

- `scienceclaw_workflow_lit_brief`
- `scienceclaw_workflow_pdf_brief`
- `scienceclaw_workflow_table_to_csv`

### 3.2 证据链与引用治理（L3 的核心护城河）

- `scienceclaw_citation_normalize`：证据/结果 -> 统一引用导出（BibTeX/RIS）+ evidence 去重（可写回 runDir）
- `scienceclaw_bundle_lint`：对目标 runDir 做“产物齐全 + evidence/citations 最小可用”校验（可作为 selfcheck/CI gate）

### 3.3 L3 必需的“交付与复现”公共能力（对标 ClawBio）

- `scienceclaw_report_compose_md`：把本次 run 的关键产物汇总成 `report.md`（交付友好）
- `scienceclaw_repro_export`：把 manifest 转成 `commands.sh + checksums + environment`（复盘升级为可复现）
- `scienceclaw_json_validate`：对 `manifest/evidence/citations.normalized` 等做结构校验（release gate）

### 3.4 L3 支撑底座（对标 sciClaw 的“runtime 工具链”思路，先做轻量版）

- `scienceclaw_fs_ingest`：把输入纳入 bundle（inputs hashing）
- `scienceclaw_http_fetch`：可控下载（allowlist/offline plan）
- `scienceclaw_format_convert`：确定性转换
- `scienceclaw_data_profile`：数据画像

## 4) L3 验收清单（像产品一样验收）

### 4.1 单次运行必须满足

- runDir 必须包含：`manifest.json`、`artifacts/`、`logs/`
- 对 `lit_brief/pdf_brief/table_to_csv`：
  - `citations.bib` 必须存在且非空（允许 placeholder，但必须可追踪模式）
  - `evidence.json` 必须是 JSON array；主链路严格要求非空
- 产物必须可复盘：至少有 1 个 log（workflow.log / lint.log / normalize.log 等）

### 4.2 自动化 gate（必须落地到 selfcheck/CI）

- `scienceclaw_bundle_lint --strict --profile auto --run-dir <runDir>`

## 5) 下一步（把差距补成“完成版”）

P3 的 L3 侧补齐建议（按性价比排序）：

1. 把 `bundle_lint` 和 `citation_normalize(--run-dir)` 变成每条 workflow 的尾处理（统一治理出口）。
2. 固化 `scienceclaw_orchestrator/run.py` 的参数契约与默认后处理策略（normalize -> report -> repro -> lint），把它变成稳定产品接口（对标 ClawBio）。
3. 在 installer/deploy 阶段写最小 `.provenance.json`（source + sha256 + installedAt），补齐 sciClaw 的 supply-chain 基线。
