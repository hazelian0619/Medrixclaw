from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import attach_run, append_command, init_run, record_artifact  # noqa: E402


def _md_table(headers: List[str], rows: List[List[str]]) -> str:
    if not headers:
        return ""
    cols = len(headers)
    lines: List[str] = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * cols) + " |")
    for r in rows:
        rr = (r + [""] * cols)[:cols]
        lines.append("| " + " | ".join((c or "").replace("|", "\\|") for c in rr) + " |")
    return "\n".join(lines).strip() + "\n"


def _read_csv(path: Path, max_rows: int = 200) -> Tuple[List[str], List[List[str]]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.reader(f)
        headers: List[str] = []
        rows: List[List[str]] = []
        for i, row in enumerate(r):
            if i == 0:
                headers = [c.strip() for c in row]
                continue
            rows.append([c for c in row])
            if len(rows) >= max_rows:
                break
    return headers, rows


def _csv_to_json(path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        items = []
        for row in r:
            items.append({k: (v if v is not None else "") for k, v in row.items()})
    meta = {"rows": len(items), "columns": len(r.fieldnames or [])}
    return items, meta


def _json_to_csv(data: Any) -> Tuple[List[str], List[Dict[str, Any]]]:
    if not isinstance(data, list):
        raise SystemExit("json_to_csv requires a JSON array of objects")
    keys: List[str] = []
    rows: List[Dict[str, Any]] = []
    for it in data:
        if not isinstance(it, dict):
            continue
        rows.append(it)
        for k in it.keys():
            if k not in keys:
                keys.append(k)
    if not keys:
        raise SystemExit("json_to_csv: no object keys found")
    return keys, rows


def _pdf_to_text(pdf_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    import fitz  # PyMuPDF

    doc = fitz.open(str(pdf_path))
    pages: List[Dict[str, Any]] = []
    try:
        for i in range(doc.page_count):
            page = doc.load_page(i)
            text = page.get_text("text")
            pages.append({"page": i + 1, "text": text})
    finally:
        doc.close()
    meta = {"pages": len(pages)}
    return pages, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--mode", required=True, choices=["pdf_to_text", "csv_to_json", "json_to_csv", "json_pretty"])
    ap.add_argument("--project", default="default")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    ap.add_argument("--run-dir", default="", help="(internal) write artifacts into an existing run dir created by a workflow")
    args = ap.parse_args()

    in_path = Path(args.input).expanduser().resolve()
    if not in_path.exists():
        raise SystemExit(f"input not found: {in_path}")

    if args.run_dir:
        ctx = attach_run(run_dir=Path(args.run_dir), task_hint="scienceclaw_format_convert", inputs_update={"input": str(in_path), "mode": args.mode})
    else:
        ctx = init_run(
            workspace_dir=Path(args.workspace),
            project=args.project,
            task="scienceclaw_format_convert",
            inputs={"input": str(in_path), "mode": args.mode, "noLlm": bool(args.no_llm)},
        )

    append_command(ctx, sys.argv[:])

    log_lines: List[str] = []
    outputs: List[Dict[str, Any]] = []
    stats: Dict[str, Any] = {}

    try:
        if args.mode == "pdf_to_text":
            pages, meta = _pdf_to_text(in_path)
            out_json = ctx.artifacts_dir / "extracted.text.json"
            out_txt = ctx.artifacts_dir / "extracted.txt"
            out_json.write_text(json.dumps({"schemaVersion": 1, "source": str(in_path), "pages": pages}, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            out_txt.write_text("\n".join((p.get("text") or "") for p in pages).strip() + "\n", encoding="utf-8")
            record_artifact(ctx, out_json, kind="convert.pdf.text.json", meta=meta)
            record_artifact(ctx, out_txt, kind="convert.pdf.text", meta=meta)
            outputs.extend([{"path": str(out_json.relative_to(ctx.run_dir)), "kind": "json"}, {"path": str(out_txt.relative_to(ctx.run_dir)), "kind": "txt"}])
            stats.update(meta)

        elif args.mode == "csv_to_json":
            items, meta = _csv_to_json(in_path)
            out_json = ctx.artifacts_dir / "converted.json"
            out_json.write_text(json.dumps({"schemaVersion": 1, "source": str(in_path), "items": items}, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            record_artifact(ctx, out_json, kind="convert.csv.json", meta=meta)
            outputs.append({"path": str(out_json.relative_to(ctx.run_dir)), "kind": "json"})
            stats.update(meta)

            headers, rows = _read_csv(in_path, max_rows=20)
            prev = ctx.artifacts_dir / "preview.md"
            prev.write_text("# Preview (first 20 rows)\n\n" + _md_table(headers, rows) + "\n", encoding="utf-8")
            record_artifact(ctx, prev, kind="convert.preview.md", meta={"rows": min(len(rows), 20)})
            outputs.append({"path": str(prev.relative_to(ctx.run_dir)), "kind": "md"})

        elif args.mode == "json_to_csv":
            data = json.loads(in_path.read_text(encoding="utf-8"))
            keys, rows = _json_to_csv(data)
            out_csv = ctx.artifacts_dir / "converted.csv"
            with out_csv.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader()
                for r in rows:
                    w.writerow({k: (r.get(k) if r.get(k) is not None else "") for k in keys})
            record_artifact(ctx, out_csv, kind="convert.json.csv", meta={"rows": len(rows), "columns": len(keys)})
            outputs.append({"path": str(out_csv.relative_to(ctx.run_dir)), "kind": "csv"})
            stats.update({"rows": len(rows), "columns": len(keys)})

        elif args.mode == "json_pretty":
            data = json.loads(in_path.read_text(encoding="utf-8"))
            out_json = ctx.artifacts_dir / "pretty.json"
            out_json.write_text(json.dumps(data, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
            record_artifact(ctx, out_json, kind="convert.json.pretty", meta={})
            outputs.append({"path": str(out_json.relative_to(ctx.run_dir)), "kind": "json"})

        else:
            raise SystemExit(f"unsupported mode: {args.mode}")
    except Exception as e:
        log_lines.append(f"error: {e}")
        raise
    finally:
        log_path = ctx.logs_dir / "convert.log"
        if not log_lines:
            log_lines.append("ok")
        log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
        record_artifact(ctx, log_path, kind="log", meta={"step": "convert", "ok": True})

    conv = {
        "schemaVersion": 1,
        "input": {"path": str(in_path), "mode": args.mode},
        "outputs": outputs,
        "stats": stats,
    }
    conv_path = ctx.artifacts_dir / "conversion.json"
    conv_path.write_text(json.dumps(conv, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, conv_path, kind="convert.meta", meta={"outputs": len(outputs)})

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

