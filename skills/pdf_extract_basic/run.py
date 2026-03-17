from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import init_run, record_artifact  # noqa: E402


def extract_pdf_text(pdf_path: Path) -> List[Dict[str, Any]]:
    import fitz  # PyMuPDF

    doc = fitz.open(str(pdf_path))
    pages: List[Dict[str, Any]] = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        text = page.get_text("text")
        pages.append({"page": i + 1, "text": text})
    return pages


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--project", default="default")
    # Standard flag across ScienceClaw skills. This skill doesn't call an LLM,
    # but we keep the interface uniform and record it in manifest inputs.
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument(
        "--workspace",
        default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")),
    )
    args = ap.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    ctx = init_run(
        workspace_dir=Path(args.workspace),
        project=args.project,
        task="pdf_extract_basic",
        inputs={"pdf": str(pdf_path), "noLlm": bool(args.no_llm)},
    )

    pages = extract_pdf_text(pdf_path)

    out_path = ctx.artifacts_dir / "extracted.json"
    out = {"pdf": str(pdf_path), "pages": pages}
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, out_path, kind="pdf.extracted", meta={"pages": len(pages)})

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
