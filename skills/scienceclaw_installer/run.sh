#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SKILLS_DIR="${WORKSPACE}/skills"
PACK_JSON="${SKILLS_DIR}/scienceclaw_meta/pack.json"

export PATH="$HOME/.local/bin:$PATH"
export PIP_DISABLE_PIP_VERSION_CHECK=1

echo "[scienceclaw_installer] python:"
python3 -V

echo "[scienceclaw_installer] pip:"
python3 -m pip -V || true

pack_version="unknown"
if [[ -f "${PACK_JSON}" ]]; then
  pack_version="$(
    python3 - <<'PY' "${PACK_JSON}" 2>/dev/null || true
import json, sys
path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    print(json.load(f).get("packVersion", "unknown"))
PY
  )"
fi
echo "[scienceclaw_installer] packVersion=${pack_version}"

net_ok() {
  python3 - <<'PY' >/dev/null 2>&1
import socket
socket.setdefaulttimeout(2.0)
socket.create_connection(("pypi.org", 443), timeout=2.0).close()
PY
}

ensure_deps() {
  python3 - <<'PY' >/dev/null 2>&1
import requests  # noqa: F401
import fitz  # PyMuPDF  # noqa: F401
PY
}

pip_install_user() {
  # On Huawei Cloud VMs we often run as root. We intentionally keep --user installs
  # (isolated to $HOME/.local) and suppress pip's root warning for clean logs.
  python3 -m pip install \
    --user \
    --root-user-action=ignore \
    --no-input \
    -U \
    "$@" \
    >/dev/null
}

mode="online"
if ! net_ok; then
  mode="offline"
fi

if [[ "${mode}" == "online" ]]; then
  echo "[scienceclaw_installer] checking python deps..."
  if ensure_deps; then
    echo "[scienceclaw_installer] deps already satisfied"
  else
    echo "[scienceclaw_installer] installing deps (user site)..."
    # Phase 2 skills depend on:
    # - requests (NCBI E-utilities, MaaS HTTP calls)
    # - pymupdf (PDF text extraction)
    pip_install_user requests pymupdf
    echo "[scienceclaw_installer] deps installed"
  fi
else
  echo "[scienceclaw_installer] WARN: network unavailable; skipping pip installs."
  echo "[scienceclaw_installer] Hint: offline selfcheck mode:"
  echo "  python3 '${SKILLS_DIR}/scienceclaw_selfcheck/run.py' --offline"
fi

echo "[scienceclaw_installer] deps ok"
echo "[scienceclaw_installer] PATH: $PATH"

echo "[scienceclaw_installer] pack meta (best-effort):"
if [[ -f "${PACK_JSON}" ]]; then
  cat "${PACK_JSON}" || true
fi

selfcheck_run_dir=""
if [[ "${mode}" == "online" ]]; then
  echo "[scienceclaw_installer] running selfcheck (online, no LLM)..."
  selfcheck_run_dir="$(python3 "${SKILLS_DIR}/scienceclaw_selfcheck/run.py" | tail -n 1)"
else
  echo "[scienceclaw_installer] running selfcheck (offline)..."
  selfcheck_run_dir="$(python3 "${SKILLS_DIR}/scienceclaw_selfcheck/run.py" --offline | tail -n 1)"
fi

echo "[scienceclaw_installer] selfcheck runDir=${selfcheck_run_dir}"

# L5 governance gate: pack validation (best-effort, does not block install).
if [[ -f "${SKILLS_DIR}/scienceclaw_pack_validate/run.py" ]]; then
  echo "[scienceclaw_installer] pack_validate (best-effort)"
  python3 "${SKILLS_DIR}/scienceclaw_pack_validate/run.py" --no-llm --strict >/dev/null || true
fi

# Required by Phase 2 delivery/ops acceptance: print packVersion and selfcheck runDir.
echo "packVersion: ${pack_version}"
echo "selfcheck runDir: ${selfcheck_run_dir}"
if [[ "${mode}" == "offline" ]]; then
  echo "offline selfcheck mode: python3 '${SKILLS_DIR}/scienceclaw_selfcheck/run.py' --offline"
fi

echo "[scienceclaw_installer] done"
