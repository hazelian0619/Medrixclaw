# MetrixClaw 通用 Claw 标准化评分卡（2026-03-31）

目标：从“后端可一键接入云端、用户可立即可用”的角度，评估当前仓库与行业通用 Claw 基线的差距。

评分区间：0-100（越高越接近成熟通用 Claw 水平）。

## 总分

- **78 / 100**

结论：

- 已达到“可交付内测与后端对接”的水平。
- 距离“成熟通用 Claw（企业生产级）”仍有 3 类关键差距：平台化治理、线上可观测性、租户级安全策略。

## 维度评分

| 维度 | 权重 | 当前分 | 评分依据（仓库证据） |
|---|---:|---:|---|
| 一键云部署自动化 | 20 | 16 | 已有 `scripts/one_click_cloud_deploy.sh`，串联 deploy/installer/mandatory verify/acceptance，并输出 deploy report JSON |
| 必选技能治理 | 15 | 15 | `skills/metrixclaw_meta/mandatory_skills.json` + `verify_mandatory_skills.py --strict`，当前 mandatory 26/26 可通过 |
| 首次使用引导 | 10 | 8 | `docs/CLOUD_ONBOARDING_CHAT_GUIDE.md` + `skills/metrixclaw_meta/onboarding_quickstart.json` 已提供首 3 轮引导模板 |
| 通用能力覆盖面 | 15 | 12 | 文献/PDF/表格/VCF/omics 工作流齐备，且有 orchestrator 路由入口 |
| 验收与质量门控 | 15 | 12 | phase2/phase3/all 验收脚本 + 质量门控技能 + 包契约校验 |
| 可观测与审计 | 10 | 7 | runDir + artifacts + manifest + deploy report 已有；缺少统一 metrics/exporter 与告警策略 |
| 后端接入契约清晰度 | 10 | 6 | README/Runbook 已有路径与命令；缺少正式 API 契约与版本化兼容矩阵 |
| 企业级安全与多租户 | 5 | 2 | allowlist/离线模式已有；缺少租户隔离、配额、细粒度 RBAC、审计留存策略 |

## 差距清单（按优先级）

P0（建议立即补）：

1. **运行时契约标准化**：给 orchestrator 输出增加固定 JSON schema（`intent`, `runDir`, `artifacts`, `status`, `errorCode`），避免后端做不稳定解析。
2. **线上观测最小闭环**：增加统一执行日志字段（trace_id、skill_id、duration_ms、exit_code），并落地到可采集目录或 stdout JSON line。
3. **失败恢复策略**：在 one-click 流程中补失败分类与重试建议（网络、依赖、权限、技能缺失），减少人工排障时间。

P1（内测后补）：

1. **多租户策略**：按租户/project 建 runDir 隔离与限额。
2. **权限模型**：区分普通用户、研发、管理员可用 skill 集。
3. **版本兼容矩阵**：维护 `packVersion -> required skill versions` 对照，防止灰度期不兼容。

P2（规模化前补）：

1. 统一指标与告警（成功率、P95 耗时、失败类型分布）。
2. 异步任务队列化（长任务与并发限流）。
3. A/B 引导文案与工作流路由优化（提升首次成功率 TTFR）。

## 对标结论（纵横向）

- 横向（通用 Claw）：你们已经覆盖“可用能力 + 一键部署 + 基线验收”，这部分已接近行业通用交付线。
- 纵向（生信差异化）：VCF/omics 路径是明显优势，建议保持“通用技能基线 + 生信专业工作流”双层架构，不要只做通用壳。
- 当前最该补的是“平台化治理能力”，不是再堆更多 skill 数量。
