from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import append_command, init_run, record_artifact  # noqa: E402


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--project", default="governance")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    skills_dir = workspace / "skills"
    pack_path = skills_dir / "scienceclaw_meta" / "pack.json"

    ctx = init_run(
        workspace_dir=workspace,
        project=args.project,
        task="scienceclaw_pack_validate",
        inputs={"workspace": str(workspace), "strict": bool(args.strict)},
    )
    append_command(ctx, sys.argv[:])

    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    if not pack_path.exists():
        errors.append({"code": "missing_pack_json", "path": str(pack_path), "message": "scienceclaw_meta/pack.json not found"})
        report = {"schemaVersion": 1, "createdAt": _now_utc(), "ok": False, "errors": errors, "warnings": warnings}
    else:
        pack = _read_json(pack_path)
        allow = pack.get("allowlist") if isinstance(pack, dict) else None
        pack_version = pack.get("packVersion") if isinstance(pack, dict) else None
        if not isinstance(allow, list):
            errors.append({"code": "invalid_allowlist", "path": str(pack_path), "message": "pack.json allowlist must be a list"})
            allow = []

        for name in allow:
            if not isinstance(name, str) or not name.strip():
                warnings.append({"code": "bad_allowlist_entry", "message": f"non-string allowlist entry: {name!r}"})
                continue
            d = skills_dir / name
            if not d.exists() or not d.is_dir():
                errors.append({"code": "missing_skill_dir", "path": str(d), "message": f"skill dir not found: {name}"})
                continue
            skill_md = d / "SKILL.md"
            if not skill_md.exists():
                errors.append({"code": "missing_skill_md", "path": str(skill_md), "message": f"SKILL.md missing: {name}"})

            # Executable entrypoint: run.py or run.sh. Vendored library is allowed to be doc-only.
            if name.startswith("vendor_"):
                continue
            if not (d / "run.py").exists() and not (d / "run.sh").exists():
                warnings.append({"code": "missing_entrypoint", "path": str(d), "message": f"no run.py/run.sh entrypoint found: {name}"})

        report = {
            "schemaVersion": 1,
            "createdAt": _now_utc(),
            "packVersion": pack_version,
            "skillsDir": str(skills_dir),
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    out_path = ctx.artifacts_dir / "pack_validate.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, out_path, kind="pack_validate", meta={"ok": report.get("ok"), "errors": len(errors), "warnings": len(warnings)})

    log_path = ctx.logs_dir / "pack_validate.log"
    log_lines = [f"workspace={workspace}", f"pack={pack_path}", f"ok={report.get('ok')} errors={len(errors)} warnings={len(warnings)}"]
    for e in errors[:30]:
        log_lines.append(f"ERROR {e.get('code')}: {e.get('message')} ({e.get('path','')})")
    for w in warnings[:30]:
        log_lines.append(f"WARN {w.get('code')}: {w.get('message')} ({w.get('path','')})")
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"step": "pack_validate"})

    print(str(ctx.run_dir))
    if args.strict and errors:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

