from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import init_run, record_artifact  # noqa: E402


def load_dotenv() -> Dict[str, str]:
    env_path = Path.home() / ".openclaw" / ".env"
    out: Dict[str, str] = {}
    if not env_path.exists():
        return out
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def ncbi_identity(dotenv: Dict[str, str]) -> Dict[str, str]:
    tool = os.environ.get("NCBI_TOOL") or dotenv.get("NCBI_TOOL") or ""
    email = os.environ.get("NCBI_EMAIL") or dotenv.get("NCBI_EMAIL") or ""
    out: Dict[str, str] = {}
    if tool:
        out["tool"] = tool
    if email:
        out["email"] = email
    return out


def pmc_id_for_pmid(pmid: str, ident: Dict[str, str]) -> Optional[str]:
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
    params = {"dbfrom": "pubmed", "db": "pmc", "id": pmid, "retmode": "json"}
    params.update(ident)
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
            return "PMC" + str(links[0])
    return None


def fetch_pdf_for_pmcid(pmcid: str) -> Tuple[Optional[bytes], str]:
    """
    Returns (pdf_bytes, source_url_or_reason).
    """
    # Strategy 1: canonical pdf endpoint (often redirects to actual pdf)
    url1 = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/"
    r1 = requests.get(url1, timeout=60, allow_redirects=True)
    # PMC sometimes blocks automated PDF downloads behind a JS proof-of-work (POW) gate.
    # Detect that and return a clear error so users can switch to local-PDF mode.
    if r1.status_code == 200 and r1.headers.get("Content-Type", "").lower().startswith("text/html") and "cloudpmc-viewer-pow" in r1.text:
        return None, "blocked_by_pmc_pow (requires browser)"
    if r1.status_code == 200 and (r1.headers.get("Content-Type", "").lower().startswith("application/pdf") or r1.content.startswith(b"%PDF")):
        return r1.content, r1.url

    # Strategy 2: scrape article page for .pdf link
    base = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
    r2 = requests.get(base, timeout=30)
    if r2.status_code != 200:
        return None, f"pmc page http {r2.status_code}"
    html = r2.text
    m = re.search(r'href=\"([^\"]+?\\.pdf)\"', html, flags=re.IGNORECASE)
    if not m:
        return None, "no pdf link found"
    href = m.group(1)
    pdf_url = href if href.startswith("http") else "https://pmc.ncbi.nlm.nih.gov" + href
    r3 = requests.get(pdf_url, timeout=60)
    if r3.status_code == 200 and r3.headers.get("Content-Type", "").lower().startswith("text/html") and "cloudpmc-viewer-pow" in r3.text:
        return None, "blocked_by_pmc_pow (requires browser)"
    if r3.status_code == 200 and (r3.headers.get("Content-Type", "").lower().startswith("application/pdf") or r3.content.startswith(b"%PDF")):
        return r3.content, pdf_url
    return None, f"pdf http {r3.status_code}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pmcid", action="append", default=[])
    ap.add_argument("--pmid", action="append", default=[])
    ap.add_argument("--project", default="default")
    # Standard flag across ScienceClaw skills. This skill doesn't call an LLM.
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    if not args.pmcid and not args.pmid:
        raise SystemExit("Pass --pmcid or --pmid")

    workspace = Path(args.workspace)
    ctx = init_run(
        workspace_dir=workspace,
        project=args.project,
        task="scienceclaw_lit_pdf_fetch_pmc",
        inputs={"pmcids": args.pmcid, "pmids": args.pmid, "noLlm": bool(args.no_llm)},
    )

    dotenv = load_dotenv()
    ident = ncbi_identity(dotenv)

    targets: List[Dict[str, str]] = []
    for pmid in args.pmid:
        pmcid = pmc_id_for_pmid(pmid, ident) or ""
        targets.append({"pmid": pmid, "pmcid": pmcid})
    for pmcid in args.pmcid:
        targets.append({"pmid": "", "pmcid": pmcid})

    downloads: List[Dict[str, Any]] = []
    for t in targets:
        pmid = t.get("pmid", "")
        pmcid = t.get("pmcid", "")
        if not pmcid:
            downloads.append({"pmid": pmid, "pmcid": pmcid, "ok": False, "error": "no pmcid"})
            continue
        try:
            pdf_bytes, src = fetch_pdf_for_pmcid(pmcid)
            if not pdf_bytes:
                downloads.append({"pmid": pmid, "pmcid": pmcid, "ok": False, "error": src})
                continue
            name = f"{pmid or pmcid}.pdf"
            out_pdf = ctx.artifacts_dir / name
            out_pdf.write_bytes(pdf_bytes)
            record_artifact(ctx, out_pdf, kind="pdf", meta={"pmid": pmid, "pmcid": pmcid, "url": src})
            downloads.append({"pmid": pmid, "pmcid": pmcid, "ok": True, "url": src, "path": f"artifacts/{name}"})
        except Exception as e:
            downloads.append({"pmid": pmid, "pmcid": pmcid, "ok": False, "error": str(e)})

    out_path = ctx.artifacts_dir / "downloads.json"
    out_path.write_text(json.dumps(downloads, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, out_path, kind="downloads", meta={"count": len(downloads)})

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
