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

from run_context import append_command, init_run, record_artifact, run_checked  # noqa: E402


def _bibtex_placeholder() -> str:
    year = time.gmtime().tm_year
    return (
        "@misc{scienceclaw_vcf_workflow,\n"
        "  title = {ScienceClaw Phase 3 VCF Annotate Brief (Offline Baseline)},\n"
        f"  year = {{{year}}},\n"
        "  note = {Offline baseline output; citations will be normalized from evidence sources when available},\n"
        "}\n"
    )


def _compose_brief(*, vcf_path: Path, stats: Dict[str, Any], summary: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# VCF Annotate Brief (Phase 3)\n")
    lines.append(f"- created_at_utc: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}")
    lines.append(f"- input_vcf: `{vcf_path}`")
    lines.append("")
    lines.append("## Summary\n")
    counts = summary.get("counts") if isinstance(summary.get("counts"), dict) else {}
    lines.append(f"- exported_variants: {counts.get('exported')}")
    lines.append(f"- skipped_variants: {counts.get('skipped')}")
    lines.append(f"- contigs: {counts.get('contigs')}")
    lines.append(f"- multiallelic: {counts.get('multiallelic')}")
    lines.append("")
    lines.append("## Validation\n")
    vcounts = stats.get("counts") if isinstance(stats.get("counts"), dict) else {}
    lines.append(f"- variants_detected: {vcounts.get('variants')}")
    lines.append(f"- samples: {len(stats.get('samples') or [])}")
    if stats.get("warnings"):
        lines.append("")
        lines.append("### Warnings\n")
        for w in (stats.get("warnings") or [])[:10]:
            lines.append(f"- {w}")
    lines.append("")
    lines.append("## Deliverables\n")
    lines.append("- `variants.annotated.tsv` / `variants.annotated.json`")
    lines.append("- `evidence.json` (non-empty)")
    lines.append("- `citations.bib` (non-empty)")
    lines.append("- `report.md` + `reproducibility/` + `bundle_lint.json`")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vcf", required=True)
    ap.add_argument("--project", default="default")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    skills = workspace / "skills"
    vcf_path = Path(args.vcf).expanduser().resolve()
    if not vcf_path.exists() or not vcf_path.is_file():
        raise SystemExit(f"vcf not found: {vcf_path}")

    ctx = init_run(
        workspace_dir=workspace,
        project=args.project,
        task="scienceclaw_workflow_vcf_annotate_brief",
        inputs={"vcf": str(vcf_path), "noLlm": bool(args.no_llm)},
    )
    append_command(ctx, sys.argv[:])

    # 1) vcf_validate -> writes vcf.stats.json and appends evidence
    validate = skills / "scienceclaw_bio_vcf_validate" / "run.py"
    if not validate.exists():
        raise SystemExit(f"missing atomic skill: {validate}")
    run_checked(
        ctx=ctx,
        argv=[sys.executable, str(validate), "--vcf", str(vcf_path), "--run-dir", str(ctx.run_dir), "--project", args.project, "--no-llm"],
        log_name="step_vcf_validate.log",
    )

    # 2) vcf_annotate -> variants.* and appends evidence
    annotate = skills / "scienceclaw_bio_vcf_annotate" / "run.py"
    if not annotate.exists():
        raise SystemExit(f"missing atomic skill: {annotate}")
    run_checked(
        ctx=ctx,
        argv=[sys.executable, str(annotate), "--vcf", str(vcf_path), "--run-dir", str(ctx.run_dir), "--project", args.project, "--no-llm"],
        log_name="step_vcf_annotate.log",
    )

    # 3) Ensure citations non-empty before any normalization (guardrail).
    cit_path = ctx.artifacts_dir / "citations.bib"
    if not cit_path.exists() or cit_path.stat().st_size == 0:
        cit_path.write_text(_bibtex_placeholder(), encoding="utf-8")
        record_artifact(ctx, cit_path, kind="citations.bib", meta={"mode": "placeholder_pre_normalize"})

    # 4) Compose brief.md (deterministic, no LLM).
    stats_path = ctx.artifacts_dir / "vcf.stats.json"
    summary_path = ctx.artifacts_dir / "variants.summary.json"
    stats: Dict[str, Any] = json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.exists() else {}
    summary: Dict[str, Any] = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    brief_path = ctx.artifacts_dir / "brief.md"
    brief_path.write_text(_compose_brief(vcf_path=vcf_path, stats=stats, summary=summary), encoding="utf-8")
    record_artifact(ctx, brief_path, kind="brief.md", meta={"mode": "deterministic"})

    # 5) Governance tail: normalize -> report -> repro -> lint (all write back to same runDir).
    evidence_path = ctx.artifacts_dir / "evidence.json"
    normalize = skills / "scienceclaw_citation_normalize" / "run.py"
    if normalize.exists() and evidence_path.exists():
        run_checked(
            ctx=ctx,
            argv=[sys.executable, str(normalize), "--run-dir", str(ctx.run_dir), "--evidence-json", str(evidence_path), "--project", args.project, "--no-llm"],
            log_name="step_citation_normalize.log",
        )

    report = skills / "scienceclaw_report_compose_md" / "run.py"
    if report.exists():
        run_checked(
            ctx=ctx,
            argv=[sys.executable, str(report), "--run-dir", str(ctx.run_dir), "--title", "Phase3: VCF Annotate Brief", "--no-llm"],
            log_name="step_report_compose.log",
        )

    repro = skills / "scienceclaw_repro_export" / "run.py"
    if repro.exists():
        run_checked(
            ctx=ctx,
            argv=[sys.executable, str(repro), "--run-dir", str(ctx.run_dir), "--source-run-dir", str(ctx.run_dir), "--no-llm"],
            log_name="step_repro_export.log",
        )

    lint = skills / "scienceclaw_bundle_lint" / "run.py"
    if lint.exists():
        # Strict: this is our L5 gate for Domain Pack.
        run_checked(
            ctx=ctx,
            argv=[sys.executable, str(lint), "--run-dir", str(ctx.run_dir), "--profile", "auto", "--strict", "--no-llm"],
            log_name="step_bundle_lint.log",
        )

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
