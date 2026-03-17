from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import attach_run, append_command, init_run, record_artifact  # noqa: E402


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path, max_chars: int) -> str:
    try:
        s = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    s = s.strip()
    if len(s) > max_chars:
        return s[:max_chars] + "\n\n...[truncated]...\n"
    return s + ("\n" if not s.endswith("\n") else "")


def _unique_path(dir_path: Path, filename: str) -> Path:
    p = dir_path / filename
    if not p.exists():
        return p
    stem = p.stem
    suffix = p.suffix
    for i in range(2, 1000):
        cand = dir_path / f"{stem}_{i}{suffix}"
        if not cand.exists():
            return cand
    raise RuntimeError(f"too many collisions for filename: {filename}")


def _artifact_table(artifacts: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("| path | kind | bytes | sha256 |")
    lines.append("| --- | --- | ---: | --- |")
    for a in artifacts:
        p = str(a.get("path") or "")
        kind = str(a.get("kind") or "")
        b = a.get("bytes")
        sha = str(a.get("sha256") or "")
        lines.append(f"| `{p}` | `{kind}` | `{b if b is not None else ''}` | `{sha[:12] + '...' if sha else ''}` |")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default="", help="Target runDir to write report artifacts into.")
    ap.add_argument("--title", default="")
    ap.add_argument("--max-embed-chars", type=int, default=4000)
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--project", default="default")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    if args.run_dir:
        ctx = attach_run(run_dir=Path(args.run_dir), task_hint="scienceclaw_report_compose_md", inputs_update={"title": args.title})
    else:
        ctx = init_run(
            workspace_dir=Path(args.workspace),
            project=args.project,
            task="scienceclaw_report_compose_md",
            inputs={"title": args.title, "maxEmbedChars": int(args.max_embed_chars), "noLlm": bool(args.no_llm)},
        )

    append_command(ctx, sys.argv[:])

    run_dir = ctx.run_dir
    manifest_path = run_dir / "manifest.json"
    man = _read_json(manifest_path)
    artifacts = man.get("artifacts") if isinstance(man.get("artifacts"), list) else []
    commands = man.get("commands") if isinstance(man.get("commands"), list) else []
    inputs = man.get("inputs") if isinstance(man.get("inputs"), dict) else {}

    title = args.title.strip() or f"ScienceClaw Delivery Report ({man.get('task')})"
    created = man.get("createdAt") or ""
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    artifacts_dir = run_dir / "artifacts"

    # Best-effort: summarize common artifacts.
    embed: List[Dict[str, Any]] = []

    def add_embed(rel: str, label: str) -> None:
        p = artifacts_dir / rel
        if not p.exists() or not p.is_file():
            return
        txt = _read_text(p, max_chars=int(args.max_embed_chars))
        if not txt:
            return
        embed.append({"path": f"artifacts/{rel}", "label": label, "chars": len(txt)})

    # Common artifacts across workflows/base.
    for rel, label in [
        ("brief.md", "brief"),
        ("profile.md", "data_profile"),
        ("preview.md", "preview"),
        ("conversion.json", "conversion_meta"),
        ("citations.bib", "citations"),
        ("evidence.json", "evidence"),
    ]:
        add_embed(rel, label)

    # Evidence count (best-effort).
    evidence_count: Optional[int] = None
    ev_path = artifacts_dir / "evidence.json"
    if ev_path.exists():
        try:
            ev = _read_json(ev_path)
            if isinstance(ev, list):
                evidence_count = len(ev)
        except Exception:
            pass

    # Reproducibility presence.
    repro_dir = artifacts_dir / "reproducibility"
    has_repro = repro_dir.exists() and repro_dir.is_dir()

    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"- runId: `{man.get('runId')}`")
    lines.append(f"- task: `{man.get('task')}`")
    lines.append(f"- createdAt: `{created}`")
    lines.append(f"- reportGeneratedAt: `{now}`")
    if evidence_count is not None:
        lines.append(f"- evidenceCount: `{evidence_count}`")
    lines.append(f"- reproducibilityBundle: `{bool(has_repro)}`")
    lines.append("")

    lines.append("## Inputs")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(inputs, indent=2, ensure_ascii=True))
    lines.append("```")
    lines.append("")

    lines.append("## Commands")
    lines.append("")
    for c in commands[:200]:
        at = str(c.get("at") or "")
        argv = c.get("argv")
        if not isinstance(argv, list):
            continue
        lines.append(f"- `{at}` " + " ".join(f"`{str(x)}`" for x in argv))
    lines.append("")

    lines.append("## Artifacts")
    lines.append("")
    lines.append(_artifact_table(artifacts))
    lines.append("")

    # Embed key artifacts (best-effort, truncated).
    if embed:
        lines.append("## Highlights (Embedded, Truncated)")
        lines.append("")
        for it in embed:
            p = artifacts_dir / Path(it["path"]).name if it["path"].startswith("artifacts/") else artifacts_dir / it["path"]
            # Keep stable mapping: use rel path as listed.
            rel = it["path"].replace("artifacts/", "")
            fp = artifacts_dir / rel
            lines.append(f"### {it['label']} `{it['path']}`")
            lines.append("")
            lines.append("```")
            lines.append(_read_text(fp, max_chars=int(args.max_embed_chars)).rstrip())
            lines.append("```")
            lines.append("")

    if has_repro:
        lines.append("## Reproducibility")
        lines.append("")
        lines.append("This run includes a reproducibility bundle under `artifacts/reproducibility/`.")
        lines.append("- `commands.sh`")
        lines.append("- `checksums.sha256`")
        lines.append("- `environment.txt`")
        lines.append("- `analysis_log.md`")
        lines.append("")

    lines.append("## Rerun")
    lines.append("")
    lines.append("Re-run the generating skill/workflow with the same inputs under the same workspace.")
    lines.append("For reproducibility verification, compare `checksums.sha256` with regenerated outputs.")
    lines.append("")

    report_md = _unique_path(artifacts_dir, "report.md")
    report_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    record_artifact(ctx, report_md, kind="report.md", meta={"embedded": len(embed), "hasRepro": bool(has_repro)})

    report_json = _unique_path(artifacts_dir, "report.json")
    report_json.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "runId": man.get("runId"),
                "task": man.get("task"),
                "createdAt": created,
                "generatedAt": now,
                "embedded": embed,
                "hasRepro": bool(has_repro),
            },
            indent=2,
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    record_artifact(ctx, report_json, kind="report.json", meta={"embedded": len(embed)})

    log_path = ctx.logs_dir / "report.log"
    log_path.write_text("ok\n", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"step": "report", "ok": True})

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

