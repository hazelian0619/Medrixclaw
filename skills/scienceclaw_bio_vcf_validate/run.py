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


def _now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def validate_vcf(vcf_path: Path, *, max_preview: int = 5) -> Tuple[Dict[str, Any], List[Dict[str, Any]], str]:
    errors: List[str] = []
    warnings: List[str] = []

    fileformat = ""
    header_lines = 0
    col_header: Optional[str] = None
    samples: List[str] = []

    variants = 0
    contigs: Dict[str, int] = {}
    multiallelic = 0
    preview: List[Dict[str, Any]] = []

    with _open_text(vcf_path) as f:
        for line_no, line in enumerate(f, start=1):
            ln = line.rstrip("\n")
            if ln.startswith("##"):
                header_lines += 1
                if ln.lower().startswith("##fileformat="):
                    fileformat = ln.split("=", 1)[1].strip()
                continue
            if ln.startswith("#"):
                # #CHROM line
                col_header = ln
                parts = ln.lstrip("#").split("\t")
                if len(parts) >= 8 and parts[:8] == ["CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO"]:
                    if len(parts) > 9:
                        samples = parts[9:]
                else:
                    warnings.append("unexpected column header (not standard VCF columns)")
                continue

            # Variant record
            if not ln.strip():
                continue
            parts = ln.split("\t")
            if len(parts) < 8:
                errors.append(f"line {line_no}: expected >=8 TAB-separated columns, got {len(parts)}")
                continue
            chrom, pos, _id, ref, alt, qual, flt, info = parts[:8]
            variants += 1
            contigs[chrom] = contigs.get(chrom, 0) + 1
            if "," in alt:
                multiallelic += 1
            if len(preview) < max_preview:
                preview.append(
                    {
                        "line": line_no,
                        "chrom": chrom,
                        "pos": pos,
                        "id": _id,
                        "ref": ref,
                        "alt": alt,
                        "qual": qual,
                        "filter": flt,
                        "info": info[:200],
                    }
                )

    if not fileformat:
        warnings.append("missing ##fileformat header")
    if not col_header:
        errors.append("missing #CHROM header line")
    if variants == 0:
        warnings.append("no variant records detected")

    stats: Dict[str, Any] = {
        "schemaVersion": 1,
        "createdAt": _now_utc(),
        "vcf": str(vcf_path),
        "fileformat": fileformat,
        "headerLines": header_lines,
        "samples": samples,
        "counts": {
            "variants": variants,
            "contigs": len(contigs),
            "multiallelic": multiallelic,
        },
        "contigsTop": sorted([{"contig": k, "variants": v} for k, v in contigs.items()], key=lambda x: (-x["variants"], x["contig"]))[:20],
        "preview": preview,
        "errors": errors,
        "warnings": warnings,
        "ok": len(errors) == 0,
    }

    evidence: List[Dict[str, Any]] = []
    # Always record the input file as evidence (for provenance).
    evidence.append(
        {
            "source": f"file:{str(vcf_path)}",
            "locator": "header",
            "quote": f"VCF validate input: {vcf_path.name} (fileformat={fileformat or 'unknown'})",
            "usedIn": ["p3/vcf/validate"],
        }
    )
    for it in preview:
        evidence.append(
            {
                "source": f"file:{str(vcf_path)}",
                "locator": f"line:{it.get('line')}",
                "quote": f"{it.get('chrom')}:{it.get('pos')} {it.get('ref')}>{it.get('alt')} FILTER={it.get('filter')}",
                "usedIn": ["p3/vcf/preview"],
            }
        )

    log = "\n".join(
        [
            f"vcf={vcf_path}",
            f"fileformat={fileformat}",
            f"variants={variants}",
            f"samples={len(samples)}",
            f"errors={len(errors)} warnings={len(warnings)}",
        ]
    )
    return stats, evidence, log + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vcf", required=True)
    ap.add_argument("--run-dir", default="", help="Attach outputs to an existing run bundle directory (workflow mode).")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--project", default="default")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    vcf_path = Path(args.vcf).expanduser().resolve()
    if not vcf_path.exists() or not vcf_path.is_file():
        raise SystemExit(f"vcf not found: {vcf_path}")

    inputs: Dict[str, Any] = {"vcf": str(vcf_path), "runDir": args.run_dir, "noLlm": bool(args.no_llm)}
    if args.run_dir:
        ctx = attach_run(run_dir=Path(args.run_dir), task_hint="scienceclaw_bio_vcf_validate", inputs_update=inputs)
    else:
        ctx = init_run(workspace_dir=workspace, project=args.project, task="scienceclaw_bio_vcf_validate", inputs=inputs)
    append_command(ctx, sys.argv[:])

    stats, evidence, log_text = validate_vcf(vcf_path)
    stats_path = ctx.artifacts_dir / "vcf.stats.json"
    stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, stats_path, kind="vcf.stats", meta={"ok": bool(stats.get("ok")), "variants": stats.get("counts", {}).get("variants")})

    count = _append_evidence(ctx.run_dir, evidence)
    ev_path = ctx.artifacts_dir / "evidence.json"
    record_artifact(ctx, ev_path, kind="evidence", meta={"mode": "append", "count": count})

    log_path = ctx.logs_dir / "vcf_validate.log"
    log_path.write_text(log_text, encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"step": "vcf_validate"})

    # Fail if structurally invalid (errors) even in non-strict mode: validation is a gate.
    if not stats.get("ok"):
        raise SystemExit(f"vcf validation failed; see artifacts/vcf.stats.json in runDir: {ctx.run_dir}")

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

