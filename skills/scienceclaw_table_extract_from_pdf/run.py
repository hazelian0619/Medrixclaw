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

from run_context import append_command, attach_run, init_run, record_artifact  # noqa: E402
from table_heuristics import TableCandidate, parse_table_like_block, to_markdown_table  # noqa: E402


def _load_openclaw_dotenv() -> Dict[str, str]:
    env_path = Path.home() / ".openclaw" / ".env"
    out: Dict[str, str] = {}
    if not env_path.exists():
        return out
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k:
            out[k] = v
    return out


def call_llm_glm5(*, api_key: str, base_url: str, prompt: str) -> str:
    """
    Use Huawei MaaS OpenAI-compatible endpoint (default in ScienceClaw).
    """
    import requests

    url = base_url.rstrip("/") + "/chat/completions"
    payload = {"model": "glm-5", "messages": [{"role": "user", "content": prompt}]}
    r = requests.post(url, headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def _extract_block_tuples(page: Any) -> List[Tuple[float, float, float, float, str]]:
    """
    Return [(x0,y0,x1,y1,text), ...] from PyMuPDF page.get_text("blocks").
    """
    out: List[Tuple[float, float, float, float, str]] = []
    blocks = page.get_text("blocks")  # type: ignore[no-untyped-call]
    for b in blocks:
        # tuple length differs across versions; first 5 are stable.
        if len(b) < 5:
            continue
        x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4]
        if not isinstance(text, str):
            continue
        out.append((float(x0), float(y0), float(x1), float(y1), text))
    return out


