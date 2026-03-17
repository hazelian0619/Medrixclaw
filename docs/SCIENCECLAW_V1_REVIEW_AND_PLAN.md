# ScienceClaw v1 严格评审与行动方案

已审阅来源：`养成路径.docx`（2026-03-15）。
评审视角：大厂技术产品经理（产品功能导向，强交付、强验收）。

本文把当前“叙事稿”转成三件可执行的东西：

- 清晰主线（mainline）
- 相对当前实现的严格差距分析（gap analysis）
- 2 周可落地的行动计划 + 验收标准

## 1) 主线（文档真正想完成什么）

方向正确的核心判断：

- OpenClaw 更像执行/控制平面（identity + memory + skills + session orchestration），不是“某个模型的聊天壳”。
- “科研 Claw”的差异化应沉到 skills/workflow 层，而不是靠换模型。
- 正确的产品节奏是：先做到行业级 cloud 基线，再做科研工作流，再做生信差异化，最后补平台治理（版本/回滚/运维）。

文档也提出了合理的分层（L0..L5）与分期路线图：

- 阶段 1：行业基线（云端托管、Web/办公入口、默认会话、记忆、健康检查）
- 阶段 2：科研公共价值（文献/PDF/表格/笔记/报告）
- 阶段 3：生信差异化（单细胞/空间组学/药物发现，以“工作流包”形态交付）
- 阶段 4：平台化升级（技能治理、发布通道、回滚、运营/可观测）

## 2) 严格评审（哪里强 / 哪里现在还不可交付）

### 强项

- 框架正确：把 OpenClaw 当 control-plane，把 skills 当产品表层。
- 排序正确：baseline -> workflows -> differentiation -> governance。
- 差异化抓手正确：
  - 证据链/引用质量（evidence chain）
  - 可复盘产物包（artifact bundle）
  - 工作流打包（卖 4 个能 demo 的 workflows，而不是“53 个技能”）

### 现在还不可交付/缺失（Top 阻塞）

1. 缺 v1 的“单一主产物（primary artifact）”定义。
   - 文档覆盖面很广（文献、PDF、表格、报告、生信、监控），但没有明确 v1 让用户“付费/复用”的那份最终输出是什么。
   - 没有主产物，就无法做范围控制、验收标准、对外 demo 与销售话术。

2. 缺可量化验收标准（TTFR + 质量门槛）。
   - 文档提到“验收”概念，但缺少可执行的 pass/fail checklist。
   - 需要一份短验收：`新用户 -> 部署 -> 配置 -> 运行 -> 产物包落地`。

3. 文档形态不是 PRD/spec，更像多轮讨论的拼接稿。
   - 重复段落、引用占位、判断与决定混杂。
   - 结果是工程无法对齐、评审无法聚焦、执行无法拆分。

4. “会话/记忆按科研项目治理”的方向正确，但缺 schema。
   - 提到把 session 映射到 project/topic/experiment/patient/task，这是对的。
   - 缺：命名规则、长期记忆 vs 项目记忆边界、写入权限（科研/医疗场景是硬要求）。

5. 技能治理意识正确，但缺落地规格与流程。
   - 文档提到 manifest/version/audit/rollback，但没有 manifest 格式、allowlist 策略、升级/回滚流程。

6. 入口策略偏多。
   - “飞书 + Web + 后续企业 IM”可行，但 v1 必须定一个主入口，否则集成会吞掉所有时间，科研工作流闭环做不出来。

## 3) 目前实现情况（现实校准）

截至 2026-03-15（结合我们已完成的环境与配置工作）：

- 阶段 1（行业基线）：部分完成
  - OpenClaw 已安装，gateway 健康（systemd user service）。
  - 模型 provider 已配置为华为云 MaaS GLM-5，probe 为 OK。
  - Web dashboard 仍为 loopback-only（需要 SSH tunnel），尚未产品化。

- 阶段 2（科研公共层）：已启动但未集成为默认体验
  - 本地已生成 ScienceClaw MVP skills 包骨架（PubMed 检索 + PDF 抽取 + orchestrator 占位）。
  - 但尚未默认安装到服务器 workspace。
  - 输出规范已按每 run 生成 `manifest.json + artifacts/ + logs/` 设计。

- 阶段 3/4：未开始（生信工作流包；技能治理/发布通道）

## 4) 必须锁定的关键决定（不锁就必然滑坡）

必须锁定一个 v1 主产物（建议，最符合产品功能导向）：

- **证据链文献简报（Evidence-backed literature brief）**：
  - 输入：topic query（可选：PDF）
  - 输出：`brief.md` + `citations.bib` + `evidence.json`
  - 这会自然反推 skills：search -> fetch -> extract -> cite -> summarize。

这是最短路径的行业级 demo，也与文档主线一致。

## 5) 两周执行计划（可落地）

### 第 1 周：做出“可演示 baseline”

1. 锁定并写清产物包规范（v1）。
   - 必须包含：
     - `manifest.json`（inputs、commands、environment、timestamps）
     - `artifacts/brief.md`
     - `artifacts/citations.bib`
     - `artifacts/evidence.json`（quote-level provenance：source + page/offset 尽可能记录）
     - `logs/*.log`

2. 让 skills 包可以“一条命令”安装到 OpenClaw workspace。
   - `workspace/skills/scienceclaw_*` + Python 依赖安装脚本。

3. 最小闭环实现为 4 个原子技能 + 1 个 orchestrator：
   - `literature_pubmed_search`（已存在）
   - `literature_pdf_fetch`（缺：通过 DOI/PMCID best-effort 下载）
   - `pdf_extract_basic`（已存在）
   - `review_brief_compose`（缺：把抽取结果生成 brief.md + citations）
   - `scienceclaw_orchestrator`（路由或触发整条 pipeline）

第 1 周验收：
`new VM -> configure key -> run 1 command -> artifact bundle created`

### 第 2 周：加固到“行业基线”

1. TTFR（Time-to-first-result）优化：
   - 引导式配置命令
   - 依赖检测 + 1 行修复提示

2. 轻量治理（governance-lite）：
   - curated 技能 allowlist
   - skills 版本锁定
   - 基础回滚（保留上一个 skills 包快照）

3. 可观测（observability）：
   - run 目录命名一致
   - gateway 日志关联到 run
   - 失败时返回“可执行修复命令”，而不是一段 stacktrace

第 2 周验收：
- 5 个 demo query 端到端跑通，每次 < 3 分钟产出产物包
- 典型失败（缺依赖、API 401/429/5xx）都能给出明确修复指令

## 6) 立刻要做的事（把 docx 变成可执行规格）

把 `养成路径.docx` 的核心结论落成这三份 markdown（已生成/维护）：

- `docs/SCIENCECLAW_V1_REVIEW_AND_PLAN.md`（本文）
- `docs/SCIENCECLAW_V1_ARTIFACT_SPEC.md`（字段与规范）
- `docs/SCIENCECLAW_SKILL_CONTRACT.md`（技能输入输出与治理约束）
