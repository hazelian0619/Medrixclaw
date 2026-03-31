#!/usr/bin/env bash
set -euo pipefail

# Install only baseline mandatory skills into an OpenClaw workspace.
#
# Usage:
#   ./install_mandatory_skills_to_workspace.sh --workspace /root/.openclaw/workspace
#   ./install_mandatory_skills_to_workspace.sh --workspace /root/.openclaw/workspace --clean

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_SKILLS="${ROOT_DIR}/skills"
META_DIR="${SRC_SKILLS}/metrixclaw_meta"
MANDATORY_JSON="${META_DIR}/mandatory_skills.json"

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
CLEAN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)
      WORKSPACE="$2"
      shift 2
      ;;
    --clean)
      CLEAN=1
      shift
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

DEST_SKILLS="${WORKSPACE}/skills"
mkdir -p "${DEST_SKILLS}"

mapfile -t MANDATORY < <(python3 - <<'PY' "${MANDATORY_JSON}"
import json, sys
p = sys.argv[1]
cfg = json.load(open(p))
for s in cfg.get("mandatory_skills", []):
    print(s)
PY
)

if [[ "${CLEAN}" -eq 1 ]]; then
  echo "[install] --clean enabled, removing destination copies of mandatory skills first"
  for s in "${MANDATORY[@]}"; do
    rm -rf "${DEST_SKILLS}/${s}"
  done
fi

echo "[install] workspace=${WORKSPACE}"
echo "[install] mandatory_count=${#MANDATORY[@]}"

for s in "${MANDATORY[@]}"; do
  if [[ ! -d "${SRC_SKILLS}/${s}" ]]; then
    echo "[install] WARN missing in repo: ${s}"
    continue
  fi
  rm -rf "${DEST_SKILLS}/${s}"
  cp -a "${SRC_SKILLS}/${s}" "${DEST_SKILLS}/${s}"
  echo "[install] copied ${s}"
done

echo "[install] verifying mandatory skills"
python3 "${META_DIR}/verify_mandatory_skills.py" --workspace "${WORKSPACE}" --strict

echo "[install] done"
