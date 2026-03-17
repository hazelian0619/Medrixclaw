---
name: scienceclaw_workflow_vcf_annotate_brief
description: Annotate a local VCF and generate a brief, evidence, citations, and reproducibility outputs. Use when the user wants a variant-level analysis bundle from a VCF file.
---

# ScienceClaw：VCF 注释与简报工作流（VCF Annotate Brief）（L4 Workflow）

## 目的 / 适用场景（when-to-use）

Phase 3 主线 Domain Pack：给定本地 VCF，一条命令产出可交付的 run bundle：

- `variants.annotated.tsv/json`
- `brief.md`
- `evidence.json`（非空）
- `citations.bib`（非空）
- `report.md`（交付汇总）
- `reproducibility/`（commands/checksums/environment）
- `bundle_lint.json`（严格 gate）

离线 baseline：不依赖外网即可跑完并交付。

## 输入

- `--vcf <path>`（必填）
- `--project <slug>`（可选）
- `--workspace <path>`（可选）
- `--no-llm`（可选）

## 输出

打印本次 `runDir`（最后一行），runDir 内含上述 artifacts。

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

python3 run.py --vcf /tmp/scienceclaw_vcf_smoke.vcf --project selfcheck --no-llm
```
