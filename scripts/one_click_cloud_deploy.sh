#!/usr/bin/env bash
set -euo pipefail

# One-click deploy for backend integration:
# 1) Deploy skills to VM
# 2) Install/repair dependencies
# 3) Verify mandatory skills
# 4) Run acceptance scripts
#
# Usage:
#   SCIENCECLAW_HOST=root@1.2.3.4 ./one_click_cloud_deploy.sh
#   SCIENCECLAW_HOST=root@1.2.3.4 ./one_click_cloud_deploy.sh --phase all

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_SCRIPT="${ROOT_DIR}/scripts/deploy_to_huawei.sh"

HOST="${SCIENCECLAW_HOST:-root@124.70.163.130}"
REMOTE_WORKSPACE="${SCIENCECLAW_REMOTE_WORKSPACE:-/root/.openclaw/workspace}"
IDENTITY="${SCIENCECLAW_IDENTITY:-$HOME/.ssh/id_ed25519}"
SSH_PORT="${SCIENCECLAW_SSH_PORT:-22}"
IDENTITY_REQUIRED=0
if [[ -n "${SCIENCECLAW_IDENTITY:-}" ]]; then
  IDENTITY_REQUIRED=1
fi
PHASE="2" # 2 | 3 | all | none
SKIP_DEPLOY=0
SUMMARY_DIR="${ROOT_DIR}/projects/deploy_reports"
mkdir -p "${SUMMARY_DIR}"
TS="$(date -u +"%Y%m%d_%H%M%S")"
SUMMARY_JSON="${SUMMARY_DIR}/deploy_${TS}.json"
SSH_OPTS=()

build_ssh_opts() {
  SSH_OPTS=(
    -p "${SSH_PORT}"
    -o StrictHostKeyChecking=accept-new
    -o ConnectTimeout=10
    -o ConnectionAttempts=3
    -o ServerAliveInterval=15
    -o ServerAliveCountMax=3
  )
  if [[ -f "${IDENTITY}" ]]; then
    SSH_OPTS=(-i "${IDENTITY}" "${SSH_OPTS[@]}")
  elif [[ "${IDENTITY_REQUIRED}" -eq 1 ]]; then
    echo "identity file not found: ${IDENTITY}" >&2
    exit 2
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      HOST="$2"
      shift 2
      ;;
    --workspace)
      REMOTE_WORKSPACE="$2"
      shift 2
      ;;
    --identity)
      IDENTITY="$2"
      IDENTITY_REQUIRED=1
      shift 2
      ;;
    --ssh-port)
      SSH_PORT="$2"
      shift 2
      ;;
    --phase)
      PHASE="$2"
      shift 2
      ;;
    --skip-deploy)
      SKIP_DEPLOY=1
      shift
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

build_ssh_opts

run_remote() {
  local cmd="$1"
  ssh "${SSH_OPTS[@]}" "${HOST}" bash -lc "${cmd}"
}

log_step() {
  local key="$1"
  local status="$2"
  local detail="$3"
  python3 - <<'PY' "${SUMMARY_JSON}" "${key}" "${status}" "${detail}" "${HOST}" "${REMOTE_WORKSPACE}" "${TS}"
import json, sys, pathlib
path = pathlib.Path(sys.argv[1])
key, status, detail = sys.argv[2], sys.argv[3], sys.argv[4]
host, ws, ts = sys.argv[5], sys.argv[6], sys.argv[7]
if path.exists():
    obj = json.load(open(path))
else:
    obj = {"schemaVersion": 1, "timestamp": ts, "host": host, "workspace": ws, "steps": {}}
obj["steps"][key] = {"status": status, "detail": detail}
json.dump(obj, open(path, "w"), indent=2)
PY
}

echo "[one-click] host=${HOST}"
echo "[one-click] workspace=${REMOTE_WORKSPACE}"
echo "[one-click] phase=${PHASE}"
echo "[one-click] ssh_port=${SSH_PORT}"
echo "[one-click] identity=${IDENTITY}"
echo "[one-click] summary=${SUMMARY_JSON}"

if [[ "${SKIP_DEPLOY}" -eq 0 ]]; then
  DEPLOY_ENV=(
    "SCIENCECLAW_HOST=${HOST}"
    "SCIENCECLAW_REMOTE_WORKSPACE=${REMOTE_WORKSPACE}"
  )
  if [[ -f "${IDENTITY}" ]]; then
    DEPLOY_ENV+=("SCIENCECLAW_IDENTITY=${IDENTITY}")
  fi
  if env "${DEPLOY_ENV[@]}" "${DEPLOY_SCRIPT}"; then
    log_step "deploy" "ok" "skills synced"
  else
    log_step "deploy" "fail" "deploy_to_huawei.sh failed"
    exit 10
  fi
else
  log_step "deploy" "skip" "--skip-deploy set"
fi

if run_remote "[[ -x \"${REMOTE_WORKSPACE}/skills/scienceclaw_installer/run.sh\" ]]"; then
  log_step "precheck_installer" "ok" "installer script found"
else
  log_step "precheck_installer" "fail" "missing installer script on remote"
  exit 21
fi

if run_remote "[[ -f \"${REMOTE_WORKSPACE}/skills/scienceclaw_meta/verify_mandatory_skills.py\" ]]"; then
  log_step "precheck_mandatory_verify" "ok" "verify_mandatory_skills.py found"
else
  log_step "precheck_mandatory_verify" "fail" "missing verify_mandatory_skills.py on remote"
  exit 22
fi

if run_remote "bash \"${REMOTE_WORKSPACE}/skills/scienceclaw_installer/run.sh\""; then
  log_step "installer" "ok" "scienceclaw_installer run.sh passed"
else
  log_step "installer" "fail" "installer failed"
  exit 11
fi

if run_remote "python3 \"${REMOTE_WORKSPACE}/skills/scienceclaw_meta/verify_mandatory_skills.py\" --workspace \"${REMOTE_WORKSPACE}\" --strict"; then
  log_step "mandatory_verify" "ok" "mandatory skills verified"
else
  log_step "mandatory_verify" "fail" "mandatory skills verification failed"
  exit 12
fi

case "${PHASE}" in
  2)
    if run_remote "bash \"${REMOTE_WORKSPACE}/skills/scienceclaw_meta/phase2_acceptance_vm.sh\""; then
      log_step "acceptance_phase2" "ok" "phase2 passed"
    else
      log_step "acceptance_phase2" "fail" "phase2 failed"
      exit 13
    fi
    ;;
  3)
    if run_remote "bash \"${REMOTE_WORKSPACE}/skills/scienceclaw_meta/phase3_acceptance_vm.sh\""; then
      log_step "acceptance_phase3" "ok" "phase3 passed"
    else
      log_step "acceptance_phase3" "fail" "phase3 failed"
      exit 14
    fi
    ;;
  all)
    if run_remote "bash \"${REMOTE_WORKSPACE}/skills/scienceclaw_meta/phase_all_acceptance_vm.sh\""; then
      log_step "acceptance_all" "ok" "phase all passed"
    else
      log_step "acceptance_all" "fail" "phase all failed"
      exit 15
    fi
    ;;
  none)
    log_step "acceptance" "skip" "phase=none"
    ;;
  *)
    log_step "acceptance" "fail" "invalid --phase value"
    echo "Invalid --phase: ${PHASE}" >&2
    exit 2
    ;;
esac

echo "[one-click] success"
echo "[one-click] summary: ${SUMMARY_JSON}"
