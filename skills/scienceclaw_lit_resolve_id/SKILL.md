---
name: scienceclaw_lit_resolve_id
description: Resolve and normalize literature identifiers such as PMID to PMCID mappings for downstream retrieval workflows. Use before PDF fetch or literature workflows when identifier normalization is required.
---

# 文献：ID 解析与规范化（PMID/PMCID）（MVP）

目的：把用户给出的 PMID 转成 PMCID（如果存在），并产出结构化映射结果，供后续 `PDF 获取` 或 workflow 使用。

## 输入

- `--pmid`（必填，可重复）：一个或多个 PMID
- `--project`（可选）：默认 `default`

示例：

```bash
python3 run.py --pmid 37566049 --pmid 38239341 --project demo
```

## 输出（产物包）

在 `$OPENCLAW_WORKSPACE/projects/<project>/runs/<runId>/` 下生成：

- `manifest.json`
- `artifacts/id_map.json`：形如 `{ "pmid": "...", "pmcid": "PMC..." }`
- `logs/`

## 常见报错（1 行修复）

- 网络/DNS 异常导致无法访问 NCBI：
  修复：检查服务器 DNS/出网，稍后重试

## 冒烟测试（< 60s）

说明：本技能依赖 NCBI E-utilities，需可访问外网。

```bash
python3 run.py --pmid 38239341 --project selfcheck --no-llm
```
