---
name: scienceclaw_pack_validate
description: Validate the ScienceClaw pack allowlist and skill directory layout in the current workspace. Use when checking whether an installed skill pack is complete and discoverable before deployment or upgrade.
---

# ScienceClaw：技能包校验（Pack Validate）（L5 Governance）

## 目的 / 适用场景（when-to-use）

对当前 workspace 的 `scienceclaw_meta/pack.json`（allowlist + 版本）做一致性校验：

- allowlist 中的 skill 目录是否存在
- 每个 skill 是否至少包含 `SKILL.md`
- 每个 skill 是否有可执行入口（`run.py` 或 `run.sh`，或明确的 vendored 目录）

用于安装后自检、升级 gate、CI gate。

本技能不依赖 LLM；离线可跑。

## 输入

- `--workspace <path>`：OpenClaw workspace（默认 `$OPENCLAW_WORKSPACE` 或 `~/.openclaw/workspace`）
- `--strict`：严格模式（发现错误即返回非 0）
- `--no-llm`：标准参数（本技能不调用 LLM）

## 输出（产物包）

- `artifacts/pack_validate.json`：`{ ok, packVersion, errors[], warnings[] }`
- `logs/pack_validate.log`

## 运行命令

```bash
python3 run.py --strict --no-llm
```

## 冒烟测试（< 60s）

```bash
python3 run.py --strict --no-llm
```
