---
name: scienceclaw_repro_export
description: Export reproducibility files such as commands, checksums, and environment snapshots from a run bundle. Use when a run needs a reproducible handoff package or audit trail.
---

# ScienceClaw：可复现性导出（Repro Export）（Base）

## 目的 / 适用场景（when-to-use）

把一个 run 的 `manifest.json` 转成“可复现性 bundle”，对标 ClawBio 的交付习惯：

- `commands.sh`：复现命令列表（来自 manifest.commands）
- `checksums.sha256`：输入/输出文件的 SHA-256（来自 manifest.artifacts）
- `environment.txt`：环境快照（Python 版本 + pip freeze best-effort）
- `analysis_log.md`：可读的执行记录（时间戳 + argv）

适合：

- 在交付/评审时给出“无需 agent 也能复现”的证据包
- 在离线环境中验证产物包完整性与可追溯性

本技能不依赖 LLM；支持 `--no-llm` 与离线运行。

## 输入

二选一：

- `--run-dir <path>`：把 repro bundle 写入该 run 的 `artifacts/reproducibility/`（推荐，workflow 内部调用）
- 或不传 `--run-dir`：本技能会创建自己的 run bundle，并把 repro bundle 写入自己的 `artifacts/reproducibility/`

可选：

- `--source-run-dir <path>`：从另一个 runDir 读取 manifest（默认等于目标 runDir）
- `--pip-freeze`：尝试记录 `python -m pip freeze`（best-effort，失败不会中断）
- `--project/--workspace/--no-llm`：标准参数

## 输出（产物包）

在目标 runDir 下生成：

- `artifacts/reproducibility/commands.sh`
- `artifacts/reproducibility/checksums.sha256`
- `artifacts/reproducibility/environment.txt`
- `artifacts/reproducibility/analysis_log.md`
- `artifacts/reproducibility/repro.json`

并更新 `manifest.json` 记录这些 artifacts。

## 运行命令

```bash
python3 run.py --run-dir /path/to/runDir --pip-freeze --no-llm
```

## 依赖

- Python 3（标准库）

## 失败模式（常见报错 + 1 行修复命令）

- `manifest.json not found`
  修复：确认 `--run-dir/--source-run-dir` 指向有效 runDir

## 安全约束

- 不访问网络；不启动对外服务
- 只写入目标 runDir 的 `artifacts/` 与 `logs/`

## Smoke Test（< 60s）

```bash
python3 run.py --project selfcheck --no-llm
```
