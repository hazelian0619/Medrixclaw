from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify mandatory ScienceClaw skills are installed and runnable-ready.")
    ap.add_argument(
        "--workspace",
        default=str(Path.home() / ".openclaw" / "workspace"),
        help="OpenClaw workspace root",
    )
    ap.add_argument("--strict", action="store_true", help="return non-zero when verification fails")
    args = ap.parse_args()

    this_dir = Path(__file__).resolve().parent
    workspace = Path(args.workspace).expanduser().resolve()
    skills_dir = workspace / "skills"

    mandatory_path = this_dir / "mandatory_skills.json"
    pack_path = this_dir / "pack.json"

    mandatory_cfg = _read_json(mandatory_path)
    mandatory = list(mandatory_cfg.get("mandatory_skills", []))
    pack_cfg = _read_json(pack_path) if pack_path.exists() else {}
    allowlist = set(pack_cfg.get("allowlist", [])) if isinstance(pack_cfg, dict) else set()

    missing_dirs = []
    missing_skill_md = []
    missing_allowlist = []
    missing_entrypoints = []

    for skill in mandatory:
        d = skills_dir / skill
        if not d.exists() or not d.is_dir():
            missing_dirs.append(skill)
            continue
        if not (d / "SKILL.md").exists():
            missing_skill_md.append(skill)
        if skill not in allowlist:
            missing_allowlist.append(skill)
        if not (d / "run.py").exists() and not (d / "run.sh").exists():
            missing_entrypoints.append(skill)

    ok = not (missing_dirs or missing_skill_md or missing_allowlist or missing_entrypoints)

    result = {
        "schemaVersion": 1,
        "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "workspace": str(workspace),
        "skillsDir": str(skills_dir),
        "mandatoryCount": len(mandatory),
        "ok": ok,
        "missing": {
            "dirs": missing_dirs,
            "skill_md": missing_skill_md,
            "allowlist": missing_allowlist,
            "entrypoints": missing_entrypoints,
        },
    }

    print(json.dumps(result, indent=2, ensure_ascii=True))
    if args.strict and not ok:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
