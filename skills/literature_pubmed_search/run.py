from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import init_run, record_artifact  # noqa: E402


def esearch(query: str, limit: int) -> List[str]:
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": str(limit),
        "sort": "relevance",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("esearchresult", {}).get("idlist", [])


def esummary(pmids: List[str]) -> List[Dict[str, Any]]:
    if not pmids:
        return []
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "json"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    result = data.get("result", {})
    out: List[Dict[str, Any]] = []
    for pmid in pmids:
        rec = result.get(pmid, {})
        if not rec:
            continue
        out.append(
            {
                "pmid": pmid,
                "title": rec.get("title"),
                "authors": [a.get("name") for a in rec.get("authors", []) if a.get("name")],
                "journal": rec.get("fulljournalname") or rec.get("source"),
                "pubdate": rec.get("pubdate"),
                "doi": rec.get("elocationid"),
            }
        )
    return out


def to_bibtex(items: List[Dict[str, Any]]) -> str:
    # Best-effort BibTeX without DOI normalization.
    lines: List[str] = []
    for it in items:
        key = f"pmid{it['pmid']}"
        title = (it.get("title") or "").replace("{", "").replace("}", "")
        authors = " and ".join(it.get("authors") or [])
        journal = (it.get("journal") or "").replace("{", "").replace("}", "")
        year = ""
        pubdate = it.get("pubdate") or ""
        for token in pubdate.split():
            if token.isdigit() and len(token) == 4:
                year = token
                break
        lines.append(f"@article{{{key},")
        if title:
            lines.append(f"  title = {{{title}}},")
        if authors:
            lines.append(f"  author = {{{authors}}},")
        if journal:
            lines.append(f"  journal = {{{journal}}},")
        if year:
            lines.append(f"  year = {{{year}}},")
        lines.append(f"  note = {{PMID: {it['pmid']}}}")
        lines.append("}\n")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--project", default="default")
    # Standard flag across ScienceClaw skills. This skill doesn't call an LLM,
    # but we keep the interface uniform and record it in manifest inputs.
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument(
        "--workspace",
        default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")),
    )
    args = ap.parse_args()

    ctx = init_run(
        workspace_dir=Path(args.workspace),
        project=args.project,
        task="pubmed_search",
        inputs={"query": args.query, "limit": args.limit, "noLlm": bool(args.no_llm)},
    )

    pmids = esearch(args.query, args.limit)
    items = esummary(pmids)

    results_path = ctx.artifacts_dir / "results.json"
    results_path.write_text(json.dumps(items, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, results_path, kind="pubmed.results", meta={"count": len(items)})

    bib_path = ctx.artifacts_dir / "citations.bib"
    bib_path.write_text(to_bibtex(items), encoding="utf-8")
    record_artifact(ctx, bib_path, kind="citations.bib")

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
