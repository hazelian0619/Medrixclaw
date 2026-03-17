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


def _try_int(s: str) -> Optional[int]:
    try:
        if s.strip() == "":
            return None
        return int(s)
    except Exception:
        return None


def _try_float(s: str) -> Optional[float]:
    try:
        if s.strip() == "":
            return None
        return float(s)
    except Exception:
        return None


def _infer_type(values: List[str]) -> str:
    non_empty = [v for v in values if (v or "").strip() != ""]
    if not non_empty:
        return "empty"
    ints = [v for v in non_empty if _try_int(v) is not None]
    if len(ints) == len(non_empty):
        return "int"
    floats = [v for v in non_empty if _try_float(v) is not None]
    if len(floats) == len(non_empty):
        return "float"
    return "string"


def _profile_csv(path: Path, max_rows: int) -> Tuple[Dict[str, Any], List[List[str]]]:
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

    cols = len(headers)
    col_values: List[List[str]] = [[] for _ in range(cols)]
    missing: List[int] = [0 for _ in range(cols)]
    for row in rows:
        rr = (row + [""] * cols)[:cols]
        for j, v in enumerate(rr):
            if (v or "").strip() == "":
                missing[j] += 1
            col_values[j].append(v)

    columns: List[Dict[str, Any]] = []
    for j, h in enumerate(headers):
        vals = col_values[j]
        t = _infer_type(vals)
        col: Dict[str, Any] = {"name": h or f"col{j+1}", "inferredType": t, "missing": missing[j], "nonEmpty": len(vals) - missing[j]}
        if t in ("int", "float"):
            nums = [(_try_float(v) if t == "float" else float(_try_int(v) or 0)) for v in vals if (v or "").strip() != ""]
            if nums:
                col["min"] = min(nums)
                col["max"] = max(nums)
        # distinct estimate (bounded)
        distinct = []
        seen = set()
        for v in vals:
            if v in seen:
                continue
            seen.add(v)
            distinct.append(v)
            if len(distinct) >= 20:
                break
        col["distinctSample"] = distinct
        columns.append(col)

    prof = {"format": "csv", "rowsScanned": len(rows), "columns": columns, "headerColumns": len(headers)}
    preview_rows = rows[: min(10, len(rows))]
    return prof, preview_rows


def _profile_json(path: Path, max_rows: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("json profile requires a JSON array")
    rows: List[Dict[str, Any]] = []
    keys: List[str] = []
    for it in data[:max_rows]:
        if not isinstance(it, dict):
            continue
        rows.append(it)
        for k in it.keys():
            if k not in keys:
                keys.append(k)

    cols: List[Dict[str, Any]] = []
    for k in keys:
        vals = [it.get(k) for it in rows]
        missing = sum(1 for v in vals if v is None or v == "")
        # coarse type inference
        non_empty = [v for v in vals if v is not None and v != ""]
        t = "empty"
        if non_empty:
            if all(isinstance(v, bool) for v in non_empty):
                t = "bool"
            elif all(isinstance(v, int) for v in non_empty):
                t = "int"
            elif all(isinstance(v, (int, float)) for v in non_empty):
                t = "float"
            elif all(isinstance(v, (dict, list)) for v in non_empty):
                t = "json"
            else:
                t = "string"
        col: Dict[str, Any] = {"name": k, "inferredType": t, "missing": missing, "nonEmpty": len(rows) - missing}
        if t in ("int", "float"):
            nums = [float(v) for v in non_empty if isinstance(v, (int, float))]
            if nums:
                col["min"] = min(nums)
                col["max"] = max(nums)
        cols.append(col)

    prof = {"format": "json", "rowsScanned": len(rows), "columns": cols, "keys": keys}
    preview = rows[: min(10, len(rows))]
    return prof, preview


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--format", default="auto", choices=["auto", "csv", "json"])
    ap.add_argument("--max-rows", type=int, default=5000)
    ap.add_argument("--project", default="default")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    ap.add_argument("--run-dir", default="", help="(internal) write artifacts into an existing run dir created by a workflow")
    args = ap.parse_args()

    in_path = Path(args.input).expanduser().resolve()
    if not in_path.exists():
        raise SystemExit(f"input not found: {in_path}")

    fmt = args.format
    if fmt == "auto":
        suf = in_path.suffix.lower()
        if suf == ".csv":
            fmt = "csv"
        elif suf == ".json":
            fmt = "json"
        else:
            raise SystemExit("format=auto could not infer; use --format csv|json")

    if args.run_dir:
        ctx = attach_run(run_dir=Path(args.run_dir), task_hint="scienceclaw_data_profile", inputs_update={"input": str(in_path), "format": fmt, "maxRows": int(args.max_rows)})
    else:
        ctx = init_run(
            workspace_dir=Path(args.workspace),
            project=args.project,
            task="scienceclaw_data_profile",
            inputs={"input": str(in_path), "format": fmt, "maxRows": int(args.max_rows), "noLlm": bool(args.no_llm)},
        )

    append_command(ctx, sys.argv[:])

    log_lines: List[str] = []
    profile: Dict[str, Any]
    preview_md = ""

    if fmt == "csv":
        prof, preview_rows = _profile_csv(in_path, max_rows=int(args.max_rows))
        headers = [c.get("name") for c in prof.get("columns", [])]
        preview = [[c for c in row] for row in preview_rows]
        preview_md = _md_table(headers, preview)
        profile = prof
    else:
        prof, preview_rows = _profile_json(in_path, max_rows=int(args.max_rows))
        # Render a preview table with first keys.
        keys = list(prof.get("keys") or [])[:8]
        rows: List[List[str]] = []
        for it in preview_rows:
            rows.append([json.dumps(it.get(k), ensure_ascii=True)[:80] if it.get(k) is not None else "" for k in keys])
        preview_md = _md_table(keys, rows)
        profile = prof

    out_json = ctx.artifacts_dir / "profile.json"
    out_json.write_text(json.dumps({"schemaVersion": 1, "source": str(in_path), **profile}, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, out_json, kind="data.profile.json", meta={"format": fmt})

    out_md = ctx.artifacts_dir / "profile.md"
    out_md.write_text(
        "# Data Profile\n\n"
        f"- Source: `{in_path}`\n"
        f"- Format: `{fmt}`\n"
        f"- Rows scanned: `{profile.get('rowsScanned')}`\n\n"
        "## Columns\n\n"
        + "\n".join(f"- `{c.get('name')}`: `{c.get('inferredType')}`, missing `{c.get('missing')}`" for c in (profile.get("columns") or []))
        + "\n\n## Preview\n\n"
        + preview_md
        + "\n",
        encoding="utf-8",
    )
    record_artifact(ctx, out_md, kind="data.profile.md", meta={"format": fmt})

    log_path = ctx.logs_dir / "profile.log"
    if not log_lines:
        log_lines.append("ok")
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"step": "profile", "ok": True})

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

