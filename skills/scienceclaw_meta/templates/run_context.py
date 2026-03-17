from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class RunContext:
    project_dir: Path
    run_dir: Path
    artifacts_dir: Path
    logs_dir: Path
    manifest_path: Path


def init_run(
    *,
    workspace_dir: Path,
    project: str,
    task: str,
    inputs: Optional[Dict[str, Any]] = None,
) -> RunContext:
    safe_project = "".join(c for c in project if c.isalnum() or c in ("-", "_")).strip("_-") or "default"
    safe_task = "".join(c for c in task if c.isalnum() or c in ("-", "_")).strip("_-") or "task"

    project_dir = workspace_dir / "projects" / safe_project
    runs_dir = project_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    # Seconds-level timestamps can collide in parallel runs; add pid + random suffix.
    uniq = f"{os.getpid()}_{secrets.token_hex(3)}"
    run_id = f"{time.strftime('%Y%m%d_%H%M%S', time.gmtime())}__{safe_task}__{uniq}"
    run_dir = runs_dir / run_id
    artifacts_dir = run_dir / "artifacts"
    logs_dir = run_dir / "logs"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = run_dir / "manifest.json"
    manifest = {
        "schemaVersion": 1,
        "createdAt": _utc_ts(),
        "project": safe_project,
        "task": safe_task,
        "runId": run_id,
        "inputs": inputs or {},
        "environment": {"python": sys.version.split()[0], "cwd": str(Path.cwd())},
        "artifacts": [],
        "commands": [],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    return RunContext(
        project_dir=project_dir,
        run_dir=run_dir,
        artifacts_dir=artifacts_dir,
        logs_dir=logs_dir,
        manifest_path=manifest_path,
    )


def attach_run(*, run_dir: Path, task_hint: str = "task", inputs_update: Optional[Dict[str, Any]] = None) -> RunContext:
    """
    Attach to an existing run directory created by another skill (workflow).
    This allows a workflow to create the run bundle once, while atomic skills
    write artifacts into the same `artifacts/` and update the same manifest.
    """
    run_dir = run_dir.expanduser().resolve()
    artifacts_dir = run_dir / "artifacts"
    logs_dir = run_dir / "logs"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        # Best-effort: init a minimal manifest so downstream tools still work.
        manifest = {
            "schemaVersion": 1,
            "createdAt": _utc_ts(),
            "project": "default",
            "task": task_hint,
            "runId": run_dir.name,
            "inputs": {},
            "environment": {"python": sys.version.split()[0], "cwd": str(Path.cwd())},
            "artifacts": [],
            "commands": [],
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    if inputs_update:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data.setdefault("inputs", {}).update(inputs_update)
        manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    # We cannot reliably infer project_dir from run_dir alone; keep it consistent but unused.
    return RunContext(
        project_dir=run_dir.parent.parent,
        run_dir=run_dir,
        artifacts_dir=artifacts_dir,
        logs_dir=logs_dir,
        manifest_path=manifest_path,
    )


def append_command(ctx: RunContext, argv: List[str]) -> None:
    data = json.loads(ctx.manifest_path.read_text(encoding="utf-8"))
    data.setdefault("commands", []).append({"at": _utc_ts(), "argv": argv})
    ctx.manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def record_artifact(ctx: RunContext, path: Path, kind: str, meta: Optional[Dict[str, Any]] = None) -> None:
    data = json.loads(ctx.manifest_path.read_text(encoding="utf-8"))
    rel = str(path.relative_to(ctx.run_dir))
    entry: Dict[str, Any] = {"at": _utc_ts(), "path": rel, "kind": kind}
    if path.is_file():
        entry["bytes"] = path.stat().st_size
        entry["sha256"] = _sha256_file(path)
    if meta:
        entry["meta"] = meta
    data.setdefault("artifacts", []).append(entry)
    ctx.manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def run_checked(*, ctx: RunContext, argv: List[str], log_name: str) -> None:
    """
    Optional helper: run a subprocess, capture output to logs/, and record the log as an artifact.
    """
    append_command(ctx, argv)
    log_path = ctx.logs_dir / log_name
    with log_path.open("wb") as log:
        proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, env=os.environ.copy())
        rc = proc.wait()
    record_artifact(ctx, log_path, kind="log", meta={"exitCode": rc})
    if rc != 0:
        raise RuntimeError(f"command failed rc={rc}, see log: {log_path}")

