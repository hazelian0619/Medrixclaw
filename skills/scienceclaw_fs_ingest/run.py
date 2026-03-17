from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import attach_run, append_command, init_run, record_artifact  # noqa: E402


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_name(name: str) -> str:
    # Keep it simple and filesystem-safe.
    out = "".join(c for c in (name or "") if c.isalnum() or c in ("-", "_", ".", " ")).strip().replace(" ", "_")
    return out or "input"


def _unique_path(dir_path: Path, filename: str) -> Path:
    p = dir_path / filename
    if not p.exists():
        return p
    stem = p.stem
    suffix = p.suffix
    for i in range(2, 1000):
        cand = dir_path / f"{stem}_{i}{suffix}"
        if not cand.exists():
            return cand
    raise RuntimeError(f"too many collisions for filename: {filename}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", action="append", required=True, help="Local file path (repeatable).")
    ap.add_argument("--project", default="default")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    ap.add_argument("--run-dir", default="", help="(internal) write artifacts into an existing run dir created by a workflow")
    args = ap.parse_args()

    src_paths = [Path(p).expanduser().resolve() for p in (args.path or [])]
    for p in src_paths:
        if not p.exists():
            raise SystemExit(f"input not found: {p}")
        if not p.is_file():
            raise SystemExit(f"input is not a regular file: {p}")

    if args.run_dir:
        ctx = attach_run(run_dir=Path(args.run_dir), task_hint="scienceclaw_fs_ingest", inputs_update={"paths": [str(p) for p in src_paths]})
    else:
        ctx = init_run(
            workspace_dir=Path(args.workspace),
            project=args.project,
            task="scienceclaw_fs_ingest",
            inputs={"paths": [str(p) for p in src_paths], "noLlm": bool(args.no_llm)},
        )

    append_command(ctx, sys.argv[:])

    inputs_dir = ctx.artifacts_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    log_lines: List[str] = []
    items: List[Dict[str, Any]] = []

    for src in src_paths:
        name = _safe_name(src.name)
        dst = _unique_path(inputs_dir, name)
        shutil.copy2(src, dst)
        sha = _sha256_file(dst)
        meta = {
            "src": str(src),
            "dst": str(dst.relative_to(ctx.run_dir)),
            "bytes": dst.stat().st_size,
            "sha256": sha,
        }
        # record_artifact computes sha256 for dst; also store it in ingest.json for convenience.
        record_artifact(ctx, dst, kind="input.file", meta={"src": str(src)})
        items.append(meta)
        log_lines.append(f"copied {src} -> {dst} sha256={sha[:12]}...")

    out_path = ctx.artifacts_dir / "ingest.json"
    out_path.write_text(json.dumps({"schemaVersion": 1, "items": items}, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, out_path, kind="fs.ingest", meta={"count": len(items)})

    log_path = ctx.logs_dir / "ingest.log"
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"step": "ingest", "ok": True})

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
