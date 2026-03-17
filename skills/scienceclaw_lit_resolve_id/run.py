from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pmid", action="append", required=True)
    ap.add_argument("--project", default="default")
    # Standard flag across ScienceClaw skills. This skill doesn't call an LLM.
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    workspace = Path(args.workspace)
    ctx = init_run(
        workspace_dir=workspace,
        project=args.project,
        task="scienceclaw_lit_resolve_id",
        inputs={"pmids": args.pmid, "noLlm": bool(args.no_llm)},
    )

    dotenv = load_dotenv()
    ident = ncbi_identity(dotenv)

    mapping: List[Dict[str, str]] = []
    log_lines: List[str] = []
    for pmid in args.pmid:
        pmcid = pmc_id_for_pmid(pmid, ident) or ""
        mapping.append({"pmid": pmid, "pmcid": pmcid})
        log_lines.append(f"pmid={pmid} pmcid={pmcid}")

    out_path = ctx.artifacts_dir / "id_map.json"
    out_path.write_text(json.dumps(mapping, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, out_path, kind="id_map", meta={"count": len(mapping)})

    log_path = ctx.logs_dir / "resolve.log"
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"count": len(mapping)})

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
