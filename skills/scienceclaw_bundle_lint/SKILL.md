---
name: scienceclaw_bundle_lint
description: Lint an existing ScienceClaw run bundle for required artifacts, structure, and minimum quality checks. Use when gating selfcheck, CI, release, or delivery acceptance for a runDir.
---

# ScienceClaw：产物包校验（Bundle Lint）（Governance）

## 目的 / 适用场景（when-to-use）

对一个已存在的 ScienceClaw `runDir` 做“产物包完整性 + 最小质量门槛”校验，输出可复盘的 lint 报告。

适用场景：

- CI / release gate：升级技能包前后跑一次，确保主链路产物齐全。
- selfcheck：保证 `brief/evidence/citations` 不空、JSON 合法、结构稳定。
- 交付前：把“能跑”升级为“可验收”。

本技能不依赖 LLM；支持离线运行。

## 输入

- `--run-dir <path>`（必填）：目标 run bundle 目录（包含 `manifest.json`、`artifacts/`、`logs/`）。
- `--profile <name>`（可选）：期望的产物配置。
  - `auto`（默认）：根据 `manifest.task` 自动推断
  - `lit_brief` / `pdf_brief` / `table_to_csv` / `omics_kickoff` / `any`
- `--strict`：严格模式（发现错误则退出非 0；默认只产出报告并返回 0）
- `--no-llm`：标准参数（本技能本身不调用 LLM）

## 输出（写回同一个 runDir）

- `artifacts/bundle_lint.json`：`{ ok, profile, errors[], warnings[], stats{} }`
- `logs/bundle_lint.log`

## 运行命令

```bash
python3 run.py --run-dir /abs/path/to/runDir --strict --profile auto --no-llm
```

## 冒烟测试（< 60s）

说明：对任意一个已存在的 runDir 做 lint。若你没有现成 runDir，可先运行 selfcheck 生成。

```bash
python3 run.py --run-dir /abs/path/to/runDir --profile any --no-llm
```

## 依赖

- Python 3（标准库）

## 安全约束

- 不访问网络；不启动对外服务
- 只写入目标 runDir 的 `artifacts/` 与 `logs/`（通过 `--run-dir` attach）
