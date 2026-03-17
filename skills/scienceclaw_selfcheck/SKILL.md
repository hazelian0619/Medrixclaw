---
name: scienceclaw_selfcheck
description: Run the ScienceClaw offline selfcheck workflow and report the runDir, success status, and generated artifacts. Use when validating deployment, installation, or minimum deliverable bundle generation.
---

# ScienceClaw：自检（Selfcheck）

目的：用一条命令验证 ScienceClaw 的 v1 主闭环是否可跑，并确认产物包规范是否满足最低要求。

## 运行命令（服务器上）

```bash
python3 run.py
```

离线模式（不访问外网，直接生成可审计的最小产物包）：

```bash
python3 run.py --offline
```

## 通过标准

- 输出一个 run 目录路径
- 该目录下存在：
  - `manifest.json`
  - `artifacts/brief.md`
  - `artifacts/citations.bib`
  - `artifacts/evidence.json`
  - `logs/`

## 冒烟测试（< 60s）

离线模式（推荐，稳定）：

```bash
python3 run.py --offline
```
