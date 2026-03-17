from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import append_command, init_run, record_artifact  # noqa: E402


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _split_lines(text: str) -> List[str]:
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]


def _is_heading(line: str) -> Optional[str]:
    s = re.sub(r"\\s+", " ", line.strip())
    if len(s) < 3 or len(s) > 80:
        return None
    low = s.lower()
    if re.match(r"^(abstract|introduction|background|methods|materials and methods|results|discussion|conclusion|references)\\b", low):
        return s
    if re.match(r"^\\d+(?:\\.\\d+)*\\s+\\S+", s):
        return s
    if s.endswith(":") and len(s) <= 60:
        return s.rstrip(":").strip()
    # Uppercase-ish headings (common in PDFs)
    letters = [c for c in s if c.isalpha()]
    if letters and sum(1 for c in letters if c.isupper()) / max(1, len(letters)) > 0.85 and len(letters) >= 6:
        return s
    return None


def _detect_sections(pages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    sections: List[Dict[str, Any]] = []
    page_section: Dict[int, str] = {}

    for p in pages:
        page_no = int(p.get("page") or 0)
        lines = _split_lines(p.get("text") or "")
        title = None
        for ln in lines[:12]:
            title = _is_heading(ln)
            if title:
                break
        if title:
            sections.append(
                {
                    "title": title,
                    "startPage": page_no,
                    "endPage": page_no,
                    "heuristic": "heading",
                }
            )

    # De-dupe adjacent same titles, and fill endPage.
    compact: List[Dict[str, Any]] = []
    for s in sections:
        if compact and compact[-1]["title"].strip().lower() == s["title"].strip().lower():
            continue
        compact.append(s)
    sections = compact

    if sections:
        for i in range(len(sections) - 1):
            sections[i]["endPage"] = max(sections[i]["startPage"], sections[i + 1]["startPage"] - 1)
        sections[-1]["endPage"] = max(sections[-1]["startPage"], max((p.get("page") or 0) for p in pages))

        for s in sections:
            for page_no in range(int(s["startPage"]), int(s["endPage"]) + 1):
                page_section[page_no] = str(s["title"])

    pages_out: List[Dict[str, Any]] = []
    for p in pages:
        page_no = int(p.get("page") or 0)
        pages_out.append({"page": page_no, "text": p.get("text") or "", "section": page_section.get(page_no)})
    return pages_out, sections


def _extract_pdf_pages(pdf_path: Path) -> List[Dict[str, Any]]:
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
    return pages


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", action="append", required=True, help="Local PDF path (repeatable).")
    ap.add_argument("--project", default="default")
    # Standard flag across ScienceClaw skills. This skill doesn't call an LLM.
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument(
        "--workspace",
        default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")),
    )
    args = ap.parse_args()

    raw_pdfs = [str(p) for p in (args.pdf or [])]
    ctx = init_run(
        workspace_dir=Path(args.workspace),
        project=args.project,
        task="scienceclaw_pdf_extract_structured",
        inputs={"pdf": raw_pdfs, "noLlm": bool(args.no_llm)},
    )
    append_command(ctx, sys.argv[:])

    log_path = ctx.logs_dir / "extract.log"
    ok_files: List[Dict[str, Any]] = []
    missing: List[str] = []
    failed: List[str] = []

    for p in raw_pdfs:
        pdf_path = Path(p).expanduser().resolve()
        if not pdf_path.exists():
            missing.append(str(pdf_path))
            continue

        try:
            pages_raw = _extract_pdf_pages(pdf_path)
            pages, sections = _detect_sections(pages_raw)
            ok_files.append(
                {
                    "path": str(pdf_path),
                    "sha256": _sha256_file(pdf_path),
                    "pages": pages,
                    "sections": sections,
                }
            )
        except Exception:
            failed.append(str(pdf_path))

    log_lines: List[str] = []
    log_lines.append(f"inputs={len(raw_pdfs)}")
    log_lines.append(f"ok={len(ok_files)}")
    log_lines.append(f"missing={len(missing)}")
    log_lines.append(f"failed={len(failed)}")
    if missing:
        log_lines.append("missing_paths=" + json.dumps(missing, ensure_ascii=True))
    if failed:
        log_lines.append("failed_paths=" + json.dumps(failed, ensure_ascii=True))
    log_path.write_text("\n".join(log_lines).strip() + "\n", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"step": "extract"})

    out_path = ctx.artifacts_dir / "extracted.json"
    out: Dict[str, Any] = {
        "schemaVersion": 1,
        "files": ok_files,
        "meta": {
            "fileCount": len(ok_files),
            "requestedCount": len(raw_pdfs),
            "missingCount": len(missing),
            "failedCount": len(failed),
            "contentSha256": _sha256_bytes(json.dumps(ok_files, ensure_ascii=True, sort_keys=True).encode("utf-8")),
        },
    }
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, out_path, kind="pdf.extracted.structured", meta={"files": len(ok_files)})

    print(str(ctx.run_dir))
    if not ok_files:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
