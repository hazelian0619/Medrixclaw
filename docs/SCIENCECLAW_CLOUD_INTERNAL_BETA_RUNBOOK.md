# ScienceClaw Cloud Internal Beta Runbook

目的：把当前 `scienceclaw/skills/` 快速同步到云端 OpenClaw workspace，并用最少步骤完成内测前验收。

适用场景：

- 开始内测前的正式上传
- 云端热修（hotfix）
- 需要快速回滚到上一个版本

本文不讨论飞书接入实现本身，只覆盖 skills 包的上传、云端验证、以及云端临时修改方法。

## 1. 当前默认路径

本地仓库：

- `/Users/pluviophile/medexiclaw01/scienceclaw`

云端 OpenClaw workspace：

- `/root/.openclaw/workspace`

云端 skills 目录：

- `/root/.openclaw/workspace/skills`

## 2. 推荐上传方式（本地推云）

优先使用现成脚本：

```bash
cd /Users/pluviophile/medexiclaw01/scienceclaw/scripts
SCIENCECLAW_HOST=root@124.70.163.130 ./deploy_to_huawei.sh
```

说明：

- 脚本会把本地 `scienceclaw/skills/` 同步到云端 `~/.openclaw/workspace/skills/`
- 同步前会自动备份已有 `scienceclaw_*` 目录
- 同步完成后会自动运行一次 `scienceclaw_selfcheck`

可选环境变量：

```bash
SCIENCECLAW_HOST=root@124.70.163.130
SCIENCECLAW_IDENTITY=$HOME/.ssh/id_ed25519
SCIENCECLAW_REMOTE_WORKSPACE=/root/.openclaw/workspace
```

## 3. 上传后必须执行的云端验收

### 3.1 安装/依赖检查

```bash
bash /root/.openclaw/workspace/skills/scienceclaw_installer/run.sh
```

### 3.2 Phase 2 主验收

```bash
bash /root/.openclaw/workspace/skills/scienceclaw_meta/phase2_acceptance_vm.sh
```

这一步会验证：

- installer + selfcheck
- 基础 skills 离线 smoke
- `scienceclaw_workflow_pdf_brief`
- `scienceclaw_workflow_table_to_csv`
- `repro_export + report_compose_md + bundle_lint`

### 3.3 Phase 3 验收（如需）

```bash
bash /root/.openclaw/workspace/skills/scienceclaw_meta/phase3_acceptance_vm.sh
```

或全量：

```bash
bash /root/.openclaw/workspace/skills/scienceclaw_meta/phase_all_acceptance_vm.sh
```

## 4. 内测前建议检查项

### 4.1 pack 元信息

```bash
cat /root/.openclaw/workspace/skills/scienceclaw_meta/pack.json
```

当前应该看到的关键字段：

- `packVersion`
- `primaryEntry`
- `primaryWorkflow`
- `employeeVisible`
- `internalOnly`

### 4.2 自检

```bash
python3 /root/.openclaw/workspace/skills/scienceclaw_selfcheck/run.py
```

无网环境可用：

```bash
python3 /root/.openclaw/workspace/skills/scienceclaw_selfcheck/run.py --offline
```

### 4.3 总入口 smoke

```bash
python3 /root/.openclaw/workspace/skills/scienceclaw_orchestrator/run.py \
  --query "openclaw glm-5" \
  --limit 3 \
  --project beta \
  --no-llm \
  --no-pdf
```

### 4.4 PDF workflow smoke

```bash
python3 - <<'PY'
import fitz
from pathlib import Path
p=Path("/tmp/scienceclaw_beta_smoke.pdf")
d=fitz.open()
pg=d.new_page()
pg.insert_text((72,72), "INTRODUCTION\nHello.\n\nRESULTS\nA B\n1 2\n")
d.save(p)
print(p)
PY

python3 /root/.openclaw/workspace/skills/scienceclaw_orchestrator/run.py \
  --pdf /tmp/scienceclaw_beta_smoke.pdf \
  --project beta \
  --no-llm
```

## 5. 云端热修（Hotfix）方式

如果只是临时修改 1-2 个文件，有两种方式。

### 5.1 推荐：本地改完再重跑 deploy

优点：

- 不会出现本地/云端分叉
- 备份和回滚路径清楚

命令：

```bash
cd /Users/pluviophile/medexiclaw01/scienceclaw/scripts
SCIENCECLAW_HOST=root@124.70.163.130 ./deploy_to_huawei.sh
```

### 5.2 临时：直接在云上修改

只建议用于非常小的热修。

登录：

```bash
ssh root@124.70.163.130
cd /root/.openclaw/workspace/skills
```

例如修改某个 skill：

```bash
cd /root/.openclaw/workspace/skills/scienceclaw_orchestrator
vi run.py
```

修改后立刻验证：

```bash
python3 /root/.openclaw/workspace/skills/scienceclaw_pack_validate/run.py --strict --no-llm
python3 /root/.openclaw/workspace/skills/scienceclaw_selfcheck/run.py --offline
```

重要规则：

- 云上热修后，必须尽快把同样修改同步回本地仓库
- 否则下一次本地 deploy 会覆盖掉云端 hotfix

## 6. 回滚

上传脚本会自动把旧版本备份到：

- `/root/.openclaw/workspace/skills/.scienceclaw-backups/<timestamp>/`

查看备份：

```bash
ssh root@124.70.163.130 "ls -1 /root/.openclaw/workspace/skills/.scienceclaw-backups | tail -n 5"
```

回滚示例：

```bash
ssh root@124.70.163.130 "TS=<timestamp> bash -lc 'cd /root/.openclaw/workspace/skills && cp -a .scienceclaw-backups/${TS}/scienceclaw_* .'"
```

若需要恢复 `literature_pubmed_search` / `pdf_extract_basic` / `vendor_openclaw_scientific_skill`，同理手动 `cp -a` 回来。

## 7. 给飞书/OpenClaw 侧的同步原则

如果你们的飞书机器人已经绑定到同一套 OpenClaw workspace，那么：

- 先更新云端 `skills/`
- 再跑 installer/selfcheck/acceptance
- 最后在飞书侧只开放 `employeeVisible` 里的能力分层

建议前台分组：

- 入口：`scienceclaw_orchestrator`
- 工作流：来自 `employeeVisible.workflow`
- 通用工具：来自 `employeeVisible.generalTools`
- 专业工具：来自 `employeeVisible.professionalTools`

不要在飞书侧直接暴露：

- `internalOnly.governance`
- `internalOnly.vendor`

## 8. 今天可直接执行的最短路径

1. 本地推云：

```bash
cd /Users/pluviophile/medexiclaw01/scienceclaw/scripts
SCIENCECLAW_HOST=root@124.70.163.130 ./deploy_to_huawei.sh
```

2. 云端验收：

```bash
bash /root/.openclaw/workspace/skills/scienceclaw_installer/run.sh
bash /root/.openclaw/workspace/skills/scienceclaw_meta/phase2_acceptance_vm.sh
```

3. 检查 pack 元信息：

```bash
cat /root/.openclaw/workspace/skills/scienceclaw_meta/pack.json
```

4. 在 OpenClaw/飞书侧只上架：

- `primaryEntry`
- `employeeVisible.workflow`
- `employeeVisible.generalTools`
- `employeeVisible.professionalTools`

一句话执行策略：

**先把 catalog 元信息和 skills 包一起推云，先开内测，再利用内测时间继续补专用 skill 和 vendor 封装。**
