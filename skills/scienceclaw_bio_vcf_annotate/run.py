from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import append_command, attach_run, init_run, record_artifact  # noqa: E402


def _open_text(path: Path):
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def _now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append_evidence(run_dir: Path, items: List[Dict[str, Any]]) -> int:
    p = run_dir / "artifacts" / "evidence.json"
    existing: List[Any] = []
    if p.exists():
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                existing = raw
        except Exception:
            existing = []
    merged = [x for x in existing if isinstance(x, dict)]
    merged.extend([x for x in items if isinstance(x, dict)])
    p.write_text(json.dumps(merged, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return len(merged)


def _parse_info(info: str, *, max_keys: int = 40) -> Dict[str, str]:
    out: Dict[str, str] = {}
    s = (info or "").strip()
    if not s or s == ".":
        return out
    for part in s.split(";"):
        if len(out) >= max_keys:
            break
        if not part:
            continue
        if "=" not in part:
            out[part] = "true"
            continue
        k, v = part.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k:
            out[k] = v
    return out


def annotate_vcf_to_rows(vcf_path: Path, *, limit: int) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]]]:
    rows: List[Dict[str, Any]] = []
    contigs: Dict[str, int] = {}
    multiallelic = 0
    skipped = 0
    col_header_seen = False

    evidence: List[Dict[str, Any]] = []
    evidence.append(
        {
            "source": f"file:{str(vcf_path)}",
            "locator": "header",
            "quote": f"VCF annotate input: {vcf_path.name} (offline baseline, limit={limit})",
            "usedIn": ["p3/vcf/annotate"],
        }
    )

    with _open_text(vcf_path) as f:
        for line_no, line in enumerate(f, start=1):
            ln = line.rstrip("\n")
            if ln.startswith("##"):
                continue
            if ln.startswith("#"):
                if ln.startswith("#CHROM"):
                    col_header_seen = True
                continue
            if not ln.strip():
                continue
            if not col_header_seen:
                # Tolerate missing header but keep evidence.
                col_header_seen = True
            parts = ln.split("\t")
            if len(parts) < 8:
                skipped += 1
                continue
            chrom, pos, _id, ref, alt, qual, flt, info = parts[:8]
            contigs[chrom] = contigs.get(chrom, 0) + 1
            if "," in alt:
                multiallelic += 1
            info_kv = _parse_info(info)

            # Minimal "annotation": we only normalize into structured fields.
            row: Dict[str, Any] = {
                "chrom": chrom,
                "pos": int(pos) if pos.isdigit() else pos,
                "id": _id,
                "ref": ref,
                "alt": alt,
                "qual": qual,
                "filter": flt,
                "info": info,
            }
            # Common useful INFO keys if present
            for k in ["RSID", "dbSNP", "CLNSIG", "CLNREVSTAT", "AF", "AC", "AN"]:
                if k in info_kv:
                    row[k.lower()] = info_kv[k]

            if len(rows) < limit:
                rows.append(row)
                if len(rows) <= 5:
                    evidence.append(
                        {
                            "source": f"file:{str(vcf_path)}",
                            "locator": f"line:{line_no}",
                            "quote": f"{chrom}:{pos} {ref}>{alt} FILTER={flt}",
                            "usedIn": ["p3/vcf/annotate.preview"],
                        }
                    )
            else:
                skipped += 1

    summary = {
        "schemaVersion": 1,
        "createdAt": _now_utc(),
        "vcf": str(vcf_path),
        "counts": {"exported": len(rows), "skipped": skipped, "contigs": len(contigs), "multiallelic": multiallelic},
        "contigsTop": sorted([{"contig": k, "variants": v} for k, v in contigs.items()], key=lambda x: (-x["variants"], x["contig"]))[:20],
    }
    return rows, summary, evidence


def _write_tsv(path: Path, rows: List[Dict[str, Any]]) -> None:
    # Keep a stable column order for downstream consumers.
    cols = ["chrom", "pos", "id", "ref", "alt", "qual", "filter", "info", "rsid", "dbsnp", "clnsig", "clnrevstat", "af", "ac", "an"]
    lines: List[str] = ["\t".join(cols)]
    for r in rows:
        parts: List[str] = []
        for c in cols:
            v = r.get(c)
            if v is None:
                parts.append("")
            else:
                parts.append(str(v))
        lines.append("\t".join(parts))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vcf", required=True)
    ap.add_argument("--limit", type=int, default=5000)
    ap.add_argument("--run-dir", default="", help="Attach outputs to an existing run bundle directory (workflow mode).")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--project", default="default")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    vcf_path = Path(args.vcf).expanduser().resolve()
    if not vcf_path.exists() or not vcf_path.is_file():
        raise SystemExit(f"vcf not found: {vcf_path}")

    limit = int(args.limit)
    if limit <= 0:
        raise SystemExit("--limit must be > 0")

    inputs: Dict[str, Any] = {"vcf": str(vcf_path), "limit": limit, "runDir": args.run_dir, "noLlm": bool(args.no_llm)}
    if args.run_dir:
        ctx = attach_run(run_dir=Path(args.run_dir), task_hint="scienceclaw_bio_vcf_annotate", inputs_update=inputs)
    else:
        ctx = init_run(workspace_dir=workspace, project=args.project, task="scienceclaw_bio_vcf_annotate", inputs=inputs)
    append_command(ctx, sys.argv[:])

    rows, summary, evidence = annotate_vcf_to_rows(vcf_path, limit=limit)

    tsv_path = ctx.artifacts_dir / "variants.annotated.tsv"
    _write_tsv(tsv_path, rows)
    record_artifact(ctx, tsv_path, kind="variants.annotated.tsv", meta={"rows": len(rows), "limit": limit})

    json_path = ctx.artifacts_dir / "variants.annotated.json"
    json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, json_path, kind="variants.annotated.json", meta={"rows": len(rows)})

    summary_path = ctx.artifacts_dir / "variants.summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, summary_path, kind="variants.summary.json", meta=summary.get("counts"))

    count = _append_evidence(ctx.run_dir, evidence)
    ev_path = ctx.artifacts_dir / "evidence.json"
    record_artifact(ctx, ev_path, kind="evidence", meta={"mode": "append", "count": count})

    log_path = ctx.logs_dir / "vcf_annotate.log"
    log_path.write_text(f"vcf={vcf_path}\nexported={len(rows)} skipped={summary['counts']['skipped']}\n", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"step": "vcf_annotate"})

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

