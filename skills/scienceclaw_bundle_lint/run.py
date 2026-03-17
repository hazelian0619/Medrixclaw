from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import append_command, attach_run, init_run, record_artifact  # noqa: E402


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _err(code: str, msg: str, *, path: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {"code": code, "message": msg}
    if path:
        out["path"] = path
    return out


def _infer_profile(manifest: Dict[str, Any]) -> str:
    task = str(manifest.get("task") or "").strip()
    # Historical/compat: early versions used "scienceclaw_lit_brief" as the task name.
    if task.endswith("scienceclaw_lit_brief"):
        return "lit_brief"
    if task.endswith("scienceclaw_workflow_lit_brief"):
        return "lit_brief"
    if task.endswith("scienceclaw_workflow_pdf_brief"):
        return "pdf_brief"
    if task.endswith("scienceclaw_workflow_table_to_csv"):
        return "table_to_csv"
    if task.endswith("scienceclaw_workflow_omics_kickoff"):
        return "omics_kickoff"
    if task.endswith("scienceclaw_workflow_vcf_annotate_brief"):
        return "vcf_annotate_brief"
    return "any"


def _required_artifacts_for_profile(profile: str) -> List[str]:
    # Paths are relative to runDir.
    if profile == "lit_brief":
        return [
            "artifacts/brief.md",
            "artifacts/results.json",
            "artifacts/evidence.json",
            "artifacts/citations.bib",
        ]
    if profile == "pdf_brief":
        return [
            "artifacts/brief.md",
            "artifacts/extracted.json",
            "artifacts/evidence.json",
            "artifacts/citations.bib",
        ]
    if profile == "table_to_csv":
        return [
            "artifacts/tables.json",
            "artifacts/tables.csv",
            "artifacts/evidence.json",
        ]
    if profile == "omics_kickoff":
        return [
            "artifacts/analysis_plan.md",
            "artifacts/environment.md",
            "artifacts/perf_env.json",
            "artifacts/qc_summary.md",
            "artifacts/annotation_table.tsv",
            "artifacts/citations.bib",
            "artifacts/evidence.json",
            "artifacts/figures/.keep",
        ]
    if profile == "vcf_annotate_brief":
        return [
            "artifacts/vcf.stats.json",
            "artifacts/variants.annotated.tsv",
            "artifacts/variants.annotated.json",
            "artifacts/variants.summary.json",
            "artifacts/brief.md",
            "artifacts/evidence.json",
            "artifacts/citations.bib",
        ]
    return [
        "manifest.json",
    ]


def _validate_evidence(evidence_path: Path, *, strict: bool) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    stats: Dict[str, Any] = {}

    try:
        raw = _read_json(evidence_path)
    except Exception as e:
        errors.append(_err("evidence_invalid_json", f"evidence.json is not valid JSON: {e}", path=str(evidence_path)))
        return errors, warnings, stats

    if not isinstance(raw, list):
        errors.append(_err("evidence_not_array", "evidence.json must be an array (EvidenceItem[])", path=str(evidence_path)))
        return errors, warnings, stats

    stats["evidenceCount"] = len(raw)
    if strict and len(raw) == 0:
        errors.append(_err("evidence_empty", "evidence.json is empty (strict)", path=str(evidence_path)))
        return errors, warnings, stats
    if len(raw) == 0:
        warnings.append(_err("evidence_empty", "evidence.json is empty", path=str(evidence_path)))
        return errors, warnings, stats

    required = ["source", "locator", "quote", "usedIn"]
    for i, it in enumerate(raw[:200]):  # keep lint bounded
        if not isinstance(it, dict):
            errors.append(_err("evidence_item_not_object", f"evidence[{i}] must be an object", path=str(evidence_path)))
            continue
        for k in required:
            if k not in it:
                errors.append(_err("evidence_missing_field", f"evidence[{i}] missing required field: {k}", path=str(evidence_path)))
        if "quote" in it:
            q = str(it.get("quote") or "")
            if strict and len(q.strip()) < 20:
                warnings.append(_err("evidence_quote_too_short", f"evidence[{i}].quote seems too short (<20 chars)", path=str(evidence_path)))
        if "usedIn" in it and not isinstance(it.get("usedIn"), list):
            errors.append(_err("evidence_usedin_not_array", f"evidence[{i}].usedIn must be an array", path=str(evidence_path)))

    return errors, warnings, stats


def _validate_citations_bib(path: Path, *, strict: bool) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    stats: Dict[str, Any] = {}

    if not path.exists():
        errors.append(_err("citations_missing", "citations.bib missing", path=str(path)))
        return errors, warnings, stats
    size = path.stat().st_size
    stats["citationsBytes"] = size
    if strict and size == 0:
        errors.append(_err("citations_empty", "citations.bib is empty (strict)", path=str(path)))
        return errors, warnings, stats
    if size == 0:
        warnings.append(_err("citations_empty", "citations.bib is empty", path=str(path)))
        return errors, warnings, stats
    head = path.read_text(encoding="utf-8", errors="replace")[:2000]
    if "@" not in head:
        warnings.append(_err("citations_suspicious", "citations.bib does not look like BibTeX (missing '@' in header)", path=str(path)))
    return errors, warnings, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, help="Target run bundle directory (will be linted and annotated).")
    ap.add_argument("--profile", default="auto", help="auto|lit_brief|pdf_brief|table_to_csv|omics_kickoff|any")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--project", default="default")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()

    # Always attach to the target runDir so the lint report is part of the same bundle.
    ctx = attach_run(
        run_dir=run_dir,
        task_hint="scienceclaw_bundle_lint",
        inputs_update={"bundleLint": {"profile": args.profile, "strict": bool(args.strict)}},
    )
    append_command(ctx, sys.argv[:])

    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    # 1) manifest.json parse
    manifest_path = run_dir / "manifest.json"
    manifest: Dict[str, Any] = {}
    if not manifest_path.exists():
        errors.append(_err("manifest_missing", "manifest.json missing", path=str(manifest_path)))
    else:
        try:
            raw = _read_json(manifest_path)
            if not isinstance(raw, dict):
                errors.append(_err("manifest_not_object", "manifest.json must be an object", path=str(manifest_path)))
            else:
                manifest = raw
        except Exception as e:
            errors.append(_err("manifest_invalid_json", f"manifest.json is not valid JSON: {e}", path=str(manifest_path)))

    # 2) Determine profile + required artifacts
    profile = args.profile.strip()
    if profile == "auto":
        profile = _infer_profile(manifest) if manifest else "any"

    required_rel = _required_artifacts_for_profile(profile)
    for rel in required_rel:
        p = run_dir / rel
        if not p.exists():
            errors.append(_err("artifact_missing", f"missing required artifact for profile={profile}: {rel}", path=str(p)))

    # 3) Specialized checks (best-effort)
    stats: Dict[str, Any] = {"profile": profile}
    ev_path = run_dir / "artifacts" / "evidence.json"
    if ev_path.exists():
        e, w, st = _validate_evidence(ev_path, strict=args.strict)
        errors.extend(e)
        warnings.extend(w)
        stats.update(st)

    cit_path = run_dir / "artifacts" / "citations.bib"
    if cit_path.exists():
        e, w, st = _validate_citations_bib(cit_path, strict=args.strict)
        errors.extend(e)
        warnings.extend(w)
        stats.update(st)

    # 4) Emit report into the same run bundle
    report = {
        "schemaVersion": 1,
        "tool": "scienceclaw_bundle_lint",
        "targetRunDir": str(run_dir),
        "profile": profile,
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }

    out_path = ctx.artifacts_dir / "bundle_lint.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, out_path, kind="bundle_lint", meta={"ok": report["ok"], "errors": len(errors), "warnings": len(warnings)})

    log_path = ctx.logs_dir / "bundle_lint.log"
    log_lines = []
    log_lines.append(f"profile={profile}")
    log_lines.append(f"strict={bool(args.strict)}")
    log_lines.append(f"errors={len(errors)} warnings={len(warnings)}")
    for it in errors[:20]:
        log_lines.append(f"ERROR {it.get('code')}: {it.get('message')} ({it.get('path','')})")
    for it in warnings[:20]:
        log_lines.append(f"WARN {it.get('code')}: {it.get('message')} ({it.get('path','')})")
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"step": "bundle_lint"})

    print(str(ctx.run_dir))
    if args.strict and errors:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
