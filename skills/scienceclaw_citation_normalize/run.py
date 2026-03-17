from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from normalize import (  # noqa: E402
    dedupe_evidence,
    normalize_source,
    sources_from_evidence,
    sources_from_results,
    to_bibtex,
    to_ris,
)
from run_context import init_run, record_artifact  # noqa: E402
from run_context import attach_run  # noqa: E402


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def _bibtex_placeholder() -> str:
    # Keep citations non-empty for downstream tooling and for product consistency.
    year = time.gmtime().tm_year
    return (
        "@misc{scienceclaw_missing_citations,\n"
        "  title = {ScienceClaw Citations Placeholder},\n"
        f"  year = {{{year}}},\n"
        "  note = {No citation sources were detected from results/evidence; replace with real citations},\n"
        "}\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-json", type=str, default="")
    ap.add_argument("--evidence-json", type=str, default="")
    ap.add_argument(
        "--run-dir",
        type=str,
        default="",
        help="Attach outputs to an existing run bundle directory (workflow mode).",
    )
    ap.add_argument("--ris", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--project", default="default")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    if not args.results_json and not args.evidence_json:
        raise SystemExit("must provide at least one of: --results-json, --evidence-json")

    workspace = Path(args.workspace)
    inputs: Dict[str, Any] = {
        "resultsJson": args.results_json,
        "evidenceJson": args.evidence_json,
        "runDir": args.run_dir,
        "ris": bool(args.ris),
        "noLlm": bool(args.no_llm),
    }
    if args.run_dir:
        ctx = attach_run(run_dir=Path(args.run_dir), task_hint="scienceclaw_citation_normalize", inputs_update=inputs)
    else:
        ctx = init_run(workspace_dir=workspace, project=args.project, task="scienceclaw_citation_normalize", inputs=inputs)

    normalize_log: List[str] = []

    results: Optional[Dict[str, Any]] = None
    if args.results_json:
        p = Path(args.results_json).expanduser()
        results = _read_json(p)
        normalize_log.append(f"loaded results: {p}")

    evidence: Optional[List[Dict[str, Any]]] = None
    evidence_stats: Optional[Dict[str, Any]] = None
    if args.evidence_json:
        p = Path(args.evidence_json).expanduser()
        raw = _read_json(p)
        if not isinstance(raw, list):
            raise SystemExit("evidence.json must be a JSON array (EvidenceItem[]) in v1")
        evidence = [x for x in raw if isinstance(x, dict)]
        normalize_log.append(f"loaded evidence: {p} items={len(evidence)}")
        evidence, evidence_stats = dedupe_evidence(evidence)
        normalize_log.append(f"evidence dedupe: {evidence_stats}")
        dedup_path = ctx.artifacts_dir / "evidence.deduped.json"
        dedup_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        record_artifact(ctx, dedup_path, kind="evidence.deduped", meta=evidence_stats)

    src_meta: Dict[str, Dict[str, Any]] = {}
    if results is not None:
        src_meta.update(sources_from_results(results))
    if evidence is not None:
        # Merge evidence-derived metadata without overriding richer results-derived fields.
        for canon, meta in sources_from_evidence(evidence).items():
            if canon not in src_meta:
                src_meta[canon] = meta
            else:
                for k, v in meta.items():
                    if k not in src_meta[canon] or not src_meta[canon].get(k):
                        src_meta[canon][k] = v

    # Build normalized citation list.
    citations: List[Dict[str, Any]] = []
    for canon, meta in src_meta.items():
        sn = normalize_source(canon)
        citations.append({"canonical": sn.canonical, "kind": sn.kind, "meta": meta})
    citations = sorted(citations, key=lambda x: x["canonical"])

    bib_path = ctx.artifacts_dir / "citations.bib"
    if citations:
        bib_path.write_text(to_bibtex(citations), encoding="utf-8")
        record_artifact(ctx, bib_path, kind="citations.bib", meta={"count": len(citations), "mode": "generated"})
    else:
        # Avoid clobbering an already-valid citations.bib produced upstream (e.g. PDF workflow).
        if bib_path.exists() and bib_path.stat().st_size > 0:
            record_artifact(ctx, bib_path, kind="citations.bib", meta={"count": 0, "mode": "kept_existing"})
        else:
            bib_path.write_text(_bibtex_placeholder(), encoding="utf-8")
            record_artifact(ctx, bib_path, kind="citations.bib", meta={"count": 0, "mode": "placeholder"})

    if args.ris:
        ris_path = ctx.artifacts_dir / "citations.ris"
        # If citations are empty, emit an empty RIS file but keep it explicit.
        ris_path.write_text(to_ris(citations), encoding="utf-8")
        record_artifact(ctx, ris_path, kind="citations.ris", meta={"count": len(citations), "mode": "generated"})

    normalized_path = ctx.artifacts_dir / "citations.normalized.json"
    normalized_path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "inputs": inputs,
                "counts": {"citations": len(citations)},
                "evidenceDedupe": evidence_stats,
                "citations": citations,
            },
            indent=2,
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    record_artifact(ctx, normalized_path, kind="citations.normalized", meta={"count": len(citations)})

    log_path = ctx.logs_dir / "normalize.log"
    log_path.write_text("\n".join(normalize_log) + "\n", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"step": "normalize"})

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
