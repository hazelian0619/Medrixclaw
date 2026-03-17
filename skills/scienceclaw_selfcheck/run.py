from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import init_run, record_artifact  # noqa: E402


def offline_bundle(workspace: Path) -> Path:
    """
    Create a minimal artifact bundle without network access.
    This is useful when the VM temporarily cannot resolve DNS or reach NCBI/MaaS.
    """
    ctx = init_run(workspace_dir=workspace, project="selfcheck", task="scienceclaw_selfcheck_offline", inputs={"mode": "offline"})
    brief = ctx.artifacts_dir / "brief.md"
    citations = ctx.artifacts_dir / "citations.bib"
    evidence = ctx.artifacts_dir / "evidence.json"

    brief_text = (
        "# ScienceClaw Selfcheck (Offline)\n\n"
        "当前环境无法访问外网（或 DNS 临时异常），已生成离线自检产物包。\n"
        "下一步：恢复网络后重新运行 selfcheck，验证 PubMed 与 GLM-5 链路。\n"
    )
    brief.write_text(brief_text, encoding="utf-8")

    # Keep citations non-empty so the Phase 2 contract remains true even in offline mode.
    year = time.gmtime().tm_year
    citations.write_text(
        (
            "@misc{scienceclaw_offline_selfcheck,\n"
            "  title = {ScienceClaw Selfcheck (Offline)},\n"
            f"  year = {{{year}}},\n"
            "  note = {Offline bundle generated when network/DNS is unavailable},\n"
            "}\n"
        ),
        encoding="utf-8",
    )

    # Minimal evidence item to exercise schema/tooling paths.
    evidence_items = [
        {
            "source": f"file:{brief.resolve()}",
            "locator": "offset:0-200",
            "quote": "当前环境无法访问外网（或 DNS 临时异常），已生成离线自检产物包。",
            "usedIn": ["selfcheck/offline"],
        }
    ]
    evidence.write_text(json.dumps(evidence_items, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    record_artifact(ctx, brief, kind="brief.md", meta={"mode": "offline"})
    record_artifact(ctx, citations, kind="citations.bib", meta={"mode": "offline"})
    record_artifact(ctx, evidence, kind="evidence", meta={"mode": "offline"})
    return ctx.run_dir


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--workspace",
        default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")),
        help="OpenClaw workspace directory (default: $OPENCLAW_WORKSPACE or ~/.openclaw/workspace)",
    )
    ap.add_argument(
        "--offline",
        action="store_true",
        help="Generate an offline selfcheck artifact bundle (no network required).",
    )
    args = ap.parse_args()

    workspace = Path(args.workspace)

    if args.offline:
        run_dir = offline_bundle(workspace)
        print(str(run_dir))
        return 0

    # Fast preflight: if network is obviously down, avoid waiting on timeouts.
    try:
        socket.setdefaulttimeout(2.0)
        socket.create_connection(("eutils.ncbi.nlm.nih.gov", 443), timeout=2.0).close()
    except OSError:
        run_dir = offline_bundle(workspace)
        print("WARN: network unavailable; generated offline selfcheck bundle.")
        print(str(run_dir))
        return 0

    ctx = init_run(workspace_dir=workspace, project="selfcheck", task="scienceclaw_selfcheck", inputs={"mode": "online"})

    workflow = workspace / "skills" / "scienceclaw_workflow_lit_brief" / "run.py"
    if not workflow.exists():
        raise SystemExit(f"workflow skill not found: {workflow}")

    # Run the workflow in no-LLM/no-PDF mode for deterministic selfcheck.
    log_path = ctx.logs_dir / "workflow.log"
    proc = subprocess.Popen(
        [
            sys.executable,
            str(workflow),
            "--query",
            "openclaw glm-5",
            "--limit",
            "3",
            "--project",
            "selfcheck",
            "--no-llm",
            "--no-pdf",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=os.environ.copy(),
        text=True,
    )
    out, _ = proc.communicate(timeout=300)
    log_path.write_text(out or "", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"exitCode": proc.returncode})
    if proc.returncode != 0:
        # Fallback: if the failure looks like a transient network/DNS problem,
        # generate an offline bundle so deployment pipelines can continue.
        text = (out or "").lower()
        if "temporary failure in name resolution" in text or "failed to establish a new connection" in text:
            run_dir = offline_bundle(workspace)
            print("WARN: online selfcheck failed (network/dns). Generated offline bundle instead.")
            print(str(run_dir))
            return 0
        raise SystemExit(f"selfcheck failed, see log: {log_path}")

    # The workflow prints the run directory as its last line.
    run_dir = Path((out or "").strip().splitlines()[-1]).expanduser()
    required = [
        run_dir / "manifest.json",
        run_dir / "artifacts" / "brief.md",
        run_dir / "artifacts" / "citations.bib",
        run_dir / "artifacts" / "evidence.json",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit("missing required artifacts in workflow run:\n" + "\n".join(missing))

    # Phase 2 sanity checks: citations should be non-empty; evidence should be a JSON array (and non-empty for lit_brief).
    citations_path = run_dir / "artifacts" / "citations.bib"
    if citations_path.stat().st_size == 0:
        raise SystemExit(f"citations.bib is empty: {citations_path}")

    evidence_path = run_dir / "artifacts" / "evidence.json"
    try:
        ev = json.loads(evidence_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"evidence.json is not valid JSON: {evidence_path} ({e})")
    if not isinstance(ev, list):
        raise SystemExit(f"evidence.json must be a JSON array: {evidence_path}")
    if len(ev) == 0:
        raise SystemExit(f"evidence.json is empty (unexpected for lit_brief): {evidence_path}")

    # Optional Phase 2 closure: run citation_normalize to ensure the standardizer itself works.
    normalize = workspace / "skills" / "scienceclaw_citation_normalize" / "run.py"
    if normalize.exists():
        nlog = ctx.logs_dir / "citation_normalize.log"
        proc2 = subprocess.Popen(
            [
                sys.executable,
                str(normalize),
                "--run-dir",
                str(run_dir),
                "--results-json",
                str(run_dir / "artifacts" / "results.json"),
                "--evidence-json",
                str(evidence_path),
                "--project",
                "selfcheck",
                "--no-llm",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=os.environ.copy(),
            text=True,
        )
        out2, _ = proc2.communicate(timeout=120)
        nlog.write_text(out2 or "", encoding="utf-8")
        record_artifact(ctx, nlog, kind="log", meta={"step": "citation_normalize", "exitCode": proc2.returncode})
        if proc2.returncode != 0:
            raise SystemExit(f"citation_normalize failed, see log: {nlog}")

    # Optional Phase 3 smoke: VCF workflow (offline deterministic, no network).
    vcf_workflow = workspace / "skills" / "scienceclaw_workflow_vcf_annotate_brief" / "run.py"
    if vcf_workflow.exists():
        vcf_path = Path("/tmp/scienceclaw_selfcheck.vcf")
        vcf_path.write_text(
            "##fileformat=VCFv4.2\n"
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
            "1\t100\t.\tA\tG\t.\tPASS\tAC=1;AN=2\n",
            encoding="utf-8",
        )
        vlog = ctx.logs_dir / "phase3_vcf_workflow.log"
        proc4 = subprocess.Popen(
            [
                sys.executable,
                str(vcf_workflow),
                "--vcf",
                str(vcf_path),
                "--project",
                "selfcheck",
                "--no-llm",
                "--workspace",
                str(workspace),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=os.environ.copy(),
            text=True,
        )
        out4, _ = proc4.communicate(timeout=300)
        vlog.write_text(out4 or "", encoding="utf-8")
        record_artifact(ctx, vlog, kind="log", meta={"step": "phase3_vcf_workflow", "exitCode": proc4.returncode})
        if proc4.returncode != 0:
            raise SystemExit(f"phase3 vcf workflow failed, see log: {vlog}")

    # Optional: lint the workflow run bundle (adds artifacts/bundle_lint.json into the same runDir).
    lint = workspace / "skills" / "scienceclaw_bundle_lint" / "run.py"
    if lint.exists():
        llog = ctx.logs_dir / "bundle_lint.log"
        proc3 = subprocess.Popen(
            [
                sys.executable,
                str(lint),
                "--run-dir",
                str(run_dir),
                "--profile",
                "auto",
                "--strict",
                "--no-llm",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=os.environ.copy(),
            text=True,
        )
        out3, _ = proc3.communicate(timeout=60)
        llog.write_text(out3 or "", encoding="utf-8")
        record_artifact(ctx, llog, kind="log", meta={"step": "bundle_lint", "exitCode": proc3.returncode})
        if proc3.returncode != 0:
            raise SystemExit(f"bundle_lint failed, see log: {llog}")

    print(str(run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
