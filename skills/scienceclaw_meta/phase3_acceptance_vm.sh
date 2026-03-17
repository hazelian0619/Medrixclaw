#!/usr/bin/env bash
set -euo pipefail

# Phase 3 acceptance script (run on the VM).
#
# Goal: run the Phase 3 Domain Pack (VCF annotate + brief) end-to-end,
# producing a concrete runDir with L5 gates applied (normalize/report/repro/lint).
#
# Usage:
#   bash /root/.openclaw/workspace/skills/scienceclaw_meta/phase3_acceptance_vm.sh
#
# Optional env:
#   OPENCLAW_WORKSPACE=/root/.openclaw/workspace

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SKILLS_DIR="${WORKSPACE}/skills"

echo "[phase3] workspace=${WORKSPACE}"
echo "[phase3] skills=${SKILLS_DIR}"

for req in scienceclaw_workflow_vcf_annotate_brief scienceclaw_bio_vcf_validate scienceclaw_bio_vcf_annotate scienceclaw_bundle_lint; do
  if [[ ! -d "${SKILLS_DIR}/${req}" ]]; then
    echo "ERROR: required skill not found in workspace: ${req}" >&2
    exit 2
  fi
done

echo "[phase3] 1) build a tiny VCF for deterministic offline workflow"
cat > /tmp/scienceclaw_phase3_smoke.vcf <<'VCF'
##fileformat=VCFv4.2
##source=scienceclaw_phase3_acceptance
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
1	100	.	A	G	.	PASS	AC=1;AN=2
1	150	rs1	C	T	.	PASS	AC=2;AN=2
2	999	.	G	A,C	.	PASS	AC=1;AN=2
VCF
echo "/tmp/scienceclaw_phase3_smoke.vcf"

echo "[phase3] 2) workflow_vcf_annotate_brief (no LLM)"
RUN_DIR="$(python3 "${SKILLS_DIR}/scienceclaw_workflow_vcf_annotate_brief/run.py" --project acceptance --vcf /tmp/scienceclaw_phase3_smoke.vcf --no-llm --workspace "${WORKSPACE}" | tail -n 1)"
echo "vcf_annotate_brief runDir: ${RUN_DIR}"

echo "[phase3] 3) strict lint gate (should be ok)"
python3 "${SKILLS_DIR}/scienceclaw_bundle_lint/run.py" --run-dir "${RUN_DIR}" --profile auto --strict --no-llm | tail -n 1

echo "[phase3] done"