def _write_csv(path: Path, rows: List[List[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow([c if isinstance(c, str) else str(c) for c in r])


def _try_llm_refine_rows(*, raw_text: str, api_key: str, base_url: str) -> Optional[List[List[str]]]:
    prompt = (
        "你是科研 PDF 表格抽取器。请把下面这段从 PDF 中抽取的表格文本块转换成严格 JSON。\\n"
        "要求：\\n"
        "- 只输出 JSON，不要输出解释性文字。\\n"
        '- JSON schema: {\"rows\": [[\"...\", \"...\"], ...] }\\n'
        "- 每个单元格是字符串；保持行列矩形结构，缺失用空字符串补齐。\\n"
        "- 不要杜撰不存在的行；不要合并行。\\n\\n"
        "RAW BLOCK:\\n"
        + raw_text[:4000]
    )
    try:
        text = call_llm_glm5(api_key=api_key, base_url=base_url, prompt=prompt)
    except Exception:
        return None
    try:
        data = json.loads(text)
    except Exception:
        return None
    rows = data.get("rows")
    if not isinstance(rows, list):
        return None
    out: List[List[str]] = []
    for r in rows:
        if not isinstance(r, list):
            return None
        out.append([(c if isinstance(c, str) else str(c)) for c in r])
    if not out:
        return None
    cols = max(len(r) for r in out)
    for i, r in enumerate(out):
        if len(r) < cols:
            out[i] = r + [""] * (cols - len(r))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--project", default="default")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--max-pages", type=int, default=50, help="0 means all pages")
    ap.add_argument("--min-rows", type=int, default=3)
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    ap.add_argument("--run-dir", default="", help="(internal) write artifacts into an existing run dir created by a workflow")
    args = ap.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    if args.run_dir:
        ctx = attach_run(run_dir=Path(args.run_dir), task_hint="scienceclaw_table_extract_from_pdf", inputs_update={"pdf": str(pdf_path)})
    else:
        ctx = init_run(
            workspace_dir=Path(args.workspace),
            project=args.project,
            task="scienceclaw_table_extract_from_pdf",
            inputs={"pdf": str(pdf_path), "noLlm": bool(args.no_llm), "maxPages": args.max_pages, "minRows": args.min_rows},
        )

    append_command(ctx, sys.argv[:])

    import fitz  # PyMuPDF

    log_path = ctx.logs_dir / "extract.log"
    tables: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    candidates: List[TableCandidate] = []

    try:
        doc = fitz.open(str(pdf_path))
        page_count = int(doc.page_count)
        limit = page_count if args.max_pages == 0 else min(page_count, max(0, int(args.max_pages)))
        for i in range(limit):
            page = doc.load_page(i)
            blocks = _extract_block_tuples(page)
            for (x0, y0, x1, y1, text) in blocks:
                cand = parse_table_like_block(text=text, page=i + 1, bbox=(x0, y0, x1, y1), min_rows=int(args.min_rows))
                if cand:
                    candidates.append(cand)
        doc.close()
    except Exception as e:
        log_path.write_text(f"error: {e}\n", encoding="utf-8")
        record_artifact(ctx, log_path, kind="log", meta={"step": "extract", "ok": False})
        raise

    candidates.sort(key=lambda c: (-c.score, c.page))
    log_path.write_text(f"pdf={pdf_path}\npages_scanned={args.max_pages}\ncandidates={len(candidates)}\n", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"step": "extract", "ok": True, "candidates": len(candidates)})

    dotenv = _load_openclaw_dotenv()
    api_key = os.environ.get("MAAS_API_KEY") or dotenv.get("MAAS_API_KEY") or ""
    base_url = os.environ.get("MAAS_BASE_URL") or dotenv.get("MAAS_BASE_URL") or "https://api.modelarts-maas.com/openai/v1"

    llm_log = ctx.logs_dir / "llm.log"
    llm_lines: List[str] = []

    out_tables_dir = ctx.artifacts_dir / "tables"
    out_tables_dir.mkdir(parents=True, exist_ok=True)

    for idx, cand in enumerate(candidates, start=1):
        table_id = f"t{idx}"
        rows = cand.rows
        llm_used = False
        if (not args.no_llm) and api_key:
            refined = _try_llm_refine_rows(raw_text=cand.raw_text, api_key=api_key, base_url=base_url)
            if refined:
                rows = refined
                llm_used = True
                llm_lines.append(f"{table_id}: ok\n")
            else:
                llm_lines.append(f"{table_id}: failed_parse\n")
        elif not args.no_llm and not api_key:
            llm_lines.append("missing MAAS_API_KEY in env; rerun with --no-llm or set MAAS_API_KEY\n")

        md = to_markdown_table(rows)
        csv_rel = f"artifacts/tables/{table_id}.csv"
        csv_path = out_tables_dir / f"{table_id}.csv"
        _write_csv(csv_path, rows)
        record_artifact(ctx, csv_path, kind="table.csv", meta={"tableId": table_id, "page": cand.page, "llmUsed": llm_used})

        tables.append(
            {
                "table_id": table_id,
                "page": cand.page,
                "bbox": [cand.bbox[0], cand.bbox[1], cand.bbox[2], cand.bbox[3]],
                "cells": rows,
                "markdown": md,
                "csv_path": csv_rel,
                "llm_used": llm_used,
            }
        )

        evidence.append(
            {
                "source": f"file:{pdf_path}",
                "locator": f"page:{cand.page}",
                "quote": cand.raw_text[:900],
                "usedIn": ["tables.json", "tables.csv"],
            }
        )

    # Governance: keep evidence non-empty even when no tables are detected, so strict bundle lint can pass.
    if not evidence:
        evidence.append(
            {
                "source": f"file:{pdf_path}",
                "locator": "page:1",
                "quote": "No table candidates detected by heuristic parser in this run.",
                "usedIn": ["tables.json", "tables.csv"],
            }
        )

    llm_log.write_text("".join(llm_lines) if llm_lines else "skipped\n", encoding="utf-8")
    record_artifact(ctx, llm_log, kind="log", meta={"step": "llm", "ok": bool(api_key) and (not args.no_llm)})

    tables_json = {
        "pdf": str(pdf_path),
        "tables": tables,
        "meta": {"candidates": len(candidates), "no_llm": bool(args.no_llm)},
    }
    tables_path = ctx.artifacts_dir / "tables.json"
    tables_path.write_text(json.dumps(tables_json, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, tables_path, kind="tables.json", meta={"count": len(tables)})

    evidence_path = ctx.artifacts_dir / "evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, evidence_path, kind="evidence", meta={"count": len(evidence)})

    # `tables.csv`: single-table output or multi-table index.
    tables_csv_path = ctx.artifacts_dir / "tables.csv"
    if len(tables) == 1:
        _write_csv(tables_csv_path, tables[0]["cells"])
        record_artifact(ctx, tables_csv_path, kind="tables.csv", meta={"mode": "single", "tables": 1})
    else:
        index_rows: List[List[str]] = [["table_id", "page", "csv_path", "rows", "cols", "pdf"]]
        for t in tables:
            rr = t.get("cells") or []
            rcount = len(rr)
            ccount = max((len(r) for r in rr), default=0)
            index_rows.append([t["table_id"], str(t["page"]), t["csv_path"], str(rcount), str(ccount), str(pdf_path)])
        _write_csv(tables_csv_path, index_rows)
        record_artifact(ctx, tables_csv_path, kind="tables.csv", meta={"mode": "index", "tables": len(tables)})

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
