from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import attach_run, append_command, init_run, record_artifact  # noqa: E402


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_name(name: str) -> str:
    out = "".join(c for c in (name or "") if c.isalnum() or c in ("-", "_", ".", " ")).strip().replace(" ", "_")
    return out or "download"


def _filename_from_url(url: str, idx: int) -> str:
    p = urllib.parse.urlparse(url)
    base = Path(p.path).name
    base = _safe_name(base)
    if not base or base == "download":
        base = f"download_{idx}"
    return base


def _domain(url: str) -> str:
    try:
        p = urllib.parse.urlparse(url)
        return (p.hostname or "").lower()
    except Exception:
        return ""


def _allowed(domain: str, allow_all: bool, allow_domains: List[str]) -> bool:
    if allow_all:
        return True
    if not domain:
        return False
    dom = domain.lower()
    for a in allow_domains:
        a = (a or "").strip().lower()
        if not a:
            continue
        if dom == a or dom.endswith("." + a):
            return True
    return False


def _download(url: str, out_path: Path, timeout_s: int = 60) -> Tuple[int, str, Optional[str]]:
    """
    Returns (http_status, final_url, error).
    """
    req = urllib.request.Request(url, headers={"User-Agent": "ScienceClaw/0.1 (http_fetch)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            status = int(getattr(resp, "status", 200))
            final_url = str(getattr(resp, "url", url))
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open("wb") as f:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
            return status, final_url, None
    except Exception as e:
        return 0, url, str(e)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", action="append", required=True)
    ap.add_argument("--allow-domain", action="append", default=[])
    ap.add_argument("--allow-all", action="store_true")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--project", default="default")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    ap.add_argument("--run-dir", default="", help="(internal) write artifacts into an existing run dir created by a workflow")
    args = ap.parse_args()

    urls = [u.strip() for u in (args.url or []) if (u or "").strip()]
    allow_domains = [d.strip() for d in (args.allow_domain or []) if (d or "").strip()]

    if args.run_dir:
        ctx = attach_run(
            run_dir=Path(args.run_dir),
            task_hint="scienceclaw_http_fetch",
            inputs_update={"urls": urls, "offline": bool(args.offline), "allowDomains": allow_domains, "allowAll": bool(args.allow_all)},
        )
    else:
        ctx = init_run(
            workspace_dir=Path(args.workspace),
            project=args.project,
            task="scienceclaw_http_fetch",
            inputs={"urls": urls, "offline": bool(args.offline), "allowDomains": allow_domains, "allowAll": bool(args.allow_all), "noLlm": bool(args.no_llm)},
        )

    append_command(ctx, sys.argv[:])

    log_lines: List[str] = []

    plan = {"schemaVersion": 1, "createdAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "urls": urls, "allowDomains": allow_domains, "allowAll": bool(args.allow_all)}
    plan_path = ctx.artifacts_dir / "fetch.plan.json"
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, plan_path, kind="http.fetch.plan", meta={"count": len(urls), "offline": bool(args.offline)})

    if args.offline:
        log_lines.append("offline=true; skip downloads")
    else:
        downloads_dir = ctx.artifacts_dir / "downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        results: List[Dict[str, Any]] = []
        for idx, url in enumerate(urls, start=1):
            dom = _domain(url)
            if not _allowed(dom, bool(args.allow_all), allow_domains):
                err = f"domain not allowed: {dom}"
                log_lines.append(f"DENY url={url} domain={dom}")
                hint = "add --allow-domain <domain> (or use --allow-all in a controlled environment)"
                results.append({"url": url, "domain": dom, "ok": False, "error": err, "hint": hint})
                continue

            fname = _filename_from_url(url, idx)
            out_path = downloads_dir / fname
            status, final_url, error = _download(url, out_path)
            if error:
                log_lines.append(f"FAIL url={url} error={error}")
                results.append({"url": url, "domain": dom, "ok": False, "error": error, "finalUrl": final_url, "httpStatus": status})
                continue

            sha = _sha256_file(out_path)
            record_artifact(ctx, out_path, kind="http.download", meta={"url": url, "finalUrl": final_url, "httpStatus": status})
            results.append(
                {
                    "url": url,
                    "domain": dom,
                    "ok": True,
                    "finalUrl": final_url,
                    "httpStatus": status,
                    "path": str(out_path.relative_to(ctx.run_dir)),
                    "bytes": out_path.stat().st_size,
                    "sha256": sha,
                }
            )
            log_lines.append(f"OK url={url} -> {out_path} sha256={sha[:12]}...")

        res_path = ctx.artifacts_dir / "fetch.results.json"
        res_path.write_text(json.dumps({"schemaVersion": 1, "results": results}, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        record_artifact(ctx, res_path, kind="http.fetch.results", meta={"count": len(results)})

    log_path = ctx.logs_dir / "fetch.log"
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"step": "fetch", "ok": True})

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
