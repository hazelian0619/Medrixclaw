from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def quote_hash(quote: str) -> str:
    # Spec: whitespace-normalize first, then sha256.
    return _sha256_text(_norm_ws(quote))


@dataclass(frozen=True)
class SourceNorm:
    canonical: str  # e.g. "PMID:38239341" / "DOI:10.1038/..." / "file:/abs/path.pdf"
    kind: str  # pmid|doi|file|unknown
    id: str  # raw id portion (canonicalized per kind)


@dataclass(frozen=True)
class LocatorNorm:
    canonical: str  # e.g. "abstract" / "page:3" / "offset:120-200"
    kind: str  # abstract|page|offset|unknown
    data: Dict[str, Any]


def _as_str(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    return str(x)


def normalize_source(src: Any) -> SourceNorm:
    # Prefer object form: {kind, id}
    if isinstance(src, dict):
        kind = (_as_str(src.get("kind")) or "").strip().lower()
        _id = (_as_str(src.get("id")) or "").strip()
        if kind == "pmid":
            pmid = re.sub(r"\D+", "", _id)
            return SourceNorm(canonical=f"PMID:{pmid}", kind="pmid", id=pmid)
        if kind == "doi":
            doi = _id.strip()
            doi = doi.lower()
            doi = doi.replace("doi:", "").strip()
            return SourceNorm(canonical=f"DOI:{doi}", kind="doi", id=doi)
        if kind == "file":
            p = Path(_id).expanduser()
            # Spec requires absolute paths; normalize for stability.
            if not p.is_absolute():
                p = p.resolve()
            canon = "file:" + os.path.normpath(str(p))
            return SourceNorm(canonical=canon, kind="file", id=str(p))
        # Unknown structured source
        s = json.dumps(src, ensure_ascii=True, sort_keys=True)
        return SourceNorm(canonical=f"unknown:{s}", kind="unknown", id=s)

    s = _as_str(src).strip()
    if not s:
        return SourceNorm(canonical="unknown:", kind="unknown", id="")

    m = re.match(r"^(PMID|DOI|file)\s*:\s*(.+)$", s, flags=re.IGNORECASE)
    if not m:
        return SourceNorm(canonical=f"unknown:{s}", kind="unknown", id=s)

    prefix = m.group(1).lower()
    body = m.group(2).strip()
    if prefix == "pmid":
        pmid = re.sub(r"\D+", "", body)
        return SourceNorm(canonical=f"PMID:{pmid}", kind="pmid", id=pmid)
    if prefix == "doi":
        doi = body.lower().replace("doi:", "").strip()
        return SourceNorm(canonical=f"DOI:{doi}", kind="doi", id=doi)
    if prefix == "file":
        p = Path(body).expanduser()
        if not p.is_absolute():
            p = p.resolve()
        canon = "file:" + os.path.normpath(str(p))
        return SourceNorm(canonical=canon, kind="file", id=str(p))
    return SourceNorm(canonical=f"unknown:{s}", kind="unknown", id=s)


def normalize_locator(loc: Any) -> LocatorNorm:
    if isinstance(loc, dict):
        kind = (_as_str(loc.get("kind")) or "").strip().lower()
        if kind == "page":
            try:
                page = int(loc.get("page"))
            except Exception:
                page = -1
            return LocatorNorm(canonical=f"page:{page}", kind="page", data={"page": page})
        if kind == "abstract":
            return LocatorNorm(canonical="abstract", kind="abstract", data={})
        if kind == "offset":
            try:
                start = int(loc.get("start"))
            except Exception:
                start = -1
            try:
                end = int(loc.get("end"))
            except Exception:
                end = -1
            return LocatorNorm(canonical=f"offset:{start}-{end}", kind="offset", data={"start": start, "end": end})
        s = json.dumps(loc, ensure_ascii=True, sort_keys=True)
        return LocatorNorm(canonical=f"unknown:{s}", kind="unknown", data={"raw": s})

    s = _as_str(loc).strip()
    if not s:
        return LocatorNorm(canonical="unknown:", kind="unknown", data={"raw": ""})

    if s.lower().startswith("page:"):
        try:
            page = int(s.split(":", 1)[1].strip())
        except Exception:
            page = -1
        return LocatorNorm(canonical=f"page:{page}", kind="page", data={"page": page})
    if s.lower() == "abstract" or s.lower().startswith("abstract:"):
        return LocatorNorm(canonical="abstract", kind="abstract", data={"raw": s})
    if s.lower().startswith("offset:"):
        rest = s.split(":", 1)[1].strip()
        m = re.match(r"^(\d+)\s*-\s*(\d+)$", rest)
        if m:
            start = int(m.group(1))
            end = int(m.group(2))
            return LocatorNorm(canonical=f"offset:{start}-{end}", kind="offset", data={"start": start, "end": end})
        return LocatorNorm(canonical=f"offset:{rest}", kind="offset", data={"raw": rest})

    return LocatorNorm(canonical=f"unknown:{s}", kind="unknown", data={"raw": s})


def dedupe_evidence(evidence: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    seen: set[str] = set()
    out: List[Dict[str, Any]] = []
    dropped = 0
    for ev in evidence:
        srcn = normalize_source(ev.get("source"))
        locn = normalize_locator(ev.get("locator"))
        qh = _as_str(ev.get("hash")).strip() or quote_hash(_as_str(ev.get("quote")))
        key = srcn.canonical + "|" + locn.canonical + "|" + qh
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        ev2 = dict(ev)
        # Ensure optional governance fields exist for downstream tools.
        ev2.setdefault("hash", qh)
        out.append(ev2)
    stats = {"before": len(evidence), "after": len(out), "dropped": dropped}
    return out, stats


def _sanitize_key(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        return "item"
    if not re.match(r"^[a-z]", s):
        s = "k_" + s
    return s


def _unique_keys(keys: Iterable[str]) -> List[str]:
    used: Dict[str, int] = {}
    out: List[str] = []
    for k in keys:
        base = k
        n = used.get(base, 0)
        if n == 0:
            used[base] = 1
            out.append(base)
            continue
        used[base] = n + 1
        out.append(f"{base}_{n+1}")
    return out


def _bib_field(name: str, value: str) -> Optional[str]:
    v = (value or "").strip()
    if not v:
        return None
    v = v.replace("{", "").replace("}", "")
    return f"  {name} = {{{v}}},"


def sources_from_results(results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    items = results.get("items") if isinstance(results, dict) else None
    if not isinstance(items, list):
        return out
    for it in items:
        if not isinstance(it, dict):
            continue
        pmid = _as_str(it.get("pmid")).strip()
        if not pmid:
            continue
        src = normalize_source(f"PMID:{pmid}")
        out[src.canonical] = {
            "source": {"kind": "pmid", "id": src.id},
            "title": _as_str(it.get("title")).strip(),
            "authors": it.get("authors") if isinstance(it.get("authors"), list) else [],
            "journal": _as_str(it.get("journal")).strip(),
            "year": _as_str(it.get("year")).strip(),
        }
    return out


def sources_from_evidence(evidence: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for ev in evidence:
        src = normalize_source(ev.get("source"))
        if src.kind == "unknown" or not src.canonical:
            continue
        rec = out.get(src.canonical, {"source": {"kind": src.kind, "id": src.id}})
        # Take first non-empty metadata encountered (best-effort merge).
        for k in ("title", "year", "confidence"):
            if not rec.get(k) and ev.get(k) is not None:
                rec[k] = ev.get(k)
        if not rec.get("authors") and isinstance(ev.get("authors"), list):
            rec["authors"] = ev.get("authors")
        out[src.canonical] = rec
    return out


def to_bibtex(sources: List[Dict[str, Any]]) -> str:
    # Deterministic sort by canonical source.
    sources_sorted = sorted(sources, key=lambda x: _as_str(x.get("canonical")))
    raw_keys: List[str] = []
    for s in sources_sorted:
        canon = _as_str(s.get("canonical"))
        if canon.startswith("PMID:"):
            raw_keys.append("pmid" + canon.split(":", 1)[1])
        elif canon.startswith("DOI:"):
            doi = canon.split(":", 1)[1]
            slug = _sanitize_key(doi)
            # Keep keys readable but bounded.
            if len(slug) > 48:
                slug = slug[:48] + "_" + hashlib.sha1(doi.encode("utf-8")).hexdigest()[:8]
            raw_keys.append("doi_" + slug)
        elif canon.startswith("file:"):
            p = canon.split(":", 1)[1]
            raw_keys.append("file_" + hashlib.sha1(p.encode("utf-8")).hexdigest()[:10])
        else:
            raw_keys.append("src_" + hashlib.sha1(canon.encode("utf-8")).hexdigest()[:10])
    keys = _unique_keys(raw_keys)

    lines: List[str] = []
    for key, s in zip(keys, sources_sorted):
        canon = _as_str(s.get("canonical"))
        kind = _as_str(s.get("kind"))
        meta = s.get("meta") if isinstance(s.get("meta"), dict) else {}

        title = _as_str(meta.get("title")).strip()
        authors = meta.get("authors") if isinstance(meta.get("authors"), list) else []
        journal = _as_str(meta.get("journal")).strip()
        year = _as_str(meta.get("year")).strip()

        if kind == "pmid" and not title:
            title = canon  # "PMID:xxxx"
        if kind == "doi" and not title:
            title = canon  # "DOI:..."
        if kind == "file" and not title:
            title = "Local file: " + Path(canon.split(":", 1)[1]).name

        lines.append(f"@article{{{key},")
        bf = _bib_field("title", title)
        if bf:
            lines.append(bf)
        if authors:
            lines.append(_bib_field("author", " and ".join([_as_str(a) for a in authors if _as_str(a).strip()])) or "  author = {},")
        bf = _bib_field("journal", journal)
        if bf:
            lines.append(bf)
        bf = _bib_field("year", year)
        if bf:
            lines.append(bf)
        # Always include canonical source in note for auditability.
        lines.append(f"  note = {{{canon}}}")
        lines.append("}\n")
    return "\n".join(lines)


def to_ris(sources: List[Dict[str, Any]]) -> str:
    sources_sorted = sorted(sources, key=lambda x: _as_str(x.get("canonical")))
    lines: List[str] = []
    for s in sources_sorted:
        canon = _as_str(s.get("canonical"))
        kind = _as_str(s.get("kind"))
        meta = s.get("meta") if isinstance(s.get("meta"), dict) else {}
        title = _as_str(meta.get("title")).strip()
        year = _as_str(meta.get("year")).strip()

        ty = "JOUR" if kind in ("pmid", "doi") else "GEN"
        lines.append(f"TY  - {ty}")
        if title:
            lines.append(f"TI  - {title}")
        if year:
            lines.append(f"PY  - {year}")
        if kind == "doi":
            doi = canon.split(":", 1)[1]
            lines.append(f"DO  - {doi}")
        lines.append(f"ID  - {canon}")
        lines.append("ER  -")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"

