---
name: scienceclaw_lit_pdf_fetch_pmc
description: Resolve a PMCID or PMID to a best-effort PMC PDF download and store the file inside a run bundle. Use in literature workflows when local PDF acquisition from PMC is needed.
---

# 文献：从 PMC 获取 PDF（PMCID/PMID）（MVP）

目的：给定 PMCID（或 PMID），从 PMC 站点 best-effort 获取 PDF 并落盘到产物包。

## 输入

- `--pmcid`（可选，可重复）：一个或多个 PMCID（形如 `PMC1234567`）
- `--pmid`（可选，可重复）：一个或多个 PMID（会尝试解析到 PMCID）
- `--project`（可选）：默认 `default`

示例：

```bash
python3 run.py --pmid 38239341 --project demo
```

## 输出（产物包）

在 `$OPENCLAW_WORKSPACE/projects/<project>/runs/<runId>/` 下生成：

- `manifest.json`
- `artifacts/*.pdf`（成功时）
- `artifacts/downloads.json`（每条记录包含 pmid/pmcid/url/ok/error）
- `logs/`

## 常见报错（1 行修复）

- 文章不在 PMC / 无 PDF：
  修复：换一篇带 PMCID 的文章，或走 DOI/出版社路径（后续版本补齐）

- `blocked_by_pmc_pow (requires browser)`：
  说明：PMC 对自动化 PDF 下载加了浏览器侧挑战（POW/JS），脚本无法直接下载。
  修复：让用户手动下载 PDF 并走本地 PDF 输入路径（workflow 支持 `--pdf /path/to/file.pdf`）

## 冒烟测试（< 60s）

说明：本技能是 best-effort。即便下载失败，也应生成 `artifacts/downloads.json` 供复盘。

```bash
python3 run.py --pmid 38239341 --project selfcheck --no-llm
```
