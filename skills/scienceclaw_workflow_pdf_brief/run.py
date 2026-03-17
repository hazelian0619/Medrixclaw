from __future__ import annotations

import argparse
import json
import hashlib
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import append_command, init_run, record_artifact  # noqa: E402


def _write_log(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


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
            sections.append({"title": title, "startPage": page_no, "endPage": page_no, "heuristic": "heading"})

    compact: List[Dict[str, Any]] = []
    for s in sections:
        if compact and compact[-1]["title"].strip().lower() == s["title"].strip().lower():
            continue
        compact.append(s)
    sections = compact

    if sections:
        last_page = max((p.get("page") or 0) for p in pages) if pages else 0
        for i in range(len(sections) - 1):
            sections[i]["endPage"] = max(sections[i]["startPage"], sections[i + 1]["startPage"] - 1)
        sections[-1]["endPage"] = max(sections[-1]["startPage"], last_page)
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
            pages.append({"page": i + 1, "text": page.get_text("text")})
    finally:
        doc.close()
    return pages


def _paragraph_candidates(text: str) -> List[str]:
    # Favor longer paragraphs; keep it deterministic.
    raw = (text or "").replace("\r\n", "\n")
    parts = [re.sub(r"\\s+", " ", p).strip() for p in re.split(r"\\n\\s*\\n", raw)]
    # Keep threshold low; evidence should exist even for short PDFs / slides.
    parts = [p for p in parts if len(p) >= 80]
    parts.sort(key=lambda s: (-len(s), s[:50]))
    return parts


def make_evidence_from_extracted(files: List[Dict[str, Any]], *, max_total: int = 24, per_page: int = 1) -> List[Dict[str, Any]]:
    evidence: List[Dict[str, Any]] = []
    for f in files:
        if len(evidence) >= max_total:
            break
        file_path = f.get("path") or ""
        pages = f.get("pages") or []
        for p in pages:
            if len(evidence) >= max_total:
                break
            page_no = int(p.get("page") or 0)
            text = p.get("text") or ""
            cands = _paragraph_candidates(text)
            if not cands:
                t = re.sub(r"\\s+", " ", text).strip()
                # Last-resort: take whatever exists (down to a small threshold),
                # otherwise the workflow can produce empty evidence on short PDFs.
                if len(t) >= 40:
                    cands = [t]
            for cand in cands[:per_page]:
                quote = cand[:900].strip()
                if not quote:
                    continue
                evidence.append(
                    {
                        "source": f"file:{file_path}",
                        "file": file_path,
                        "locator": f"page:{page_no};chars:0-{min(900, len(cand))}",
                        "page": page_no,
                        "quote": quote,
                        "usedIn": ["summary"],
                    }
                )
                if len(evidence) >= max_total:
                    break
    return evidence


def to_citations_bib(files: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for f in files:
        sha = (f.get("sha256") or "")[:12] or "unknown"
        path = f.get("path") or ""
        title_guess = ""
        pages = f.get("pages") or []
        if pages:
            first = (pages[0].get("text") or "").strip()
            if first:
                title_guess = _split_lines(first)[:1][0] if _split_lines(first) else ""
                title_guess = re.sub(r"[{}]", "", title_guess)[:120]
        key = f"file{sha}"
        lines.append(f"@misc{{{key},")
        if title_guess:
            lines.append(f"  title = {{{title_guess}}},")
        lines.append("  howpublished = {Local PDF},")
        if path:
            esc = path.replace("\\\\", "/")
            lines.append(f"  note = {{{esc} (SHA256:{f.get('sha256')})}}")
        lines.append("}\n")
    return "\n".join(lines)


def compose_brief_md(*, files: List[Dict[str, Any]], evidence: List[Dict[str, Any]], llm_summary: Optional[str]) -> str:
    lines: List[str] = []
    lines.append("# PDF -> Evidence -> Brief\n")
    lines.append(f"- 生成时间（UTC）: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}")
    lines.append(f"- 文件数: {len(files)}")
    lines.append(f"- 证据片段数: {len(evidence)}\n")

    if llm_summary:
        lines.append("## 摘要（模型生成，可选）\n")
        lines.append(llm_summary.strip())
        lines.append("")

    lines.append("## 输入文件\n")
    for i, f in enumerate(files, start=1):
        pages = f.get("pages") or []
        sections = f.get("sections") or []
        lines.append(f"{i}. `{f.get('path')}` (pages={len(pages)})")
        if sections:
            sec_titles = [str(s.get('title')) for s in sections[:10] if s.get("title")]
            if sec_titles:
                lines.append(f"   sections: {', '.join(sec_titles)}")
    lines.append("")

    lines.append("## 证据片段（Evidence）\n")
    for i, ev in enumerate(evidence, start=1):
        lines.append(f"### E{i} {ev.get('file')} {ev.get('locator')}")
        lines.append((ev.get("quote") or "").strip())
        lines.append("")

    lines.append("## 复盘与重跑\n")
    lines.append("本次 run 目录下包含 `extracted.json`（按页文本）与 `evidence.json`（带 file/page locator）。")
    lines.append("若要重跑，请使用相同的 `--pdf` 列表与 `--project`。\n")

    return "\n".join(lines).rstrip() + "\n"


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


def call_openai_compat(*, api_key: str, base_url: str, model: str, prompt: str) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        url,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"llm http {e.code}: {body[:400]}")
    except Exception as e:
        raise RuntimeError(f"llm request failed: {e}")
    return str(data["choices"][0]["message"]["content"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", action="append", required=True, help="Local PDF path (repeatable).")
    ap.add_argument("--project", default="default")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument(
        "--workspace",
        default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")),
    )
    args = ap.parse_args()

    raw_pdfs = [str(p) for p in (args.pdf or [])]
    workspace = Path(args.workspace)
    ctx = init_run(
        workspace_dir=workspace,
        project=args.project,
        task="scienceclaw_workflow_pdf_brief",
        inputs={"pdf": raw_pdfs, "noLlm": bool(args.no_llm)},
    )
    append_command(ctx, sys.argv[:])

    extract_log = ctx.logs_dir / "extract.log"
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

    _write_log(
        extract_log,
        "\n".join(
            [
                f"inputs={len(raw_pdfs)}",
                f"ok={len(ok_files)}",
                f"missing={len(missing)}",
                f"failed={len(failed)}",
                ("missing_paths=" + json.dumps(missing, ensure_ascii=True)) if missing else "",
                ("failed_paths=" + json.dumps(failed, ensure_ascii=True)) if failed else "",
            ]
        ).strip()
        + "\n",
    )
    record_artifact(ctx, extract_log, kind="log", meta={"step": "extract"})

    extracted_path = ctx.artifacts_dir / "extracted.json"
    extracted = {"schemaVersion": 1, "files": ok_files}
    extracted_path.write_text(json.dumps(extracted, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, extracted_path, kind="pdf.extracted.structured", meta={"files": len(ok_files)})

    citations_path = ctx.artifacts_dir / "citations.bib"
    citations_path.write_text(to_citations_bib(ok_files), encoding="utf-8")
    record_artifact(ctx, citations_path, kind="citations.bib", meta={"files": len(ok_files)})

    evidence_log = ctx.logs_dir / "evidence.log"
    evidence = make_evidence_from_extracted(ok_files)
    _write_log(evidence_log, f"evidence_count={len(evidence)}\n")
    record_artifact(ctx, evidence_log, kind="log", meta={"step": "evidence"})

    evidence_path = ctx.artifacts_dir / "evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, evidence_path, kind="evidence", meta={"count": len(evidence)})

    llm_log = ctx.logs_dir / "llm.log"
    llm_summary: Optional[str] = None
    if not args.no_llm and evidence:
        dotenv = _load_openclaw_dotenv()
        api_key = os.environ.get("MAAS_API_KEY") or dotenv.get("MAAS_API_KEY") or ""
        base_url = os.environ.get("MAAS_BASE_URL") or dotenv.get("MAAS_BASE_URL") or "https://api.modelarts-maas.com/openai/v1"
        model = os.environ.get("MAAS_MODEL") or dotenv.get("MAAS_MODEL") or "glm-5"
        if not api_key:
            _write_log(llm_log, "missing MAAS_API_KEY; rerun with --no-llm or set MAAS_API_KEY\n")
        else:
            prompt = (
                "你是科研助理。请仅基于以下 evidence 片段，总结 8-12 句中文简报摘要。\\n"
                "要求：\\n"
                "- 不要杜撰，不要引入 evidence 以外的信息。\\n"
                "- 每一句末尾标注来源，格式为 [file:/abs/path.pdf page:N]。\\n"
                "- 输出纯文本，不要 markdown。\\n\\n"
                "Evidence JSON:\\n"
                + json.dumps(evidence[:20], ensure_ascii=True, indent=2)
            )
            try:
                llm_summary = call_openai_compat(api_key=api_key, base_url=base_url, model=model, prompt=prompt)
                _write_log(llm_log, "ok\n")
            except Exception as e:
                _write_log(llm_log, f"error: {e}\n")
    else:
        _write_log(llm_log, "skipped\n")
    record_artifact(ctx, llm_log, kind="log", meta={"step": "llm", "ok": bool(llm_summary)})

    brief_log = ctx.logs_dir / "brief.log"
    brief_path = ctx.artifacts_dir / "brief.md"
    brief_path.write_text(compose_brief_md(files=ok_files, evidence=evidence, llm_summary=llm_summary), encoding="utf-8")
    _write_log(brief_log, "ok\n")
    record_artifact(ctx, brief_log, kind="log", meta={"step": "brief"})
    record_artifact(ctx, brief_path, kind="brief.md")

    print(str(ctx.run_dir))
    if not ok_files:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
