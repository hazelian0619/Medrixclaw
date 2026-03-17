from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import append_command, init_run, record_artifact  # noqa: E402


def _write_log(log_path: Path, text: str) -> None:
    log_path.write_text(text, encoding="utf-8")


def _load_openclaw_dotenv() -> Dict[str, str]:
    """
    Best-effort loader for `~/.openclaw/.env` so the workflow can run even when
    the shell hasn't exported MAAS_* vars. This avoids forcing users to `source`
    the file manually.
    """
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


def _ncbi_identity(dotenv: Dict[str, str]) -> Dict[str, str]:
    """
    NCBI E-utilities best practice: provide `tool` and `email` when available.
    Optional env vars:
      - NCBI_TOOL
      - NCBI_EMAIL
    """
    tool = os.environ.get("NCBI_TOOL") or dotenv.get("NCBI_TOOL") or ""
    email = os.environ.get("NCBI_EMAIL") or dotenv.get("NCBI_EMAIL") or ""
    out: Dict[str, str] = {}
    if tool:
        out["tool"] = tool
    if email:
        out["email"] = email
    return out


def pubmed_esearch(query: str, limit: int) -> List[str]:
    dotenv = _load_openclaw_dotenv()
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": query, "retmode": "json", "retmax": str(limit), "sort": "relevance"}
    params.update(_ncbi_identity(dotenv))
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("esearchresult", {}).get("idlist", [])


def pubmed_esummary(pmids: List[str]) -> Dict[str, Any]:
    if not pmids:
        return {}
    dotenv = _load_openclaw_dotenv()
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "json"}
    params.update(_ncbi_identity(dotenv))
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def pubmed_efetch_abstracts(pmids: List[str]) -> Dict[str, str]:
    """
    Return {pmid: abstract_text}.
    Use ElementTree for robustness (efetch XML varies; regex is too brittle).
    """
    if not pmids:
        return {}
    dotenv = _load_openclaw_dotenv()
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}
    params.update(_ncbi_identity(dotenv))
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    xml_text = r.text

    out: Dict[str, str] = {}
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        # If parsing fails, return empty; caller will degrade gracefully.
        return out

    for art in root.findall(".//PubmedArticle"):
        pmid = art.findtext(".//MedlineCitation/PMID")
        if not pmid:
            continue
        abs_nodes = art.findall(".//Abstract/AbstractText")
        if not abs_nodes:
            continue
        parts: List[str] = []
        for n in abs_nodes:
            # AbstractText can include labels and mixed content; itertext is safest.
            s = "".join(n.itertext()).strip()
            if s:
                parts.append(s)
        text = re.sub(r"\\s+", " ", " ".join(parts)).strip()
        if text:
            out[str(pmid)] = text
    return out


