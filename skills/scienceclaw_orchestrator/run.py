from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def _run(argv: List[str], *, timeout_s: int) -> str:
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=os.environ.copy(), text=True)
    out, _ = proc.communicate(timeout=timeout_s)
    if proc.returncode != 0:
        raise SystemExit(f"command failed (rc={proc.returncode}):\n" + (out or ""))
    return out or ""


def _last_line_path(text: str) -> Path:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    if not lines:
        raise SystemExit("workflow produced no output; cannot locate runDir")
    p = Path(lines[-1]).expanduser()
    if not p.exists():
        raise SystemExit(f"workflow did not print a valid runDir path: {p}")
    return p


def _pick_intent(*, intent: str, query: str, pdf: str, tables: bool, omics: bool) -> str:
    if intent:
        return intent
    if omics:
        return "omics_kickoff"
    if pdf and tables:
        return "table_to_csv"
    if pdf:
        return "pdf_brief"
    if query:
        return "lit_brief"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--intent", default="", help="lit_brief|pdf_brief|table_to_csv|omics_kickoff (default: auto)")

    # Common routing signals
    ap.add_argument("--query", default="")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--pdf", default="")
    ap.add_argument("--vcf", default="", help="VCF input for Phase 3 domain pack")
    ap.add_argument("--tables", action="store_true", help="With --pdf: route to table_to_csv instead of pdf_brief")
    ap.add_argument("--omics-kickoff", action="store_true", help="Route to omics kickoff template bundle")

    # Standard knobs
    ap.add_argument("--project", default="default")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--no-pdf", action="store_true", help="Lit workflow only: skip best-effort PDF fetch")
    ap.add_argument("--strict", action="store_true", help="Fail if bundle_lint finds errors")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()

    # Auto routing: vcf has higher priority than pdf/query.
    if not args.intent.strip() and args.vcf.strip():
        intent = "vcf_annotate_brief"
    else:
        intent = _pick_intent(intent=args.intent.strip(), query=args.query.strip(), pdf=args.pdf.strip(), tables=bool(args.tables), omics=bool(args.omics_kickoff))
    if intent not in ("lit_brief", "pdf_brief", "table_to_csv", "omics_kickoff", "vcf_annotate_brief"):
        raise SystemExit("cannot infer intent; provide --intent or one of: --query / --pdf / --vcf / --omics-kickoff")

    if intent == "lit_brief":
        workflow = workspace / "skills" / "scienceclaw_workflow_lit_brief" / "run.py"
        argv = [
            sys.executable,
            str(workflow),
            "--query",
            args.query,
            "--limit",
            str(int(args.limit)),
            "--project",
            args.project,
        ]
        if args.no_llm:
            argv.append("--no-llm")
        if args.no_pdf:
            argv.append("--no-pdf")
        out = _run(argv, timeout_s=600)
        run_dir = _last_line_path(out)
    elif intent == "pdf_brief":
        workflow = workspace / "skills" / "scienceclaw_workflow_pdf_brief" / "run.py"
        argv = [
            sys.executable,
            str(workflow),
            "--pdf",
            args.pdf,
            "--project",
            args.project,
            "--workspace",
            str(workspace),
        ]
        if args.no_llm:
            argv.append("--no-llm")
        out = _run(argv, timeout_s=900)
        run_dir = _last_line_path(out)
    elif intent == "table_to_csv":
        workflow = workspace / "skills" / "scienceclaw_workflow_table_to_csv" / "run.py"
        argv = [
            sys.executable,
            str(workflow),
            "--pdf",
            args.pdf,
            "--project",
            args.project,
            "--workspace",
            str(workspace),
        ]
        if args.no_llm:
            argv.append("--no-llm")
        out = _run(argv, timeout_s=900)
        run_dir = _last_line_path(out)
    else:
        if intent == "vcf_annotate_brief":
            workflow = workspace / "skills" / "scienceclaw_workflow_vcf_annotate_brief" / "run.py"
            argv = [
                sys.executable,
                str(workflow),
                "--vcf",
                args.vcf,
                "--project",
                args.project,
                "--workspace",
                str(workspace),
            ]
            if args.no_llm:
                argv.append("--no-llm")
            out = _run(argv, timeout_s=900)
            run_dir = _last_line_path(out)
        else:
            workflow = workspace / "skills" / "scienceclaw_workflow_omics_kickoff" / "run.py"
            argv = [
                sys.executable,
                str(workflow),
                "--project",
                args.project,
                "--workspace",
                str(workspace),
            ]
            out = _run(argv, timeout_s=120)
            run_dir = _last_line_path(out)

    # Post-processing: normalize citations/evidence (if inputs exist) -> report -> reproducibility -> lint
    evidence_json = run_dir / "artifacts" / "evidence.json"
    results_json = run_dir / "artifacts" / "results.json"

    normalize = workspace / "skills" / "scienceclaw_citation_normalize" / "run.py"
    if normalize.exists() and (evidence_json.exists() or results_json.exists()):
        argv = [sys.executable, str(normalize), "--run-dir", str(run_dir), "--project", args.project, "--no-llm"]
        if results_json.exists():
            argv += ["--results-json", str(results_json)]
        if evidence_json.exists():
            argv += ["--evidence-json", str(evidence_json)]
        _run(argv, timeout_s=120)

    report = workspace / "skills" / "scienceclaw_report_compose_md" / "run.py"
    if report.exists():
        _run([sys.executable, str(report), "--run-dir", str(run_dir), "--no-llm"], timeout_s=60)

    repro = workspace / "skills" / "scienceclaw_repro_export" / "run.py"
    if repro.exists():
        _run([sys.executable, str(repro), "--run-dir", str(run_dir), "--source-run-dir", str(run_dir), "--no-llm"], timeout_s=60)

    lint = workspace / "skills" / "scienceclaw_bundle_lint" / "run.py"
    if lint.exists():
        proc = subprocess.Popen(
            [sys.executable, str(lint), "--run-dir", str(run_dir), "--profile", "auto", "--no-llm"] + (["--strict"] if args.strict else []),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=os.environ.copy(),
            text=True,
        )
        out, _ = proc.communicate(timeout=60)
        if proc.returncode != 0:
            # Strict lint is a hard gate when requested.
            raise SystemExit(f"bundle_lint failed (rc={proc.returncode}):\n" + (out or ""))

    print(str(run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
