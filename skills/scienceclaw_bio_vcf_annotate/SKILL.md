---
name: scienceclaw_bio_vcf_annotate
description: Annotate a local VCF file into structured TSV and JSON outputs and append provenance into the run bundle. Use when a workflow or operator needs deterministic offline-friendly VCF annotation artifacts for downstream review.
---

# ScienceClaw：VCF 注释与结构化导出（VCF Annotate）（L4 Atomic）

## 目的 / 适用场景（when-to-use）

把 VCF 变成可下游消费的结构化结果（TSV/JSON），并把关键 provenance 写入 run bundle（evidence + citations）。

说明：Phase 3 v1 的离线 baseline 不追求“全数据库注释正确性”，优先交付“稳定结构 + 可复盘”。在线/深度注释作为后续增强。

本技能不依赖 LLM；离线可跑。

## 输入

- `--vcf <path>`（必填）：VCF 文件（支持 `.vcf` / `.vcf.gz`）
- `--run-dir <path>`（可选）：写回已有 runDir（workflow 模式）
- `--limit <n>`（可选）：最多导出多少条变异（默认 5000；用于保护 TTFR）
- `--project/--workspace/--no-llm`：标准参数

## 输出（产物包）

- `artifacts/variants.annotated.tsv`
- `artifacts/variants.annotated.json`（array-of-objects）
- `artifacts/variants.summary.json`（统计摘要）
- `artifacts/evidence.json`（追加：指向输入 VCF 与样例变异行）
- `logs/vcf_annotate.log`

## 运行命令

```bash
python3 run.py --vcf /abs/path/sample.vcf --project demo --no-llm
```

## 冒烟测试（< 60s）

```bash
cat > /tmp/scienceclaw_vcf_smoke.vcf <<'VCF'
##fileformat=VCFv4.2
##contig=<ID=1,length=248956422>
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	SAMPLE
1	1000	.	A	G	.	PASS	.	GT	0/1
VCF

python3 run.py --vcf /tmp/scienceclaw_vcf_smoke.vcf --project selfcheck --no-llm --limit 100
```
