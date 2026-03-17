# 文献：PubMed 检索（MVP）

通过 NCBI E-utilities 检索 PubMed，并产出：

- `results.json`：结构化论文列表（PMID、标题、作者、期刊、年份等）
- `citations.bib`：BibTeX（best-effort）
- `manifest.json`：证据与复盘记录（provenance：query、limit、时间戳、hash 等）

## 输入参数

- `--query`（必填）：用户的检索 query
- `--limit`（可选）：默认 10
- `--project`（可选）：默认 `default`

## 运行命令

在 OpenClaw 的工具 shell 或服务器终端执行：

```bash
python3 run.py --query "single-cell RNA-seq differential expression" --limit 10 --project demo
```

## 预期输出

会在以下目录创建新的 run 包：
`$OPENCLAW_WORKSPACE/projects/<project>/runs/<runId>/...`

Artifacts：

- `artifacts/results.json`
- `artifacts/citations.bib`

## 常见报错（1 行修复）

- `ModuleNotFoundError: requests`
  修复：`python3 -m pip install --user requests`

- HTTP 429 / 限流
  修复：`sleep 5` 后重试，或调小 `--limit`

## 冒烟测试（< 60s）

说明：本技能依赖 NCBI E-utilities，需可访问外网。

```bash
python3 run.py --query "openclaw glm-5" --limit 1 --project selfcheck --no-llm
```
