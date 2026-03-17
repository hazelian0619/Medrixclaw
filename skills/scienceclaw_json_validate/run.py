from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import append_command, init_run, record_artifact  # noqa: E402


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _err(errors: List[str], msg: str) -> None:
    errors.append(msg)


def _warn(warnings: List[str], msg: str) -> None:
    warnings.append(msg)


def _require_dict(x: Any, errors: List[str], name: str) -> Dict[str, Any]:
    if not isinstance(x, dict):
        _err(errors, f"{name} must be an object")
        return {}
    return x


def _require_list(x: Any, errors: List[str], name: str) -> List[Any]:
    if not isinstance(x, list):
        _err(errors, f"{name} must be an array")
        return []
    return x


def validate_manifest(data: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    d = _require_dict(data, errors, "manifest")
    if d.get("schemaVersion") != 1:
        _warn(warnings, "schemaVersion should be 1")
    for k in ("createdAt", "project", "task", "runId", "inputs", "environment", "artifacts", "commands"):
        if k not in d:
            _err(errors, f"missing field: {k}")
    env = d.get("environment")
    if isinstance(env, dict):
        if "python" not in env:
            _warn(warnings, "environment.python missing")
        if "cwd" not in env:
            _warn(warnings, "environment.cwd missing")
    arts = d.get("artifacts")
    if isinstance(arts, list):
        for i, a in enumerate(arts[:500]):
            if not isinstance(a, dict):
                _err(errors, f"artifacts[{i}] must be an object")
                continue
            if "path" not in a or "kind" not in a:
                _err(errors, f"artifacts[{i}] missing path/kind")
            if a.get("sha256") is None:
                _warn(warnings, f"artifacts[{i}] missing sha256 (ok for non-file artifacts)")
    return errors, warnings


def validate_evidence(data: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    items = _require_list(data, errors, "evidence")
    for i, ev in enumerate(items[:2000]):
        if not isinstance(ev, dict):
            _err(errors, f"evidence[{i}] must be an object")
            continue
        for k in ("source", "locator", "quote", "usedIn"):
            if k not in ev:
                _err(errors, f"evidence[{i}] missing field: {k}")
        if "quote" in ev and isinstance(ev.get("quote"), str) and len(ev.get("quote") or "") > 2000:
            _warn(warnings, f"evidence[{i}].quote is long (>2000 chars)")
        used_in = ev.get("usedIn")
        if used_in is not None and not isinstance(used_in, list):
            _err(errors, f"evidence[{i}].usedIn must be an array")
    return errors, warnings


def validate_profile(data: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    d = _require_dict(data, errors, "profile")
    if d.get("schemaVersion") != 1:
        _warn(warnings, "schemaVersion should be 1")
    if "source" not in d:
        _err(errors, "missing source")
    if "format" not in d:
        _err(errors, "missing format")
    if "rowsScanned" not in d:
        _warn(warnings, "rowsScanned missing")
    if "columns" not in d:
        _warn(warnings, "columns missing")
    return errors, warnings


def validate_conversion(data: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    d = _require_dict(data, errors, "conversion")
    if d.get("schemaVersion") != 1:
        _warn(warnings, "schemaVersion should be 1")
    if "input" not in d:
        _err(errors, "missing input")
    if "outputs" not in d:
        _err(errors, "missing outputs")
    return errors, warnings


def validate_fetch_plan(data: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    d = _require_dict(data, errors, "fetch_plan")
    if d.get("schemaVersion") != 1:
        _warn(warnings, "schemaVersion should be 1")
    if "urls" not in d:
        _err(errors, "missing urls")
    return errors, warnings


def validate_fetch_results(data: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    d = _require_dict(data, errors, "fetch_results")
    if d.get("schemaVersion") != 1:
        _warn(warnings, "schemaVersion should be 1")
    res = d.get("results")
    if not isinstance(res, list):
        _err(errors, "results must be an array")
        return errors, warnings
    for i, r in enumerate(res[:2000]):
        if not isinstance(r, dict):
            _err(errors, f"results[{i}] must be an object")
            continue
        if "url" not in r or "ok" not in r:
            _err(errors, f"results[{i}] missing url/ok")
    return errors, warnings


def validate_citations_normalized(data: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    d = _require_dict(data, errors, "citations_normalized")
    if d.get("schemaVersion") != 1:
        _warn(warnings, "schemaVersion should be 1")
    if "citations" not in d:
        _err(errors, "missing citations")
    cits = d.get("citations")
    if isinstance(cits, list):
        for i, c in enumerate(cits[:2000]):
            if not isinstance(c, dict):
                _err(errors, f"citations[{i}] must be an object")
                continue
            if "canonical" not in c or "kind" not in c:
                _err(errors, f"citations[{i}] missing canonical/kind")
    return errors, warnings


VALIDATORS = {
    "manifest": validate_manifest,
    "evidence": validate_evidence,
    "profile": validate_profile,
    "conversion": validate_conversion,
    "fetch_plan": validate_fetch_plan,
    "fetch_results": validate_fetch_results,
    "citations_normalized": validate_citations_normalized,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--type", required=True, choices=sorted(VALIDATORS.keys()))
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--project", default="default")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    in_path = Path(args.json).expanduser().resolve()
    if not in_path.exists():
        raise SystemExit(f"json not found: {in_path}")

    ctx = init_run(
        workspace_dir=Path(args.workspace),
        project=args.project,
        task="scienceclaw_json_validate",
        inputs={"json": str(in_path), "type": args.type, "strict": bool(args.strict), "noLlm": bool(args.no_llm)},
    )
    append_command(ctx, sys.argv[:])

    raw = json.loads(in_path.read_text(encoding="utf-8"))
    errors, warnings = VALIDATORS[args.type](raw)
    ok = len(errors) == 0

    out = {
        "schemaVersion": 1,
        "input": {"path": str(in_path), "sha256": _sha256_file(in_path), "type": args.type},
        "ok": ok,
        "errors": errors,
        "warnings": warnings,
    }
    out_path = ctx.artifacts_dir / "validation.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, out_path, kind="json.validation", meta={"ok": ok, "errors": len(errors), "warnings": len(warnings)})

    log_path = ctx.logs_dir / "validate.log"
    log_lines = [f"type={args.type}", f"ok={ok}", f"errors={len(errors)}", f"warnings={len(warnings)}"]
    for e in errors[:50]:
        log_lines.append("ERROR: " + e)
    for w in warnings[:50]:
        log_lines.append("WARN: " + w)
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"step": "validate", "ok": ok})

    print(str(ctx.run_dir))
    return 0 if (ok or not args.strict) else 2


if __name__ == "__main__":
    raise SystemExit(main())

