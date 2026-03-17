---
name: scienceclaw_citation_normalize
description: Normalize, deduplicate, and export citations and evidence records from ScienceClaw results into reproducible citation files. Use at the governance or workflow tail when a bundle needs clean references.
---

# ScienceClaw：引用与证据链规范化（citations/evidence normalize）

目的：把 `results.json` 或 `evidence.json` 中的来源信息（PMID/DOI/本地文件）规范化、去重，并导出可复盘的引用文件（`citations.bib`，可选 `citations.ris`）。

本技能不依赖 LLM；`--no-llm` 仅用于对齐统一接口与审计字段（输出一致的结构化中间产物）。

## 输入

二选一（至少提供一个）：

- `--results-json <path>`：workflow 的检索结果（建议包含 `items[*].pmid/title/authors/year/journal`）
- `--evidence-json <path>`：证据片段列表（`EvidenceItem[]`；见 `SCIENCECLAW_V1_ARTIFACT_SPEC.md`）

其他参数：

- `--project <slug>`：默认 `default`
- `--workspace <path>`：默认 `$OPENCLAW_WORKSPACE` 或 `~/.openclaw/workspace`
- `--run-dir <path>`：把输出写回已有 run 包目录（workflow 就地治理；不再新建 runDir）
- `--ris`：同时输出 `artifacts/citations.ris`
- `--no-llm`：离线/自检模式（行为同默认；保证结构化产物齐全）

示例：

```bash
python3 run.py --evidence-json /path/to/evidence.json --project demo --ris --no-llm
```

### Workflow 就地治理（推荐）

如果你在 workflow 中已经生成了 runDir（包含 `manifest.json + artifacts/ + logs/`），建议使用 `--run-dir` 把规范化产物写回同一个包，避免产生第二个 run 包：

```bash
python3 run.py \
  --run-dir /path/to/projects/<project>/runs/<runId> \
  --evidence-json /path/to/projects/<project>/runs/<runId>/artifacts/evidence.json \
  --no-llm
```

## 输出（产物包）

在 `$OPENCLAW_WORKSPACE/projects/<project>/runs/<runId>/` 下生成：

- `manifest.json`
- `artifacts/citations.bib`：去重、按 key 排序的 BibTeX（至少包含 PMID-only entries）
- `artifacts/citations.normalized.json`：结构化中间产物（规范化后的来源列表、去重统计、输入指纹）
- `artifacts/evidence.deduped.json`：如果提供了 `--evidence-json`，输出去重后的 evidence 列表
- `artifacts/citations.ris`（可选）
- `logs/normalize.log`

## 去重规则（核心）

- Evidence 去重：`source_canonical + locator_canonical + quote_hash`。
- Citation 去重：按 `source_canonical`（例如 `PMID:38239341` / `DOI:10.xxxx/...` / `file:/abs/path.pdf`）。

## 常见报错（1 行修复）

- `json.decoder.JSONDecodeError`
  修复：确认输入文件是合法 JSON（不是 Markdown 或被截断的文本）。

- `FileNotFoundError`
  修复：确认 `--results-json/--evidence-json` 路径存在且为绝对路径（推荐）。

## 冒烟测试（< 60s）

```bash
python3 run.py --evidence-json <(printf '[{\"source\":\"PMID:123\",\"locator\":\"abstract\",\"quote\":\"hello\",\"usedIn\":[\"summary\"]}]') --project selfcheck --no-llm
```
