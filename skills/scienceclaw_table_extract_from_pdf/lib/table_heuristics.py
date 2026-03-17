from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple


# Split columns on tabs or runs of 2+ spaces.
_SPLIT_SPACES = re.compile(r"(?:\t|\s{2,})+")


def _split_cols(line: str) -> List[str]:
    s = line.strip().strip("\ufeff")
    if not s:
        return []
    if "|" in s and s.count("|") >= 2:
        parts = [p.strip() for p in s.strip("|").split("|")]
        parts = [p for p in parts if p != ""]
        return parts
    parts = [p.strip() for p in _SPLIT_SPACES.split(s) if p.strip()]
    return parts


def _mode_int(values: Sequence[int]) -> Optional[int]:
    if not values:
        return None
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    best = max(counts.items(), key=lambda kv: (kv[1], kv[0]))
    return int(best[0])


@dataclass(frozen=True)
class TableCandidate:
    page: int
    bbox: Tuple[float, float, float, float]
    raw_text: str
    rows: List[List[str]]
    cols: int
    score: float


def parse_table_like_block(*, text: str, page: int, bbox: Tuple[float, float, float, float], min_rows: int) -> Optional[TableCandidate]:
    raw = (text or "").strip()
    if not raw:
        return None
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if len(lines) < min_rows:
        return None

    splits: List[List[str]] = []
    col_counts: List[int] = []
    for ln in lines:
        cols = _split_cols(ln)
        splits.append(cols)
        if len(cols) >= 2:
            col_counts.append(len(cols))

    if len(col_counts) < min_rows:
        return None

    mode_cols = _mode_int(col_counts)
    if not mode_cols or mode_cols < 2:
        return None

    good_rows = [r for r in splits if len(r) == mode_cols]
    if len(good_rows) < min_rows:
        # If most lines have >=2 cols but not a stable count, it's still useful as raw evidence,
        # but we won't treat it as a parsed table candidate.
        return None

    norm_rows: List[List[str]] = []
    for r in good_rows:
        rr = list(r[:mode_cols])
        if len(rr) < mode_cols:
            rr.extend([""] * (mode_cols - len(rr)))
        norm_rows.append(rr)

    # A lightweight score: prefer more rows and more columns.
    score = float(len(norm_rows) * 10 + mode_cols)
    return TableCandidate(page=page, bbox=bbox, raw_text=raw, rows=norm_rows, cols=mode_cols, score=score)


def to_markdown_table(rows: List[List[str]]) -> str:
    if not rows:
        return ""
    cols = max((len(r) for r in rows), default=0)
    if cols <= 0:
        return ""

    def esc(s: str) -> str:
        return (s or "").replace("|", "\\|").strip()

    hdr = rows[0] + [""] * (cols - len(rows[0]))
    body = rows[1:]
    lines: List[str] = []
    lines.append("| " + " | ".join(esc(x) for x in hdr) + " |")
    lines.append("| " + " | ".join(["---"] * cols) + " |")
    for r in body:
        rr = r + [""] * (cols - len(r))
        lines.append("| " + " | ".join(esc(x) for x in rr) + " |")
    return "\n".join(lines).strip() + "\n"
