#!/usr/bin/env bash
set -euo pipefail

# Phase 2 acceptance script (run on the VM).
#
# Goal: produce concrete runDirs as delivery evidence:
# - installer -> selfcheck
# - pdf brief (offline baseline)
# - table to csv (offline baseline)
#
# Assumptions:
# - ScienceClaw skills are deployed into: $OPENCLAW_WORKSPACE/skills/
# - python3 is available
#
# Usage:
#   bash /root/.openclaw/workspace/skills/scienceclaw_meta/phase2_acceptance_vm.sh
#
# Optional env:
#   OPENCLAW_WORKSPACE=/root/.openclaw/workspace

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SKILLS_DIR="${WORKSPACE}/skills"

echo "[phase2] workspace=${WORKSPACE}"
echo "[phase2] skills=${SKILLS_DIR}"

if [[ ! -d "${SKILLS_DIR}" ]]; then
  echo "ERROR: skills dir not found: ${SKILLS_DIR}" >&2
  exit 2
fi

for req in scienceclaw_installer scienceclaw_selfcheck scienceclaw_workflow_pdf_brief scienceclaw_workflow_table_to_csv scienceclaw_bundle_lint; do
  if [[ ! -d "${SKILLS_DIR}/${req}" ]]; then
    echo "ERROR: required skill not found in workspace: ${req}" >&2
    exit 2
  fi
done

echo "[phase2] 1) installer (includes selfcheck)"
bash "${SKILLS_DIR}/scienceclaw_installer/run.sh" | tail -n 40

echo "[phase2] 1.5) base skills (office/data) offline smoke"
python3 - <<'PY'
import json
from pathlib import Path
import os, sys, subprocess, tempfile

ws = Path(os.environ.get("OPENCLAW_WORKSPACE", str(Path.home()/".openclaw"/"workspace")))
skills = ws / "skills"

csvp = Path("/tmp/scienceclaw_base_smoke.csv")
csvp.write_text("a,b\n1,2\n,3\n4,\n", encoding="utf-8")

def run_skill(name, argv):
    p = skills / name / "run.py"
    if not p.exists():
        raise SystemExit(f"missing skill: {name} at {p}")
    out = subprocess.check_output([sys.executable, str(p)] + argv, text=True).strip().splitlines()[-1]
    print(f"[base] {name} runDir: {out}")
    return out

# fs_ingest: ingest this repo's pack.json as a file input
pack = skills / "scienceclaw_meta" / "pack.json"
run_skill("scienceclaw_fs_ingest", ["--path", str(pack), "--project", "acceptance", "--no-llm"])

# http_fetch: offline plan
run_skill("scienceclaw_http_fetch", ["--url", "https://example.com/a.txt", "--offline", "--project", "acceptance", "--no-llm"])

# format_convert + data_profile
run_skill("scienceclaw_format_convert", ["--input", str(csvp), "--mode", "csv_to_json", "--project", "acceptance", "--no-llm"])
run_skill("scienceclaw_data_profile", ["--input", str(csvp), "--project", "acceptance", "--no-llm"])
PY

echo "[phase2] 2) build a tiny PDF for deterministic offline workflows"
python3 - <<'PY'
import fitz
from pathlib import Path
p=Path("/tmp/scienceclaw_phase2_smoke.pdf")
d=fitz.open()
pg=d.new_page()
pg.insert_text((72,72), "INTRODUCTION\nWe studied X.\n\nMETHODS\nWe did Y.\n\nRESULTS\nWe observed Z.\n\nTABLE 1\nA  B\n1  2\n3  4\n")
d.save(p)
print(str(p))
PY

echo "[phase2] 3) workflow_pdf_brief (no LLM)"
PDF_RUN_DIR="$(python3 "${SKILLS_DIR}/scienceclaw_workflow_pdf_brief/run.py" --project acceptance --pdf /tmp/scienceclaw_phase2_smoke.pdf --no-llm | tail -n 1)"
echo "pdf_brief runDir: ${PDF_RUN_DIR}"

echo "[phase2] 3.1) repro export + delivery report (pdf_brief)"
python3 "${SKILLS_DIR}/scienceclaw_repro_export/run.py" --run-dir "${PDF_RUN_DIR}" --pip-freeze --no-llm | tail -n 1
python3 "${SKILLS_DIR}/scienceclaw_report_compose_md/run.py" --run-dir "${PDF_RUN_DIR}" --title "Phase2 Acceptance: PDF Brief" --no-llm | tail -n 1
echo "[phase2] 3.2) strict lint gate (pdf_brief)"
python3 "${SKILLS_DIR}/scienceclaw_bundle_lint/run.py" --run-dir "${PDF_RUN_DIR}" --profile auto --strict --no-llm | tail -n 1

echo "[phase2] 4) workflow_table_to_csv (no LLM)"
TABLE_RUN_DIR="$(python3 "${SKILLS_DIR}/scienceclaw_workflow_table_to_csv/run.py" --project acceptance --pdf /tmp/scienceclaw_phase2_smoke.pdf --no-llm | tail -n 1)"
echo "table_to_csv runDir: ${TABLE_RUN_DIR}"

echo "[phase2] 4.1) repro export + delivery report (table_to_csv)"
python3 "${SKILLS_DIR}/scienceclaw_repro_export/run.py" --run-dir "${TABLE_RUN_DIR}" --pip-freeze --no-llm | tail -n 1
python3 "${SKILLS_DIR}/scienceclaw_report_compose_md/run.py" --run-dir "${TABLE_RUN_DIR}" --title "Phase2 Acceptance: Table to CSV" --no-llm | tail -n 1
echo "[phase2] 4.2) strict lint gate (table_to_csv)"
python3 "${SKILLS_DIR}/scienceclaw_bundle_lint/run.py" --run-dir "${TABLE_RUN_DIR}" --profile auto --strict --no-llm | tail -n 1

echo "[phase2] done"
