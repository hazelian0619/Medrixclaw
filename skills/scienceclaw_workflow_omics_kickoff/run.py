from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR / "lib"))

from run_context import append_command, init_run, record_artifact  # noqa: E402


def _sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _now_local() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def _write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def _analysis_plan_template(*, dataset: str) -> str:
    return (
        "# Omics Analysis Plan (Phase 3)\n\n"
        f"- created_at: {_now_local()}\n"
        f"- dataset: {dataset}\n\n"
        "## 1. 目标与交付\n\n"
        "- 目标：完成 QC + 注释（必要时加轨迹/空间），并输出可复盘 runDir 产物包。\n"
        "- 交付：见本 runDir 的 artifacts 清单（brief/figures/evidence/citations）。\n\n"
        "## 2. 环境策略（参考 Pantheon: environment_management）\n\n"
        "- 环境：conda / venv（记录在 environment.md；导出 environment.yml 或 requirements.txt）。\n"
        "- 关键包版本：scanpy/anndata/numpy/pandas/scvi-tools/celltypist（按实际使用填写）。\n\n"
        "## 3. 性能策略（参考 Pantheon: parallel_computing）\n\n"
        "- n_jobs：\n"
        "- NUMBA/OMP/BLAS：见 perf_env.json。\n\n"
        "## 4. QC 计划（参考 Pantheon: quality_control，先做瘦身版）\n\n"
        "- 必做：QC metrics + 阈值决策 + 过滤前后统计 + 图。\n"
        "- 可选：doublet（有依赖时做）。\n"
        "- 备注：ambient RNA / SoupX 等重依赖先作为增强项，不阻塞 v1。\n\n"
        "## 5. 注释计划（参考 Pantheon: cell_type_annotation）\n\n"
        "- 方法：marker-based / reference-based（按实际选择）。\n"
        "- 输出：annotation_table.tsv（cluster_id -> cell_type + evidence_ref）。\n\n"
        "## 6. 可选模块\n\n"
        "- trajectory（参考 Pantheon: trajectory_inference）\n"
        "- spatial mapping（参考 Pantheon: single_cell_spatial_mapping）\n"
        "- database access（参考 Pantheon: database_access/*；作为在线增强）\n\n"
        "## 7. 产物清单（本 runDir 约定）\n\n"
        "- analysis_plan.md\n"
        "- environment.md\n"
        "- perf_env.json\n"
        "- qc_summary.md\n"
        "- annotation_table.tsv\n"
        "- figures/\n"
        "- citations.bib (non-empty)\n"
        "- evidence.json (non-empty)\n"
    )


def _environment_template() -> str:
    return (
        "# Environment (Phase 3 Omics)\n\n"
        "本文件用于记录可复现环境信息。\n\n"
        "## Python\n\n"
        "- python: \n"
        "- executable: \n\n"
        "## Env Manager\n\n"
        "- conda env: \n"
        "- venv path: \n\n"
        "## Packages (pin if possible)\n\n"
        "- scanpy==\n"
        "- anndata==\n"
        "- numpy==\n"
        "- pandas==\n"
        "- scipy==\n"
        "- matplotlib==\n"
        "- scvi-tools== (optional)\n"
        "- celltypist== (optional)\n"
    )


def _qc_summary_template() -> str:
    return (
        "# QC Summary\n\n"
        "## 数据概览\n\n"
        "- cells_before:\n"
        "- genes_before:\n"
        "- samples/batches:\n\n"
        "## QC 指标\n\n"
        "- counts:\n"
        "- genes:\n"
        "- mt_pct:\n\n"
        "## 阈值与理由（必须可复盘）\n\n"
        "- thresholds:\n"
        "- rationale (link to figures + evidence refs):\n\n"
        "## 过滤前后统计\n\n"
        "- cells_after:\n"
        "- genes_after:\n"
    )


def _annotation_table_template() -> str:
    return "cluster_id\tcell_type\tevidence_ref\tnotes\n"


