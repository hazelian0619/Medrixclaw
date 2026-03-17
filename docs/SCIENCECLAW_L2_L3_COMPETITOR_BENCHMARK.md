# ScienceClaw L2/L3 对标拆解（竞品做法 -> 我们的点位）

目的：把“行业垂直科研竞品”在 L2/L3 的典型做法拆解成可执行点位，并映射到 ScienceClaw 当前实现与缺口。

范围：

- L2 = 通用基础能力（文件/下载/转换/校验/报告/可复现性）
- L3 = 科研公共能力（文献检索、PDF/表格抽取、引用与证据链治理）

不讨论 L0 control-plane（OpenClaw）与 L4/L5 的完整产品化策略（只在与 L2/L3 强相关处引用）。

## 1) 我们现在的 L2（Base/Foundation）点位

原则：必须满足 `manifest.json + artifacts/ + logs/`；必须支持 `--no-llm` 或离线退化；不引入重依赖以保护 TTFR。

### 文件与输入面

- `scienceclaw_fs_ingest`
  - 点位：把用户本地文件纳入 bundle（`artifacts/inputs/`），输出 `ingest.json`（含 sha256/bytes），为后续 workflow 提供稳定输入。

### 可控下载（安全与离线退化）

- `scienceclaw_http_fetch`
  - 点位：默认域名 allowlist（供应链入口控制）；`--offline` 输出结构化下载计划（plan），在线输出 results+hash。

### 格式转换（确定性）

- `scienceclaw_format_convert`
  - 点位：PDF->text、CSV<->JSON、JSON pretty；输出 `conversion.json` + preview。

### 数据画像（办公交付常用）

- `scienceclaw_data_profile`
  - 点位：CSV/JSON（array-of-objects）画像输出 `profile.json + profile.md`。

### 质量门槛（结构校验）

- `scienceclaw_json_validate`
  - 点位：对 `manifest/evidence/profile/conversion/fetch_* / citations_normalized` 做快速校验，输出 `validation.json`（可作为 release gate / acceptance gate）。

### 可复现性导出（对标 ClawBio 的 repro bundle）

- `scienceclaw_repro_export`
  - 点位：从 `manifest.json` 导出 `commands.sh + checksums.sha256 + environment.txt + analysis_log.md`。
  - 价值：把“复盘”从“看日志”升级为“可以被复现”的交付物。

### 交付报告（对标 ClawBio 的 report.md 风格）

- `scienceclaw_report_compose_md`
  - 点位：汇总 inputs/commands/artifacts，并嵌入 brief/profile/preview/citations/evidence 等关键产物片段，生成 `report.md`。

## 2) 我们现在的 L3（Research-Common）点位

### 文献检索与 ID 规范化

- `literature_pubmed_search`：PubMed 检索 -> 结构化结果 + BibTeX
- `scienceclaw_lit_resolve_id`：PMID -> PMCID
- `scienceclaw_lit_pdf_fetch_pmc`：PMC PDF best-effort 获取（非稳定主路径）

### PDF 与表格抽取

- `pdf_extract_basic`
- `scienceclaw_pdf_extract_structured`
- `scienceclaw_table_extract_from_pdf`

### 证据链与引用治理出口

- `scienceclaw_citation_normalize`：证据链 schema/去重/引用导出（BibTeX/RIS）
- `evidence.json` schema：SourceRef/Locator/quote_hash 去重规则（见 `SCIENCECLAW_V1_ARTIFACT_SPEC.md`）

## 3) 竞品对标：它们怎么做 L2/L3

以下为“可验证的工程做法”，不是主观印象。

### 3.1 sciClaw（重点：审计/供应链/工具链集成）

L2 倾向（通用工具链）：

- 通过“内置工具链”覆盖办公与转换：`pandoc-docx`、`imagemagick`、`pdf`、`xlsx`、`pptx` 等（更像把通用能力做成 runtime 标配）。
- Docker 镜像内置大量工具，TTFR 依赖镜像一次性交付（不是按 skill 单独 pip 安装）。

L3 倾向（科研公共）：

- PubMed 优先：`pubmed-cli` 作为研究与引用检查的基础工具之一。
- “claim-evidence alignment”作为写作/综述的默认要求（体现证据链思维）。

治理点位（对我们影响最大）：

- skill 安装写 `.provenance.json`（来源 URL + sha256 + 安装时间 + size），并做 size limit/binary rejection/pinned catalog（供应链硬化）。
- workspace 有 hooks JSONL audit log（把审计写进运行环路）。

参考（本地 clone）：

- `sciclaw/README.md`（Evidence & Provenance / Workspace Layout / 工具链）
- `sciclaw/pkg/skills/installer.go`（.provenance.json）

### 3.2 ClawBio（重点：可复现性 bundle 是第一等公民）

L2 倾向（通用基础能力）：

- **Reproducibility Contract**：每次分析输出 `commands.sh + environment.yml + checksums.sha256 + analysis_log.md`，且跟 report/figures/tables 同级。
- 通用 `checksums.py` / `report.py` 抽成公共库：报告 header 自动写 input checksum，结果写标准 envelope（result.json）。

L3 倾向（科研公共）：

- 把“网络调用”边界写死：数据处理不联网；联网只在 PubMed/结构数据库/安装依赖等特定情况。
- skill packaging 以 `SKILL.md + Python scripts + tests` 为主，但强调“复现包不依赖 agent”。

参考（本地 clone）：

- `ClawBio2/README.md`（Provenance & Reproducibility）
- `ClawBio2/docs/architecture.md`（Reproducibility Contract）
- `ClawBio2/clawbio/common/checksums.py`、`ClawBio2/clawbio/common/report.py`

### 3.3 LabClaw（重点：大规模 SKILL.md 库与模板一致性）

L2/L3 的形态与 sciClaw/ClawBio 不同：

- 主要交付 200+ `SKILL.md` 说明书，覆盖面广（检索、引用管理、写作等），但并不强制统一产物包/证据链 schema。
- 强项在“模板化与 catalog”：同类 skill 的说明结构一致，易于扩展与安装（`install https://github.com/wu-yc/LabClaw`）。

对我们的可用启发：

- 适合用来“抄模板/抄目录信息架构”，不适合直接作为受控执行基座（除非 wrapper 化输出契约）。

## 4) 对标结论：我们 L2/L3 还差什么

已补齐（对标最关键差距）：

- ClawBio 风格的 repro bundle：我们已补 `scienceclaw_repro_export`（基于 manifest 导出 commands/checksums/env/log）。
- “交付报告”统一模板：我们已补 `scienceclaw_report_compose_md`。
- 结构化产物校验：我们已补 `scienceclaw_json_validate`（可作为 acceptance gate）。

仍属增强项（不建议 P2 强行纳入受控基座）：

- docx/xlsx/pptx 深办公链路：sciClaw 用镜像内置工具链解决；我们若要引入，需要明确依赖策略（系统包 vs pip）与 TTFR 影响。
- 更强的 supply-chain 安装 provenance：sciClaw 是“install 时写 provenance”；我们当前部署是“copy skills to workspace”，如果要对齐，需要在 deploy/installer 阶段增加 provenance 记录与 pinning/rollback。

