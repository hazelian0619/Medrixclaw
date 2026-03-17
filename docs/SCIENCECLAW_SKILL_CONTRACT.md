# ScienceClaw 技能契约（草案）

目的：定义所有会随 ScienceClaw 一起交付的技能（skill）必须满足的最小“产品/工程约束”，避免技能堆积后不可维护、不可验收、不可审计。

## 1) 技能类型（分层）

- 原子技能（atomic skill）：只做一件事，产出中间 artifacts。
- 工作流技能（workflow skill）：把多个原子技能串成 pipeline。
- 编排/路由器（orchestrator）：把用户模糊意图路由到某个原子/工作流技能（可选：触发整条 pipeline）。

规则：优先原子技能；workflow/orchestrator 必须“薄”，并且可测试、可回归。

## 2) 每个 `SKILL.md` 的必填字段

每个技能必须明确：

- 目的 / 适用场景（when-to-use）
- 输入（flags、文件、env vars）
- 输出（产物路径 + 格式，必须写清楚）
- 依赖（系统依赖 + Python/Node 依赖）
- 失败模式（常见报错 + 1 行修复命令）
- 安全约束（明确禁止做什么）

## 3) 证据与复盘（provenance）要求

每次技能运行必须：

- 在 `projects/<project>/runs/<runId>/` 下创建 run 目录
- 写入/更新 `manifest.json`
- 产物只允许写入 `artifacts/`
- 日志只允许写入 `logs/`

## 4) 安全/治理要求（v1 最小集）

- 禁止把密钥打印到 stdout/stderr。
- 若技能使用外部 API：
  - 从 env var（或 OpenClaw secret ref）读取 key
  - 如需记录，最多记录 key 的末尾 4 位（用于排障定位，不泄露）
- 禁止启动对外网络服务（不要开端口）。

## 5) 可测试性（v1 最小集）

每个技能的 `SKILL.md` 必须包含一条“冒烟测试（smoke test）”指令，满足：

- 可在一台全新 VM 上执行
- < 60 秒完成（MVP 阶段）
- 至少产出 1 个 artifact + 1 个 `manifest.json`

## 6) 维护约定（RunContext 同步）

说明：为了避免跨-skill import 导致的版本治理问题，ScienceClaw v1 允许每个 skill 复制一份 `lib/run_context.py`。

风险：复制会导致“修一个 bug 需要改 N 份”的漂移风险。

约定：所有 `lib/run_context.py` 必须与 canonical 模板保持一致；发布前必须执行：

```bash
python3 scienceclaw/skills/scienceclaw_meta/sync_run_context.py --check
```
