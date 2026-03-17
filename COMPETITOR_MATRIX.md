# 竞品矩阵（仅 Claw 范围）

范围：只聚焦“Claw 形态”的产品/项目（OpenClaw 核心 + 云端托管/衍生形态 + 科研 claw 技能包）。
排除：邻接替代品（Zotero/Obsidian/Elicit 等），因为当前阶段我们的目的不是市场竞品大战，而是快速对齐并落地到 OpenClaw 配置与 skills 包。

## 我们要优化的目标（产品优先）

矩阵只看三条主链路：

1. 首次成功链路（TTFR, Time-to-first-result）：部署 -> 配模型 -> 生成第一份可用产物
2. 科研工作流链路：文献 -> PDF -> 证据链/引用 -> 报告产物
3. 可运营链路：升级、治理、安全、可观测

## 矩阵（v0 -> v0.1 已初步填充）

评分说明：

- 0 = 缺失
- 1 = 部分具备
- 2 = 默认具备/成熟可用

列定义：

- 交付（Delivery）：镜像/模板？是否引导式配置？TTFR 目标？
- 技能层（Skills Layer）：原子/大一统？是否有 orchestrator？是否有版本策略？
- 产物（Artifacts）：manifest/provenance？引用？可复盘产物包？
- 运维（Ops）：升级/回滚、日志、默认安全策略
- 商业化（Monetization）：主要“转化点”在哪里（API tokens、托管、模板等）

| 样本 | 交付 | 技能层 | 产物 | 运维 | 商业化 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| OpenClaw OSS（上游） | 2 | 2 | 1 | 2 | 0 | 上游提供完整 control-plane 与 skills 解析优先级；但“科研产物包/证据链”不作为强制默认 |
| sciClaw（科研工作流） | 2 | 2 | 2 | 2 | 0 | 单二进制 Go runtime + 生命周期 hooks + `~/sciclaw` 单目录审计；把“研究工作”当成一条可复盘闭环 |
| LabClaw（科研技能库） | 2 | 2 | 1 | 1 | 0 | 211 个 `SKILL.md`，强一致的 skill 模板与分域目录；强调“一条消息 install 全量技能” |
| ClawBio（生信技能库） | 1 | 2 | 2 | 1 | 0 | 强调每次分析输出可复现包（commands/env/checksums）；目录里有 orchestrator 与 `catalog.json` |
| openclaw-scientific-skill（综合科研 skill） | 1 | 1 | 0 | 0 | 0 | 单一“超大 skill”，用 references 文档堆能力面；更像知识包而不是可验收 workflow |
| 华为云 镜像/模板（交付形态） | 2 | 2 | 1 | 2 | 2 | 这是交付/转化路径样本，不是 skills 架构样本：核心是镜像即用 + 引导接 MaaS 模型消耗 |
| AutoGLM/OpenClaw 托管形态 | 0 | 0 | 0 | 0 | 0 | 待补充可验证 GitHub 架构证据后再填（避免凭印象打分） |

## 矩阵输出（交付物）

从矩阵直接产出两样东西：

- “行业一流标准”验收清单（v1）
- ScienceClaw v1 范围：1 个主产物 + 10 个核心技能 + 1 个 orchestrator

## 证据链接（用于评审时快速打开）

说明：这里先放“最载荷”的入口链接，后续每一行评分都应能回指到某个明确来源。

- OpenClaw 上游仓库：`https://github.com/openclaw/openclaw`
- OpenClaw 配置参考（skills/providers 等）：`https://docs.openclaw.ai/gateway/configuration-reference`
- sciClaw 仓库（README/结构/安装）：`https://github.com/drpedapati/sciclaw`
- sciClaw hooks 文档（审计/策略/provenance）：`https://sciclaw.dev/docs.html`
- LabClaw 仓库（README/目录/skill 格式）：`https://github.com/wu-yc/LabClaw`
- ClawBio 仓库（README/skills/catalog）：`https://github.com/ClawBio/ClawBio`
- ClawBio 可复现性说明（commands/env/checksums）：`https://clawbio.github.io/ClawBio/`
- openclaw-scientific-skill 仓库（README/SKILL.md/脚本）：`https://github.com/Zhaozilongxa/openclaw-scientific-skill`

## 对齐结论（先抓 Research Workflow Chain）

从这些 GitHub 样本里抽象出来的“行业一流标准做法”，集中在三件事：

- 1. 产物包是第一等公民：sciclaw 用 hooks 把审计写进运行环路；ClawBio 把可复现包当作输出的一部分，而不是事后补文档。
- 2. 技能不是“功能列表”，而是“可组合工作流单元”：LabClaw/ClawBio 都有明确的分域目录与一致的 skill 结构；并且存在 orchestrator/编排入口。
- 3. 安装与升级要像产品：LabClaw 把“install repo”做成一条消息；sciclaw 通过 brew tap + companion tools 让 TTFR 可控。

## 我们当前差距（聚焦可交付）

基于现有 ScienceClaw 实现（OpenClaw 已跑通，MVP skills 已生成骨架），与上述样本相比当前的 Top 差距：

- 缺“v1 主产物的一键闭环”：我们有检索与 PDF 抽取的原子技能，但缺 `pdf_fetch` 与 `brief_compose`，导致无法产出 `brief.md + citations + evidence.json`。
- 缺“审计/证据链的默认机制”：我们有 manifest 设计，但缺像 sciclaw hooks 那样的运行环路审计与“失败也产出可复盘包”的硬约束。
- 缺“技能包的产品化安装方式”：目前还没做到像 LabClaw 一样一句话 install 或一条脚本安装到 workspace，并完成依赖检查与自测。
- 缺“技能治理最小集”：allowlist、版本锁定、回滚策略、以及最基础的安全扫描/禁用能力尚未落地。