def to_bibtex(items: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for it in items:
        pmid = it.get("pmid") or ""
        key = f"pmid{pmid}" if pmid else f"item{len(lines)}"
        title = (it.get("title") or "").replace("{", "").replace("}", "")
        if pmid and not title:
            # Standardized "PMID-only" fallback (guarantee minimally useful BibTeX).
            title = f"PMID: {pmid}"
        authors = " and ".join(it.get("authors") or [])
        journal = (it.get("journal") or "").replace("{", "").replace("}", "")
        year = it.get("year") or ""
        lines.append(f"@article{{{key},")
        if title:
            lines.append(f"  title = {{{title}}},")
        if authors:
            lines.append(f"  author = {{{authors}}},")
        if journal:
            lines.append(f"  journal = {{{journal}}},")
        if year:
            lines.append(f"  year = {{{year}}},")
        if pmid:
            lines.append(f"  note = {{PMID: {pmid}}}")
        lines.append("}\n")
    return "\n".join(lines)


def normalize_summary(esummary_json: Dict[str, Any], pmids: List[str]) -> List[Dict[str, Any]]:
    result = esummary_json.get("result", {}) if isinstance(esummary_json, dict) else {}
    items: List[Dict[str, Any]] = []
    for pmid in pmids:
        rec = result.get(pmid, {})
        if not rec:
            continue
        authors = [a.get("name") for a in rec.get("authors", []) if a.get("name")]
        pubdate = rec.get("pubdate") or ""
        year = ""
        for tok in pubdate.split():
            if tok.isdigit() and len(tok) == 4:
                year = tok
                break
        items.append(
            {
                "pmid": pmid,
                "title": rec.get("title"),
                "authors": authors,
                "journal": rec.get("fulljournalname") or rec.get("source"),
                "pubdate": pubdate,
                "year": year,
            }
        )
    return items


def pmc_id_for_pmid(pmid: str) -> Optional[str]:
    """
    Try to map PubMed -> PMC via elink. Returns "PMCxxxxxx" or None.
    """
    dotenv = _load_openclaw_dotenv()
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
    params = {"dbfrom": "pubmed", "db": "pmc", "id": pmid, "retmode": "json"}
    params.update(_ncbi_identity(dotenv))
    r = requests.get(url, params=params, timeout=30)
    if r.status_code != 200:
        return None
    data = r.json()
    linksets = data.get("linksets", [])
    for ls in linksets:
        for db in ls.get("linksetdbs", []):
            if db.get("dbto") != "pmc":
                continue
            links = db.get("links", [])
            if not links:
                continue
            # links are numeric PMC ids without "PMC" prefix
            return "PMC" + str(links[0])
    return None


def fetch_pmc_pdf(pmcid: str, out_path: Path) -> Tuple[bool, str]:
    """
    Best-effort: fetch PDF for PMC article by scraping the article page for a pdf link.
    """
    base = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
    r = requests.get(base, timeout=30)
    if r.status_code != 200:
        return False, f"pmc page http {r.status_code}"
    html = r.text
    m = re.search(r'href=\"([^\"]+?\\.pdf)\"', html, flags=re.IGNORECASE)
    if not m:
        return False, "no pdf link found"
    href = m.group(1)
    pdf_url = href if href.startswith("http") else "https://pmc.ncbi.nlm.nih.gov" + href
    pr = requests.get(pdf_url, timeout=60)
    if pr.status_code != 200:
        return False, f"pdf http {pr.status_code}"
    out_path.write_bytes(pr.content)
    return True, pdf_url


def extract_pdf_text(pdf_path: Path) -> List[Dict[str, Any]]:
    import fitz  # PyMuPDF

    doc = fitz.open(str(pdf_path))
    pages: List[Dict[str, Any]] = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        text = page.get_text("text")
        pages.append({"page": i + 1, "text": text})
    return pages


def make_evidence_from_abstracts(items: List[Dict[str, Any]], abstracts: Dict[str, str]) -> List[Dict[str, Any]]:
    evidence: List[Dict[str, Any]] = []
    for it in items:
        pmid = it.get("pmid")
        if not pmid:
            continue
        abs_text = abstracts.get(pmid)
        if not abs_text:
            continue
        quote = abs_text[:900].strip()
        evidence.append(
            {
                "source": f"PMID:{pmid}",
                "locator": "abstract",
                "quote": quote,
                "usedIn": ["summary"],
            }
        )
    return evidence


def make_evidence_from_pdf(pmid: str, pages: List[Dict[str, Any]], max_quotes: int = 6) -> List[Dict[str, Any]]:
    evidence: List[Dict[str, Any]] = []
    for p in pages:
        if len(evidence) >= max_quotes:
            break
        text = re.sub(r"\\s+", " ", (p.get("text") or "")).strip()
        if len(text) < 200:
            continue
        quote = text[:900]
        evidence.append(
            {
                "source": f"PMID:{pmid}",
                "locator": f"page:{p.get('page')}",
                "quote": quote,
                "usedIn": ["summary"],
            }
        )
    return evidence


def compose_brief_md(*, query: str, items: List[Dict[str, Any]], evidence: List[Dict[str, Any]], llm_text: Optional[str]) -> str:
    lines: List[str] = []
    lines.append(f"# 证据链文献简报\n")
    lines.append(f"- Query: `{query}`")
    lines.append(f"- 生成时间（UTC）: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}\n")

    if llm_text:
        lines.append("## 摘要（模型生成）\n")
        lines.append(llm_text.strip())
        lines.append("")

    lines.append("## 候选文献（Top）\n")
    for i, it in enumerate(items, start=1):
        pmid = it.get("pmid")
        title = it.get("title") or ""
        year = it.get("year") or ""
        journal = it.get("journal") or ""
        lines.append(f"{i}. {title} ({year}, {journal}) [PMID:{pmid}]")
    lines.append("")

    lines.append("## 证据片段（Evidence）\n")
    for i, ev in enumerate(evidence, start=1):
        lines.append(f"### E{i} {ev.get('source')} {ev.get('locator')}")
        lines.append(ev.get("quote", "").strip())
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def call_llm_glm5(*, api_key: str, base_url: str, prompt: str) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": "glm-5",
        "messages": [
            {"role": "user", "content": prompt},
        ],
    }
    r = requests.post(url, headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--project", default="default")
    ap.add_argument("--pdf", action="append", default=[])
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    workspace = Path(args.workspace)
    ctx = init_run(workspace_dir=workspace, project=args.project, task="scienceclaw_lit_brief", inputs={"query": args.query, "limit": args.limit, "noPdf": args.no_pdf, "noLlm": args.no_llm})

    # 1) PubMed search + summary + abstract fetch
    log0 = ctx.logs_dir / "pubmed.log"
    append_command(ctx, ["pubmed_esearch/esummary/efetch", args.query, str(args.limit)])
    try:
        pmids = pubmed_esearch(args.query, args.limit)
        esum = pubmed_esummary(pmids)
        items = normalize_summary(esum, pmids)
        abstracts = pubmed_efetch_abstracts(pmids)
        _write_log(log0, f"pmids={len(pmids)}\\nitems={len(items)}\\nabstracts={len(abstracts)}\\n")
    except Exception as e:
        _write_log(log0, f"error: {e}\\n")
        record_artifact(ctx, log0, kind="log", meta={"step": "pubmed", "ok": False})
        raise
    record_artifact(ctx, log0, kind="log", meta={"step": "pubmed", "ok": True})

    results_path = ctx.artifacts_dir / "results.json"
    results_path.write_text(json.dumps({"items": items, "abstracts": abstracts}, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, results_path, kind="pubmed.results", meta={"count": len(items)})

    bib_path = ctx.artifacts_dir / "citations.bib"
    bib_text = to_bibtex(items)
    if (not bib_text.strip()) and pmids:
        # If normalization failed upstream (e.g. esummary empty), still emit PMID-only entries.
        bib_text = to_bibtex([{"pmid": p} for p in pmids])
    bib_path.write_text(bib_text, encoding="utf-8")
    record_artifact(ctx, bib_path, kind="citations.bib")

    evidence: List[Dict[str, Any]] = []
    evidence.extend(make_evidence_from_abstracts(items, abstracts))

    # 2a) Optional: process local PDFs (most reliable path)
    for pdf_str in args.pdf:
        pdf_path = Path(pdf_str).expanduser().resolve()
        if not pdf_path.exists():
            continue
        try:
            pages = extract_pdf_text(pdf_path)
            extracted_path = ctx.artifacts_dir / f"local_{pdf_path.stem}.extracted.json"
            extracted_path.write_text(json.dumps({"source": str(pdf_path), "pages": pages}, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            record_artifact(ctx, extracted_path, kind="pdf.extracted", meta={"source": str(pdf_path), "pages": len(pages)})
            # Use file path as source for evidence
            evidence.extend(
                [
                    {
                        "source": f"file:{pdf_path}",
                        "locator": f"page:{p.get('page')}",
                        "quote": re.sub(r"\\s+", " ", (p.get("text") or "")).strip()[:900],
                        "usedIn": ["summary"],
                    }
                    for p in pages[:3]
                    if (p.get("text") or "").strip()
                ]
            )
        except Exception:
            # Do not fail the whole run because a local PDF couldn't be parsed.
            continue

    # 2b) Optional: fetch 1-2 PDFs from PMC and extract text (best-effort; may be blocked by POW)
    if (not args.no_pdf) and (not args.pdf):
        pdf_log = ctx.logs_dir / "pdf_fetch.log"
        ok_count = 0
        for it in items[: min(3, len(items))]:
            pmid = it.get("pmid")
            if not pmid:
                continue
            pmcid = pmc_id_for_pmid(pmid)
            if not pmcid:
                continue
            out_pdf = ctx.artifacts_dir / f"{pmid}.pdf"
            try:
                ok, src = fetch_pmc_pdf(pmcid, out_pdf)
                if not ok:
                    continue
                ok_count += 1
                record_artifact(ctx, out_pdf, kind="pdf", meta={"pmid": pmid, "pmcid": pmcid, "url": src})
                pages = extract_pdf_text(out_pdf)
                extracted_path = ctx.artifacts_dir / f"{pmid}.extracted.json"
                extracted_path.write_text(json.dumps({"pmid": pmid, "pmcid": pmcid, "pages": pages}, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
                record_artifact(ctx, extracted_path, kind="pdf.extracted", meta={"pages": len(pages)})
                evidence.extend(make_evidence_from_pdf(pmid, pages))
            except Exception as e:
                pdf_log.write_text(f"pmid={pmid} error: {e}\\n", encoding="utf-8")
        _write_log(pdf_log, f"pdf_ok={ok_count}\\n")
        record_artifact(ctx, pdf_log, kind="log", meta={"step": "pdf", "ok": True})

    # 3) Evidence JSON
    evidence_path = ctx.artifacts_dir / "evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, evidence_path, kind="evidence", meta={"count": len(evidence)})

    # 4) Compose brief
    llm_text: Optional[str] = None
    llm_log = ctx.logs_dir / "llm.log"
    if not args.no_llm:
        dotenv = _load_openclaw_dotenv()
        api_key = os.environ.get("MAAS_API_KEY") or dotenv.get("MAAS_API_KEY") or ""
        base_url = os.environ.get("MAAS_BASE_URL") or dotenv.get("MAAS_BASE_URL") or "https://api.modelarts-maas.com/openai/v1"
        if not api_key:
            _write_log(llm_log, "missing MAAS_API_KEY in env; rerun with --no-llm or set MAAS_API_KEY\n")
        else:
            prompt = (
                "你是生命科学科研助理。请基于以下证据片段，生成一段 8-12 句的中文研究简报摘要。\\n"
                "要求：\\n"
                "- 只总结证据中出现的信息，不要杜撰。\\n"
                "- 在每一句末尾用 [PMID:xxxxxx] 形式标注来源（如果该句来自某 PMID 的证据）。\\n"
                "- 输出纯文本，不要 markdown 标题。\\n\\n"
                f"Query: {args.query}\\n\\n"
                "Evidence JSON:\\n"
                + json.dumps(evidence[:20], ensure_ascii=True, indent=2)
            )
            try:
                llm_text = call_llm_glm5(api_key=api_key, base_url=base_url, prompt=prompt)
                _write_log(llm_log, "ok\n")
            except Exception as e:
                _write_log(llm_log, f"error: {e}\n")
    record_artifact(ctx, llm_log, kind="log", meta={"step": "llm", "ok": bool(llm_text)})

    brief_path = ctx.artifacts_dir / "brief.md"
    brief_path.write_text(compose_brief_md(query=args.query, items=items, evidence=evidence, llm_text=llm_text), encoding="utf-8")
    record_artifact(ctx, brief_path, kind="brief.md")

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
