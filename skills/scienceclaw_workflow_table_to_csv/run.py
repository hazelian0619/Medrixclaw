from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import append_command, init_run, record_artifact  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--project", default="default")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    workspace = Path(args.workspace)
    ctx = init_run(
        workspace_dir=workspace,
        project=args.project,
        task="scienceclaw_workflow_table_to_csv",
        inputs={"pdf": str(Path(args.pdf).expanduser().resolve()), "noLlm": bool(args.no_llm)},
    )
    append_command(ctx, sys.argv[:])

    atomic = workspace / "skills" / "scienceclaw_table_extract_from_pdf" / "run.py"
    if not atomic.exists():
        raise SystemExit(f"atomic skill not found: {atomic}")

    log_path = ctx.logs_dir / "workflow.log"
    argv = [
        sys.executable,
        str(atomic),
        "--pdf",
        args.pdf,
        "--project",
        args.project,
        "--workspace",
        str(workspace),
        "--run-dir",
        str(ctx.run_dir),
    ]
    if args.no_llm:
        argv.append("--no-llm")

    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=os.environ.copy(), text=True)
    out, _ = proc.communicate(timeout=600)
    log_path.write_text(out or "", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"exitCode": proc.returncode})
    if proc.returncode != 0:
        raise SystemExit(f"workflow failed, see log: {log_path}")

    # Validate required artifacts exist (atomic wrote into our runDir).
    required = [
        ctx.run_dir / "manifest.json",
        ctx.run_dir / "artifacts" / "tables.json",
        ctx.run_dir / "artifacts" / "tables.csv",
        ctx.run_dir / "artifacts" / "evidence.json",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit("missing required artifacts:\n" + "\n".join(missing))

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

