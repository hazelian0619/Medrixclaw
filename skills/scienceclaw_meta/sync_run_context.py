from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import List, Tuple


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _targets(repo_root: Path) -> List[Path]:
    # All skill-local run_context copies.
    skills_dir = repo_root / "scienceclaw" / "skills"
    out: List[Path] = []
    for p in skills_dir.rglob("lib/run_context.py"):
        # Do not self-sync the template itself.
        if "scienceclaw_meta/templates/" in str(p).replace("\\", "/"):
            continue
        out.append(p)
    return sorted(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="Do not modify files; exit non-zero if drift detected.")
    # .../scienceclaw/skills/scienceclaw_meta/sync_run_context.py -> repo root is parents[3]
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[3]))
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    template_path = repo_root / "scienceclaw" / "skills" / "scienceclaw_meta" / "templates" / "run_context.py"
    if not template_path.exists():
        raise SystemExit(f"template not found: {template_path}")

    tmpl = _read_text(template_path).rstrip() + "\n"
    tmpl_hash = _sha256_text(tmpl)

    changed: List[Tuple[Path, str, str]] = []
    for p in _targets(repo_root):
        cur = _read_text(p).rstrip() + "\n"
        cur_hash = _sha256_text(cur)
        if cur_hash == tmpl_hash:
            continue
        changed.append((p, cur_hash, tmpl_hash))
        if not args.check:
            p.write_text(tmpl, encoding="utf-8")

    if changed:
        print(f"[sync_run_context] template_sha256={tmpl_hash}")
        for p, cur_hash, want_hash in changed:
            print(f"[sync_run_context] drift: {p} cur={cur_hash[:12]} want={want_hash[:12]}")
        if args.check:
            print("[sync_run_context] FAIL: drift detected (run with this script without --check to sync).")
            return 2
        print(f"[sync_run_context] synced {len(changed)} file(s).")
    else:
        print("[sync_run_context] ok: no drift.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
