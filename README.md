# MetrixClaw

> 面向科研场景的可部署 Claw 技能包：既有行业通用能力，也有生信深度能力。

## 你会得到什么

- 行业通用基线：文献检索、PDF/表格处理、数据转换、结构化交付。
- 生信深度能力：VCF 质检、VCF 注释、组学任务启动与交付。
- 工程可交付：每次执行都有 `runDir` 产物包（`artifacts/ + manifest.json + logs/`）。
- 后端可接入：一条命令打通云端部署、依赖安装、基线校验、验收。

## 一键云部署（后端入口）

```bash
cd scripts
METRIXCLAW_HOST=root@<your-vm-ip> \
METRIXCLAW_IDENTITY=~/.ssh/id_ed25519 \
METRIXCLAW_REMOTE_WORKSPACE=/root/.openclaw/workspace \
METRIXCLAW_SSH_PORT=22 \
./one_click_cloud_deploy.sh --phase 2
```

默认自动执行：

1. 同步技能到云端 workspace
2. 安装/修复运行依赖
3. 校验必选技能基线
4. 运行验收脚本（phase2/phase3/all）

部署报告输出：

- `projects/deploy_reports/deploy_<timestamp>.json`

## 本地快速自检

```bash
cd scripts
./metrixclaw_local_setup.sh
./metrixclaw_local_selfcheck.sh
```

## 必选技能基线安装

```bash
cd scripts
./metrixclaw_install_baseline.sh --workspace /root/.openclaw/workspace --clean
```

## 用户首次引导（开箱可用）

- 对话模板：`docs/CLOUD_ONBOARDING_CHAT_GUIDE.md`
- 机器可读模板：`skills/metrixclaw_meta/onboarding_quickstart.json`

建议把这套引导作为新会话首轮提示，帮助用户在 30 秒内完成首个任务。

## 能力结构（产品视角）

1. 通用层（行业标准）
- 文献简报
- PDF 简报
- PDF 表格提取
- 数据转换/画像/校验
- 报告合成与可复现导出

2. 专业层（生信深度）
- VCF 质检
- VCF 注释与简报
- 组学任务 kickoff 与可审计交付

这套结构保证了两件事：

- 普通科研用户一上来就能用（通用能力齐全）
- 生信团队能持续做深（专业能力不被通用层稀释）

## 文档

- 标准化量化评分卡：`docs/MEDRIXCLAW_STANDARD_SCORECARD_2026-03-31.md`
- 竞品对标：`COMPETITOR_MATRIX.md`
- 第三方声明：`THIRD_PARTY_NOTICES.md`

## 备注

仓库中已有部分历史前缀的内部目录与技能 ID，用于兼容现有运行时；对外产品名统一为 `MetrixClaw`。