def _bibtex_minimal() -> str:
    year = time.gmtime().tm_year
    return (
        "@misc{scienceclaw_p3_omics_kickoff,\n"
        "  title = {ScienceClaw Phase 3 Omics Kickoff},\n"
        f"  year = {{{year}}},\n"
        "  note = {Template bundle for QC+annotation deliverables; fill with real citations during analysis},\n"
        "}\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="default")
    ap.add_argument("--dataset", default="", help="Optional dataset path (recorded + hashed; not parsed).")
    # Standard flag across ScienceClaw skills. This workflow doesn't call an LLM,
    # but we keep the interface uniform and record it in manifest inputs.
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--workspace", default=os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
    args = ap.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    inputs: Dict[str, Any] = {"dataset": args.dataset, "noLlm": bool(args.no_llm)}
    ctx = init_run(workspace_dir=workspace, project=args.project, task="scienceclaw_workflow_omics_kickoff", inputs=inputs)
    append_command(ctx, sys.argv[:])

    log_lines: List[str] = []
    log_lines.append(f"created_at={_now_local()}")
    log_lines.append(f"workspace={workspace}")
    log_lines.append(f"run_dir={ctx.run_dir}")

    dataset_str = "(none)"
    if args.dataset:
        p = Path(args.dataset).expanduser().resolve()
        if p.exists() and p.is_file():
            dataset_str = str(p)
            log_lines.append(f"dataset_path={p}")
            try:
                log_lines.append(f"dataset_sha256={_sha256_file(p)}")
                record_artifact(ctx, p, kind="input.file", meta={"role": "dataset"})
            except Exception:
                log_lines.append("dataset_sha256=error")
        else:
            dataset_str = f"(missing:{p})"
            log_lines.append(f"dataset_missing={p}")

    figures_dir = ctx.artifacts_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    # Keep an empty placeholder file so directory presence is visible in artifacts listing.
    placeholder = figures_dir / ".keep"
    _write_text(placeholder, "")
    record_artifact(ctx, placeholder, kind="figures.keep")

    analysis_plan = ctx.artifacts_dir / "analysis_plan.md"
    _write_text(analysis_plan, _analysis_plan_template(dataset=dataset_str))
    record_artifact(ctx, analysis_plan, kind="analysis_plan.md")

    environment_md = ctx.artifacts_dir / "environment.md"
    _write_text(environment_md, _environment_template())
    record_artifact(ctx, environment_md, kind="environment.md")

    perf_env = ctx.artifacts_dir / "perf_env.json"
    perf_payload = {
        "schemaVersion": 1,
        "createdAt": _now_local(),
        "cpuCount": os.cpu_count(),
        "env": {k: os.environ.get(k, "") for k in ["NUMBA_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]},
    }
    perf_env.write_text(json.dumps(perf_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, perf_env, kind="perf_env.json")

    qc_summary = ctx.artifacts_dir / "qc_summary.md"
    _write_text(qc_summary, _qc_summary_template())
    record_artifact(ctx, qc_summary, kind="qc_summary.md")

    anno_tsv = ctx.artifacts_dir / "annotation_table.tsv"
    _write_text(anno_tsv, _annotation_table_template())
    record_artifact(ctx, anno_tsv, kind="annotation_table.tsv")

    citations = ctx.artifacts_dir / "citations.bib"
    _write_text(citations, _bibtex_minimal())
    record_artifact(ctx, citations, kind="citations.bib", meta={"mode": "kickoff"})

    evidence = ctx.artifacts_dir / "evidence.json"
    evidence_items: List[Dict[str, Any]] = [
        {
            "source": f"file:{analysis_plan.resolve()}",
            "locator": "offset:0-300",
            "quote": "目标：完成 QC + 注释，并输出可复盘 runDir 产物包。",
            "usedIn": ["p3/omics/kickoff"],
        }
    ]
    evidence.write_text(json.dumps(evidence_items, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    record_artifact(ctx, evidence, kind="evidence", meta={"count": len(evidence_items), "mode": "kickoff"})

    log_path = ctx.logs_dir / "kickoff.log"
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    record_artifact(ctx, log_path, kind="log", meta={"step": "kickoff"})

    print(str(ctx.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
