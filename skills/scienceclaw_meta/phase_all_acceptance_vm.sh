#!/usr/bin/env bash
set -euo pipefail

# All-up acceptance script (Phase 2 + Phase 3) for VM delivery evidence.
#
# Usage:
#   bash /root/.openclaw/workspace/skills/scienceclaw_meta/phase_all_acceptance_vm.sh

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SKILLS_DIR="${WORKSPACE}/skills"

echo "[phase_all] workspace=${WORKSPACE}"
echo "[phase_all] skills=${SKILLS_DIR}"

if [[ ! -d "${SKILLS_DIR}/scienceclaw_meta" ]]; then
  echo "ERROR: scienceclaw_meta not found in workspace: ${SKILLS_DIR}" >&2
  exit 2
fi

echo "[phase_all] phase2 acceptance"
bash "${SKILLS_DIR}/scienceclaw_meta/phase2_acceptance_vm.sh" | tail -n 120

echo "[phase_all] phase3 acceptance"
bash "${SKILLS_DIR}/scienceclaw_meta/phase3_acceptance_vm.sh" | tail -n 120

echo "[phase_all] done"

