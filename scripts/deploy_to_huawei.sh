#!/usr/bin/env bash
set -euo pipefail

# Deploy ScienceClaw skills to a Huawei Cloud OpenClaw VM.
# This script is meant to run on the developer machine (Mac/Linux).
#
# Usage:
#   SCIENCECLAW_HOST=root@124.70.163.130 ./deploy_to_huawei.sh
#
# Rollback (restore a previous backup on the VM):
#   ssh $SCIENCECLAW_HOST "ls -1 /root/.openclaw/workspace/skills/.scienceclaw-backups | tail -n 5"
#   ssh $SCIENCECLAW_HOST "TS=<timestamp> bash -lc 'cd /root/.openclaw/workspace/skills && cp -a .scienceclaw-backups/${TS}/scienceclaw_* .'"
#
# Requirements:
# - passwordless SSH (recommended) or configured SSH agent

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="${ROOT_DIR}/skills"

HOST="${SCIENCECLAW_HOST:-root@124.70.163.130}"
REMOTE_WORKSPACE="${SCIENCECLAW_REMOTE_WORKSPACE:-/root/.openclaw/workspace}"
REMOTE_SKILLS="${REMOTE_WORKSPACE}/skills"

IDENTITY="${SCIENCECLAW_IDENTITY:-$HOME/.ssh/id_ed25519}"
SSH_OPTS=()
SCP_OPTS=()

retry() {
  local attempts="$1"
  shift
  local n=1
  local delay=1
  while true; do
    if "$@"; then
      return 0
    fi
    if [[ "$n" -ge "$attempts" ]]; then
      return 1
    fi
    sleep "$delay"
    n=$((n + 1))
    delay=$((delay * 2))
    if [[ "$delay" -gt 8 ]]; then
      delay=8
    fi
  done
}

if [[ -f "${IDENTITY}" ]]; then
  # Keep SSH connections alive during large scp transfers; Huawei Cloud VMs can drop idle TCP sessions.
  SSH_OPTS=(
    -i "${IDENTITY}"
    -o BatchMode=yes
    -o StrictHostKeyChecking=accept-new
    -o ConnectTimeout=10
    -o ConnectionAttempts=3
    -o ServerAliveInterval=15
    -o ServerAliveCountMax=3
    -o TCPKeepAlive=yes
  )
  SCP_OPTS=("${SSH_OPTS[@]}")
fi

TS="$(date -u +"%Y%m%d_%H%M%S")"
BACKUP_DIR="${REMOTE_SKILLS}/.scienceclaw-backups/${TS}"

echo "[deploy] host=${HOST}"
echo "[deploy] local_skills=${SKILLS_DIR}"
echo "[deploy] remote_skills=${REMOTE_SKILLS}"

retry 3 ssh "${SSH_OPTS[@]}" "${HOST}" "mkdir -p '${REMOTE_SKILLS}' '${BACKUP_DIR}'"

echo "[deploy] backing up existing scienceclaw_* skills (if any) -> ${BACKUP_DIR}"
retry 3 ssh "${SSH_OPTS[@]}" "${HOST}" "bash -lc 'shopt -s nullglob; for d in \"${REMOTE_SKILLS}\"/scienceclaw_*; do bn=\$(basename \"\$d\"); cp -a \"\$d\" \"${BACKUP_DIR}/\$bn\"; done'"

copy_skills() {
  # Remove only the skill dirs we manage to avoid accumulating stale files.
  # We do not touch other skills that may be preinstalled by the OpenClaw image.
  ssh "${SSH_OPTS[@]}" "${HOST}" "bash -lc 'rm -rf \"${REMOTE_SKILLS}\"/scienceclaw_* \"${REMOTE_SKILLS}\"/literature_pubmed_search \"${REMOTE_SKILLS}\"/pdf_extract_basic \"${REMOTE_SKILLS}\"/vendor_openclaw_scientific_skill || true'"

  # Stream a tarball to reduce SSH connection churn vs many small scp transfers.
  # macOS tar may emit Apple xattrs; disable them to avoid noisy warnings on Linux extract.
  COPYFILE_DISABLE=1 tar --no-xattrs -C "${SKILLS_DIR}" -czf - . 2>/dev/null \
    | ssh "${SSH_OPTS[@]}" "${HOST}" "tar -C '${REMOTE_SKILLS}' -xzf -"
}

echo "[deploy] copying skills (tar stream)..."
retry 3 copy_skills

echo "[deploy] fixing perms..."
retry 3 ssh "${SSH_OPTS[@]}" "${HOST}" "chmod +x '${REMOTE_SKILLS}/scienceclaw_installer/run.sh' '${REMOTE_SKILLS}/scienceclaw_meta/phase2_acceptance_vm.sh' 2>/dev/null || true"

echo "[deploy] running selfcheck..."
retry 3 ssh "${SSH_OPTS[@]}" "${HOST}" "python3 '${REMOTE_SKILLS}/scienceclaw_selfcheck/run.py' | tail -n 1"

echo "[deploy] rollback hint:"
echo "[deploy]   ssh ${HOST} \"ls -1 '${REMOTE_SKILLS}/.scienceclaw-backups' | tail -n 5\""
echo "[deploy]   ssh ${HOST} \"TS=<timestamp> bash -lc 'cd \\\"${REMOTE_SKILLS}\\\" && cp -a .scienceclaw-backups/\\${TS}/scienceclaw_* .'\""

echo "[deploy] done"
