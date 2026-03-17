from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import attach_run, append_command, init_run, record_artifact  # noqa: E402


def _read_manifest(run_dir: Path) -> Dict[str, Any]:
    p = run_dir / "manifest.json"
    if not p.exists():
        raise SystemExit(f"manifest.json not found in runDir: {run_dir}")
    return json.loads(p.read_text(encoding="utf-8"))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _render_commands_sh(commands: List[Dict[str, Any]], *, header_note: str = "") -> str:
    lines: List[str] = []
    lines.append("#!/usr/bin/env bash")
    lines.append("set -euo pipefail")
    lines.append("")
    if header_note:
        lines.append(f"# {header_note}")
        lines.append("")
    for c in commands:
        at = str(c.get("at") or "")
        argv = c.get("argv")
        if not isinstance(argv, list) or not argv:
            continue
        cmd = " ".join(shlex.quote(str(x)) for x in argv)
        if at:
            lines.append(f"# at={at}")
        lines.append(cmd)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_checksums(artifacts: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
    # Format: "<sha256>  <path>" like coreutils sha256sum output.
    lines: List[str] = []
    missing = 0
    for a in artifacts:
        sha = a.get("sha256")
        p = a.get("path")
        if not sha or not p:
            missing += 1
            continue
        lines.append(f"{sha}  {p}")
    lines.sort()
    stats = {"totalArtifacts": len(artifacts), "checksummed": len(lines), "missingShaOrPath": missing}
    return "\n".join(lines).rstrip() + "\n", stats


def _environment_snapshot(*, want_pip_freeze: bool) -> Tuple[str, Dict[str, Any]]:
    lines: List[str] = []
    meta: Dict[str, Any] = {}
    lines.append(f"python: {sys.version.split()[0]}")
    lines.append(f"platform: {sys.platform}")
    lines.append("")
    if want_pip_freeze:
        try:
            out = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True, stderr=subprocess.STDOUT, timeout=30)
            lines.append("# pip freeze")
            lines.append(out.strip())
            meta["pipFreeze"] = "ok"
        except Exception as e:
            lines.append(f"# pip freeze failed: {e}")
            meta["pipFreeze"] = "failed"
    return "\n".join(lines).rstrip() + "\n", meta


def _analysis_log(commands: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("# Analysis Log")
    lines.append("")
    for c in commands:
        at = str(c.get("at") or "")
        argv = c.get("argv")
        if not isinstance(argv, list):
            continue
        cmd = " ".join(shlex.quote(str(x)) for x in argv)
        lines.append(f"- `{at}` `{cmd}`".strip())
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default="", help="Target runDir to write reproducibility artifacts into.")
    ap.add_argument("--source-run-dir", default="", help="Optional source runDir to read manifest from (default: target runDir).")
    ap.add_argument("--pip-freeze", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--project", default="default")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    if args.run_dir:
        ctx = attach_run(run_dir=Path(args.run_dir), task_hint="scienceclaw_repro_export", inputs_update={"sourceRunDir": args.source_run_dir or args.run_dir})
    else:
        ctx = init_run(
            workspace_dir=Path(args.workspace),
            project=args.project,
            task="scienceclaw_repro_export",
            inputs={"sourceRunDir": args.source_run_dir or "", "pipFreeze": bool(args.pip_freeze), "noLlm": bool(args.no_llm)},
        )

    append_command(ctx, sys.argv[:])

    target_run = ctx.run_dir
    source_run = Path(args.source_run_dir).expanduser().resolve() if args.source_run_dir else target_run

    man = _read_manifest(source_run)
    commands = man.get("commands") if isinstance(man.get("commands"), list) else []
    artifacts = man.get("artifacts") if isinstance(man.get("artifacts"), list) else []
    env = man.get("environment") if isinstance(man.get("environment"), dict) else {}

    repro_dir = target_run / "artifacts" / "reproducibility"
    repro_dir.mkdir(parents=True, exist_ok=True)

    note = f"source_run={source_run} task={man.get('task')} createdAt={man.get('createdAt')} python={env.get('python')}"
    commands_sh = repro_dir / "commands.sh"
    _write(commands_sh, _render_commands_sh(commands, header_note=note))
    # Make it executable (best-effort).
    try:
        commands_sh.chmod(0o755)
    except Exception:
        pass
    record_artifact(ctx, commands_sh, kind="repro.commands.sh", meta={"sourceRunDir": str(source_run)})

    checksums_txt, checksum_stats = _render_checksums(artifacts)
    checksums_path = repro_dir / "checksums.sha256"
    _write(checksums_path, checksums_txt)
    record_artifact(ctx, checksums_path, kind="repro.checksums", meta=checksum_stats)

    env_txt, env_meta = _environment_snapshot(want_pip_freeze=bool(args.pip_freeze))
    env_path = repro_dir / "environment.txt"
    _write(env_path, env_txt)
    record_artifact(ctx, env_path, kind="repro.environment", meta=env_meta)

    log_md = repro_dir / "analysis_log.md"
    _write(log_md, _analysis_log(commands))
    record_artifact(ctx, log_md, kind="repro.analysis_log", meta={"commands": len(commands)})

    repro_json = repro_dir / "repro.json"
    repro = {
        "schemaVersion": 1,
        "generatedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sourceRunDir": str(source_run),
        "targetRunDir": str(target_run),
        "source": {
            "task": man.get("task"),
            "runId": man.get("runId"),
            "createdAt": man.get("createdAt"),
        },
        "counts": {
            "commands": len(commands),
            "artifacts": len(artifacts),
            **checksum_stats,
        },
    }
    _write(repro_json, json.dumps(repro, indent=2, ensure_ascii=True) + "\n")
    record_artifact(ctx, repro_json, kind="repro.meta", meta={"sourceRunDir": str(source_run)})

    tool_log = ctx.logs_dir / "repro_export.log"
    _write(tool_log, f"ok source={source_run} target={target_run}\n")
    record_artifact(ctx, tool_log, kind="log", meta={"step": "repro_export", "ok": True})

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

