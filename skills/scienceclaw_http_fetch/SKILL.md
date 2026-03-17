---
name: scienceclaw_http_fetch
description: Fetch approved URLs into the current run bundle with domain allowlisting, hashes, and HTTP metadata. Use when a workflow needs controlled external downloads or offline fetch planning.
---

# ScienceClaw：安全下载（HTTP Fetch）（Base）

## 目的 / 适用场景（when-to-use）

把给定 URL 下载到本次 run 的 `artifacts/downloads/` 下，并记录 hash、HTTP 状态与重定向信息，便于审计与复盘。

特点：

- 默认需要显式 allowlist（`--allow-domain`），避免“任意下载”成为供应链风险入口
- 提供 `--offline` 退化路径：只输出结构化下载计划，不执行网络请求
- 不依赖 LLM（`--no-llm` 仅作接口对齐）

## 输入

- `--url`（必填，可重复）：URL
- `--allow-domain`（可选，可重复）：允许的域名（例如 `ncbi.nlm.nih.gov`）
- `--allow-all`：允许所有域名（不推荐；仅在受控环境下使用）
- `--offline`：离线退化（只产出 `fetch.plan.json`）
- `--project`（可选）：默认 `default`
- `--workspace`（可选）：默认 `$OPENCLAW_WORKSPACE` 或 `~/.openclaw/workspace`
- `--run-dir`（可选）：写入一个已有 runDir（由 workflow 创建）
- `--no-llm`：兼容统一接口；本技能不使用 LLM

## 输出（产物包）

- `manifest.json`
- `artifacts/fetch.plan.json`（offline 时必出）
- `artifacts/fetch.results.json`（online 时必出）
- `artifacts/downloads/<files...>`（online 成功时）
- `logs/fetch.log`

## 运行命令

```bash
python3 run.py --url "https://example.com/data.csv" --allow-domain example.com --project demo --no-llm
```

## 依赖

- Python 3（标准库 `urllib`）

## 失败模式（常见报错 + 1 行修复命令）

- `ERROR: domain not allowed`
  修复：添加 `--allow-domain <domain>`（或在受控环境下使用 `--allow-all`）

## 安全约束

- 不启动对外网络服务（不开端口）
- 下载输出仅写入 `artifacts/downloads/`

## Smoke Test（< 60s）

离线 smoke（不依赖网络）：

```bash
python3 run.py --url "https://example.com/a.txt" --offline --project selfcheck --no-llm
```
