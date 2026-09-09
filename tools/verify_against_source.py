#!/usr/bin/env python3
"""
Verify the MITA JSON dataset against its source CMS PDFs.

This checker has two layers:

  Structural  (no dependencies) - schema shape, naming consistency, referential
              integrity, required-field population, BCM/BPT pairing.
  Fidelity    (requires PyMuPDF) - compares transcribed text against the source
              PDFs and detects known extraction artifacts: page-header
              contamination, bullet-marker leakage, and hyphen line-break splits.

Usage:
    .venv/bin/python tools/verify_against_source.py
    .venv/bin/python tools/verify_against_source.py --structural-only
    .venv/bin/python tools/verify_against_source.py --area care_management
    .venv/bin/python tools/verify_against_source.py --verbose

Exit codes:
    0  no errors (warnings may be present)
    1  one or more errors
    2  the check could not run meaningfully (no files found, missing dependency)

Design note: this script exits 2 rather than 0 when it finds nothing to inspect.
A validator that reports success on an empty file set is worse than no validator.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")

EXPECTED_TOTAL = 152
EXPECTED_PER_TYPE = 76

BCM_TOP_KEYS = {
    "document_type", "version", "version_date", "business_area", "sub_category",
    "process_name", "process_code", "process_id", "maturity_model", "metadata",
}
BPT_TOP_KEYS = {
    "document_type", "version", "version_date", "business_area", "sub_category",
    "process_name", "process_code", "process_id", "process_details", "metadata",
}
BPT_DETAIL_KEYS = {
    "description", "trigger_events", "results", "process_steps", "diagrams",
    "shared_data", "predecessor_processes", "successor_processes", "constraints",
    "failures", "performance_measures",
}
# Present only on records whose source pages carry numbered reference tables.
# Exactly one record in the corpus does: EE_Determine_Member_Eligibility_BPT,
# whose steps cite "Table 1" through "Table 7". Optional, so its absence from
# the other 75 BPT records is not a finding.
BPT_OPTIONAL_DETAIL_KEYS = {"reference_tables"}
REFERENCE_TABLE_KEYS = {"table_number", "title", "page_reference", "rows"}
REFERENCE_ROW_KEYS = {"authority", "eligibility_group"}

LEVEL_KEYS = {"level_1", "level_2", "level_3", "level_4", "level_5"}
TRIGGER_KEYS = {"environment_based", "interaction_based"}

# ---------------------------------------------------------------------------
# Step-structure constants
#
# `process_steps` is a flat list mixing two kinds of entry: numbered steps
# ("1. START: ...") and verbatim scenario headings from the source ("Capitation
# Payment", "Alternate Path: Suspended Claim"). A heading is any entry that does
# not open with "<digits>.".
#
# Numbering restarts at 1 for each scenario, which is faithful to the source, so
# step numbers are NOT unique within a record. The checks below assert the shape
# that makes those restarts legible rather than trying to force one sequence.
# ---------------------------------------------------------------------------

# Records whose source genuinely does not begin at step 1. CMS carried the
# numbering over from the preceding process (Manage TPL Recovery ends at 9), so
# Manage Estate Recovery is published as steps 10-21 with no 1-9 anywhere. The
# transcription is correct; the defect is CMS's. See docs/SOURCE_DEFECTS.md.
#
# Keyed by `process_id` rather than filename: the filename carries a version, so
# a version bump would silently drop the exemption, whereas `process_id` is the
# record's identity and is already checked for uniqueness.
STEP_START_EXCEPTIONS = {
    "FM_MANAGE_ESTATE_RECOVERY": 10,
}

# Cascade suppressor, not the detector. A CFR citation split at its period leaves
# "435." heading an entry, which reads as step 435; skipping it keeps `previous`
# on the last real step so one bad entry yields one error instead of two. The
# check that actually detects a split is the sequence test below - a low
# fragment such as "4." passes this threshold and is caught by colliding with
# the real step 4. Do not rely on this constant as the guard against splits.
MAX_PLAUSIBLE_STEP_NUMBER = 60

# Loose sanity bound on a scenario heading, not a discriminator. Heading lengths
# are bimodal: 17 are short labels of 10-46 characters ("Manage FMAP",
# "Alternate Path: Suspended Claim"), while 3 run 278-416 because CMS writes a
# paragraph of guidance as the label (CM_Authorize_Referral, CM_Authorize_Service,
# EE_Determine_Provider_Eligibility). No single threshold separates a long
# legitimate heading from a swallowed step body, so this only catches an egregious
# case. EXPECTED_SCENARIO_HEADINGS below is the real guard - it catches any entry
# misclassified as a heading whatever its length.
MAX_HEADING_LENGTH = 500

# Scenario headings across the corpus. Classification is by exclusion - anything
# not matching "<digits>." is treated as a heading - so this count is what catches
# debris misclassified as a heading, and a heading silently lost by a
# re-extraction, in both directions.
EXPECTED_SCENARIO_HEADINGS = 20

# A figure occupies one region of one page, so a page should contribute one diagram,
# or a small number if it carries several. Well above that means the extraction
# recorded the fragments a figure is composed of rather than the figure.
MAX_DIAGRAMS_PER_PAGE = 3

# Minimum distinct colours for an image to be a figure rather than extraction debris.
#
# The 76 images this record previously shipped were single vector shapes pulled out of
# the page: a blank grey box, a black box with mirrored text. Every one of them had
# exactly **2** distinct colours; the nine real figure renders have 528 to 1057. So
# the threshold sits two orders of magnitude clear of both sides.
#
# Note that modal-colour fraction does *not* separate them - the debris ranged 0.51 to
# 0.98 and the real figures 0.70 to 0.87, which overlap. Colour count is the measure
# that works.
MIN_DIAGRAM_COLOURS = 16

# Legend and connector labels from the swim-lane figures. These sit in the PDF
# text layer at a smaller font than step body text, so they can be swept into a
# step when extraction ignores font size. The figures themselves are recorded in
# `diagrams`, so this text is debris wherever it appears in prose.
#
# A hardcoded list only catches the legend, not every box label, and adding
# phrases one at a time is whack-a-mole. See "Not established - placement" in
# tools/README.md for what this does and does not reach.
FLOWCHART_FRAGMENTS = [
    "Dual Paths", "Process No Yes", "Continue End", "No Yes No Yes",
]

# Labels from the source table's left-hand "Item" column. They delimit the record's
# fields rather than belonging to any of them, so one arriving at the end of a step
# means the extraction ran past the end of the step's own cell.
#
# Matched only after a sentence terminator, because these words occur in ordinary
# step prose too - "5. Determine performance measures" and "7. Record the results"
# are legitimate steps, and "Alternate Path: Third Party Liability Failures" is a
# legitimate scenario heading. Requiring "." or ";" or ":" before the label
# distinguishes an appended row label from a sentence that happens to end on the
# same word: 0 false positives across the corpus.
ITEM_COLUMN_LABELS = [
    "Business Process Steps", "Performance Measures", "Trigger Events",
    "Trigger Event", "Process Steps", "Predecessors", "Verifications",
    "Description", "Constraints", "Shared Data", "Predecessor", "Successors",
    "Successor", "Failures", "Results", "Result",
]
ITEM_LABEL_TAIL_RX = re.compile(
    r"[.;:]\s+(" + "|".join(re.escape(x) for x in
                            sorted(ITEM_COLUMN_LABELS, key=len, reverse=True))
    + r")\s*$", re.IGNORECASE)

CODE_TO_AREA = {
    "BR": "Business Relationship Management",
    "CM": "Care Management",
    "CO": "Contractor Management",
    "EE": "Eligibility and Enrollment Management",
    "FM": "Financial Management",
    "OM": "Operations Management",
    "PE": "Performance Management",
    "PL": "Plan Management",
    "PM": "Provider Management",
}

# Text that must never appear inside transcribed content: PDF running headers
# and footers from the Appendix C / Appendix D page furniture.
# Compared after canon(), which normalises every dash to U+002D, so these are
# written in that normalised form. Includes the per-page footer, which is the
# furniture sitting closest to table content at a page break and so the most
# likely to be spliced in.
_HEADER_ARTIFACT_SOURCE = [
    "Part I - Business Architecture", "Part I Part 1 - Business Architecture",
    "Appendix C- Business Process", "Appendix D - Business Capability Matrix",
    "Part I, Appendix C - Page", "Part I, Appendix D - Page",
    "Model Details", "Matrix Details", "Version 3.0", "May 2014",
]

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def squash(text: str) -> str:
    """Collapse all whitespace runs to single spaces."""
    return re.sub(r"\s+", " ", text).strip()


def canon(text: str) -> str:
    """Normalise text for comparison against PDF-extracted text.

    Unifies curly quotes, rejoins hyphen line-breaks, drops bullet glyphs, and
    collapses whitespace. Deliberately lossy: it exists so that cosmetic
    differences do not mask substantive ones.
    """
    text = (text.replace("\u2019", "'").replace("\u2018", "'")
                .replace("\u201c", '"').replace("\u201d", '"')
                .replace("\u2013", "-").replace("\u2014", "-")
                .replace("\u2010", "-").replace("\u2011", "-"))
    text = re.sub(r"[\uf0a7\uf0b7\u2022\u25aa\u25cf]", " ", text)
    text = re.sub(r"-\s+", "-", text)          # rejoin hyphen line-breaks
    return squash(text)


# Normalised at import so the literals match the canon()-ed content they are
# compared against. Writing them pre-normalised by hand does not work: canon()
# also collapses "- " to "-", which silently killed every entry containing a
# spaced dash - including the page footer, the furniture most likely to be
# spliced into a cell at a page break.
HEADER_ARTIFACTS = None          # populated below, after canon() is defined


def tokenise(text: str):
    """Lower-cased alphanumeric words, for attestation against the source."""
    return re.findall(r"[a-z0-9]+", text.lower())


# Function words that a complete sentence does not end on. A field ending here,
# with no terminal punctuation, is the signature of text lost at a page break -
# the sibling of the truncated-word case, and invisible to token attestation
# because every word present is still a real word from the right pages.
DANGLING_TAIL = {
    "to", "for", "and", "or", "the", "a", "an", "of", "in", "on", "at", "by",
    "with", "from", "via", "is", "are", "was", "were", "be", "been", "as",
    "that", "which", "this", "these", "those", "not", "if", "when", "into",
    "than", "then", "per", "including", "include", "includes", "such",
    "between", "through", "under", "over", "about", "after", "before",
    "during", "but", "both", "either", "neither", "also", "may", "will",
    "shall", "can", "must", "should",
}


def dangling_tail(text: str):
    """Return the offending tail word if `text` looks truncated, else None.

    Only the final line is judged: an interior line ending in a function word is
    simply mid-sentence and continues on the next. An enumeration ending in
    "; or" or ", and" is authored list syntax, not a truncation.
    """
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        return None
    last = lines[-1]
    if len(last) < 12 or last[-1] in '.?!:;)%_"”’':
        return None
    words = re.findall(r"[A-Za-z0-9']+", last)
    if not words or words[-1].lower() not in DANGLING_TAIL:
        return None
    # "...; or" / "..., and" is a list continuation the source wrote that way
    if re.search(r"[;,]\s+(or|and)$", last, re.I):
        return None
    return words[-1]


HEADER_ARTIFACTS = [canon(a) for a in _HEADER_ARTIFACT_SOURCE]
assert all(canon(a) == a for a in HEADER_ARTIFACTS), \
    "HEADER_ARTIFACTS must be canon()-stable, or the comparison silently fails"


def iter_strings(obj, path=""):
    """Yield (json_path, string) for every string leaf."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from iter_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


# Strings shorter than this are skipped by the trace: short fragments like
# "Fingerprinting" or "Maturity level is not applicable." carry little signal and
# recur across the corpus, so tracing them adds noise rather than assurance.
# Their surrounding context is covered by the longer strings around them.
MIN_TRACE_LENGTH = 25


def traceable_text(doc):
    """Yield (json_path, text) for every substantive content string.

    Covers every field whose text comes from the source document: BCM questions,
    notes, categories and all five level descriptions; BPT descriptions, steps,
    results, shared data, predecessors, successors, failures, performance
    measures, constraints, trigger events, and reference-table titles and cells.

    Excluded: metadata, `document_type` and other fixed enumerations, and the
    `diagrams` entries. Diagram filenames and descriptions ("Process diagram from
    page 2") are generated by the extraction tooling rather than transcribed, so
    attesting them against the source would be meaningless.
    """
    if doc.get("document_type") == "BCM":
        for i, q in enumerate(doc.get("maturity_model", {}).get("capability_questions", [])):
            base = f"q{i}"
            for field in ("question", "note"):
                if q.get(field):
                    yield f"{base}.{field}", q[field]
            for key in sorted(q.get("levels", {})):
                if q["levels"][key]:
                    yield f"{base}.{key}", q["levels"][key]
            if q.get("category"):
                yield f"{base}.category", q["category"]
    else:
        details = doc.get("process_details", {})
        for field in ("predecessor_processes", "successor_processes"):
            for i, item in enumerate(details.get(field) or []):
                if isinstance(item, str) and item:
                    yield f"{field}[{i}]", item
        for field in ("description", "constraints"):
            if details.get(field):
                yield field, details[field]
        for field in ("results", "process_steps", "shared_data", "failures",
                      "performance_measures"):
            for i, item in enumerate(details.get(field) or []):
                if isinstance(item, str) and item:
                    yield f"{field}[{i}]", item
        for kind in ("environment_based", "interaction_based"):
            for i, item in enumerate((details.get("trigger_events") or {}).get(kind) or []):
                if isinstance(item, str) and item:
                    yield f"trigger_events.{kind}[{i}]", item
        # Reference-table titles and cells are transcribed from the source, so they
        # belong under the same attestation as every other transcribed field.
        # Without this, a rotated citation or a fabricated CFR section would ship
        # silently - the structural checks only see shape, not content.
        #
        # Note that token attestation alone cannot catch a *swapped* pairing, since
        # both strings still occur in the source. check_reference_table_pairing()
        # covers that case.
        for i, tb in enumerate((details.get("reference_tables") or [])):
            if not isinstance(tb, dict):
                continue
            if tb.get("title"):
                yield f"reference_tables[{i}].title", tb["title"]
            for j, row in enumerate(tb.get("rows") or []):
                if not isinstance(row, dict):
                    continue
                for key in ("authority", "eligibility_group"):
                    if row.get(key):
                        yield f"reference_tables[{i}].rows[{j}].{key}", row[key]


def slugify_process(code: str, name: str) -> str:
    """Canonical process_id: CODE_UPPER_SNAKE_NAME."""
    slug = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").upper()
    return f"{code}_{slug}"


def window_start(text: str, pos: int, words: int) -> int:
    """Character offset `words` whitespace-separated tokens before `pos`.

    `text` is always canon()-ed, so whitespace runs are already collapsed.
    """
    i = pos
    for _ in range(words + 1):
        j = text.rfind(" ", 0, i)
        if j < 0:
            return 0
        i = j
    return i + 1


def window_end(text: str, pos: int, words: int) -> int:
    """Character offset `words` whitespace-separated tokens after `pos`."""
    i = pos
    for _ in range(words):
        j = text.find(" ", i + 1)
        if j == -1:
            return len(text)
        i = j
    return i


# A wrapped table cell splits into at most two pieces: the part before the page
# or line break and the part after. Allowing more lets fabricated text assemble
# itself out of unrelated scraps of the same page span.
MIN_FRAGMENT = 12
MIN_TAIL_FRAGMENT = 4
MAX_FRAGMENTS = 2


def source_fragments(text: str, flat: str, page_starts=None):
    """Decompose `text` into contiguous fragments of `flat`, in order.

    A table cell that wraps onto another line - or across a page break - is
    split in the raw PDF text stream by the neighbouring columns and the running
    header. Correctly reassembled text therefore will not appear verbatim in
    `flat`, even though every piece of it does, in order.

    Returns the fragment list when `text` decomposes into at most
    MAX_FRAGMENTS pieces that each appear in `flat` at strictly increasing
    positions, otherwise None. When `page_starts` is given, the split must also
    straddle a page boundary - every genuine wrapped cell in this corpus does,
    whereas a fragmentation caused by a dropped word usually does not.

    This is a weaker guarantee than exact containment, so callers must pass a
    `flat` scoped to the record's own page span. Given the whole document it
    would happily assemble a question out of fragments belonging to a different
    process. Reordered content fails; content that merely repeats a phrase found
    elsewhere in the span can still pass, so the reported fragments are printed
    for a human to judge.
    """
    def boundaries(s):
        """Candidate split offsets, longest first. A cell can only break between
        words, so word boundaries are the complete candidate set - enumerating
        them avoids both the cost and the incompleteness of scanning every
        character length."""
        out = [len(s)]
        out.extend(m.start() for m in re.finditer(r"\s", s))
        return sorted(set(out), reverse=True)

    def split_at(remaining, search_from, depth):
        if not remaining:
            return []
        if depth >= MAX_FRAGMENTS:
            return None
        # Try every word-boundary split, longest first. A greedy longest-match-only
        # search gives false negatives: where the same phrase occurs twice in the
        # span with different break points, the longest match belongs to the wrong
        # occurrence and leaves an unmatchable remainder.
        for size in boundaries(remaining):
            floor = MIN_TAIL_FRAGMENT if size >= len(remaining) else MIN_FRAGMENT
            if size < floor:
                continue
            at = flat.find(remaining[:size], search_from)
            while at != -1:
                rest = remaining[size:].lstrip()
                if rest and page_starts is not None:
                    nxt = flat.find(rest[:max(MIN_TAIL_FRAGMENT, min(len(rest), 24))],
                                    at + size)
                    if nxt == -1 or not any(at + size <= b <= nxt for b in page_starts):
                        at = flat.find(remaining[:size], at + 1)
                        continue
                tail = split_at(rest, at + size, depth + 1)
                if tail is not None:
                    return [remaining[:size]] + tail
                # the same prefix may occur again later with a usable remainder
                at = flat.find(remaining[:size], at + 1)
        return None

    if len(text) > 4000:            # guard: unmatchable long input is O(n^2.4)
        return None
    return split_at(text, 0, 0)


# --------------------------------------------------------------------------
# findings
# --------------------------------------------------------------------------

@dataclass
class Report:
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    stats: Counter = field(default_factory=Counter)

    def error(self, filename, message, detail=""):
        self.errors.append((filename, message, detail))

    def warn(self, filename, message, detail=""):
        self.warnings.append((filename, message, detail))


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------

def load_dataset(area_filter=None):
    """Return list of (relative_path, parsed_json). Raises on unreadable JSON."""
    records, broken = [], []
    for doc_type in ("bcm", "bpt"):
        type_dir = os.path.join(DATA_DIR, doc_type)
        if not os.path.isdir(type_dir):
            continue
        for area in sorted(os.listdir(type_dir)):
            area_path = os.path.join(type_dir, area)
            if not os.path.isdir(area_path):
                continue
            if area_filter and area != area_filter:
                continue
            for name in sorted(os.listdir(area_path)):
                if not name.endswith(".json"):
                    continue
                abs_path = os.path.join(area_path, name)
                rel = os.path.relpath(abs_path, REPO_ROOT)
                try:
                    with open(abs_path, encoding="utf-8") as fh:
                        records.append((rel, json.load(fh)))
                except json.JSONDecodeError as exc:
                    broken.append((rel, f"invalid JSON: {exc}"))
    return records, broken


# --------------------------------------------------------------------------
# structural checks
# --------------------------------------------------------------------------

def check_structure(records, rep: Report, area_filter=None):
    bcm_ids, bpt_ids = defaultdict(list), defaultdict(list)

    for rel, doc in records:
        base = os.path.basename(rel)
        doc_type = doc.get("document_type")
        rep.stats[f"files_{doc_type}"] += 1

        # --- top-level key shape
        expected = BCM_TOP_KEYS if doc_type == "BCM" else BPT_TOP_KEYS
        actual = set(doc.keys())
        for missing in sorted(expected - actual):
            rep.error(base, f"missing top-level field: {missing}")
        for extra in sorted(actual - expected):
            rep.warn(base, f"unexpected top-level field: {extra}")

        # --- constants
        if doc.get("version") != "3.0":
            rep.error(base, f"version is {doc.get('version')!r}, expected '3.0'")
        if doc.get("version_date") != "May 2014":
            rep.error(base, f"version_date is {doc.get('version_date')!r}")

        # --- filename agreement
        m = re.match(r"^([A-Z]{2})_(.+)_(BCM|BPT)_v3\.0\.json$", base)
        if not m:
            rep.error(base, "filename does not match [CODE]_[Name]_[BCM|BPT]_v3.0.json")
        else:
            fcode, fname, ftype = m.groups()
            if fcode != doc.get("process_code"):
                rep.error(base, f"process_code {doc.get('process_code')!r} != filename {fcode!r}")
            if ftype != doc_type:
                rep.error(base, f"document_type {doc_type!r} != filename {ftype!r}")
            norm = lambda s: re.sub(r"[^a-z0-9]+", "", s.lower())
            if norm(fname) != norm(doc.get("process_name", "")):
                rep.error(base, f"process_name {doc.get('process_name')!r} != filename {fname!r}")

        # --- code / area / directory agreement
        code = doc.get("process_code")
        if code in CODE_TO_AREA and doc.get("business_area") != CODE_TO_AREA[code]:
            rep.error(base, f"business_area {doc.get('business_area')!r} does not match code {code}")
        dir_area = rel.split(os.sep)[2]
        if code in CODE_TO_AREA:
            expect_dir = re.sub(r"[^a-z0-9]+", "_", CODE_TO_AREA[code].lower())
            if dir_area != expect_dir:
                rep.error(base, f"located in {dir_area}/, expected {expect_dir}/")

        # --- process_id
        pid = doc.get("process_id")
        if pid:
            want = slugify_process(code, doc.get("process_name", ""))
            # process_id is canonical and may legitimately differ from
            # process_name where CMS spells the process differently in the
            # BPT and BCM documents. Only the prefix is mandatory.
            if not pid.startswith(f"{code}_"):
                rep.error(base, f"process_id {pid!r} does not start with {code}_")
            (bcm_ids if doc_type == "BCM" else bpt_ids)[pid].append(base)
            if pid != want:
                rep.stats["process_id_differs_from_name"] += 1

        # --- metadata
        meta = doc.get("metadata", {})
        for extra in sorted(set(meta) - {"source_file", "source_page_range",
                                         "extracted_date", "manually_corrected",
                                         "source_process_name"}):
            rep.warn(base, f"unexpected metadata field {extra!r}")
        for req in ("source_file", "source_page_range", "extracted_date"):
            if not meta.get(req):
                rep.error(base, f"metadata.{req} missing or empty")
        src = meta.get("source_file", "")
        if src and not os.path.exists(os.path.join(REPO_ROOT, src)):
            rep.error(base, f"metadata.source_file does not exist: {src}")
        if meta.get("source_page_range") and not re.match(r"^\d+(-\d+)?$", str(meta["source_page_range"])):
            rep.error(base, f"malformed source_page_range: {meta['source_page_range']!r}")

        # --- type-specific
        if doc_type == "BCM":
            check_bcm_body(base, doc, rep)
        elif doc_type == "BPT":
            check_bpt_body(base, doc, rep, rel)
        else:
            rep.error(base, f"unknown document_type: {doc_type!r}")

    # --- process_id must be unique within a document type, and must pair
    #
    # Uniqueness is the whole point of the field: a duplicate would silently
    # collapse two processes into one for any consumer indexing by it, which is
    # the failure mode process_id exists to prevent.
    for doc_type, ids in (("BCM", bcm_ids), ("BPT", bpt_ids)):
        for pid, files in sorted(ids.items()):
            if len(files) > 1:
                rep.error(files[0],
                          f"process_id {pid} is not unique among {doc_type} records",
                          ", ".join(sorted(files)))

    if area_filter is None:
        for pid, files in sorted(bcm_ids.items()):
            if pid not in bpt_ids:
                rep.error(files[0], f"BCM has no BPT counterpart for process_id {pid}")
        for pid, files in sorted(bpt_ids.items()):
            if pid not in bcm_ids:
                rep.error(files[0], f"BPT has no BCM counterpart for process_id {pid}")


def check_bcm_body(base, doc, rep: Report):
    questions = doc.get("maturity_model", {}).get("capability_questions")
    if not questions:
        rep.error(base, "maturity_model.capability_questions missing or empty")
        return
    rep.stats["bcm_questions"] += len(questions)

    seen = set()
    for i, q in enumerate(questions):
        tag = f"q{i}"
        allowed = {"category", "question", "levels", "note"}
        for extra in sorted(set(q.keys()) - allowed):
            rep.warn(base, f"{tag}: unexpected field {extra!r}")
        for req in ("category", "question", "levels"):
            if req not in q:
                rep.error(base, f"{tag}: missing {req!r}")

        text = (q.get("question") or "").strip()
        if not text:
            rep.error(base, f"{tag}: empty question")
        elif text in seen:
            rep.error(base, f"{tag}: duplicate question text {text[:60]!r}")
        else:
            seen.add(text)

        # A question containing a '?' followed by more text is the signature of
        # two source questions merged across a page break.
        if re.search(r"\?\s+\S", text):
            rep.error(base, f"{tag}: text continues past '?' - likely two merged questions",
                      text[:150])
        # Duplicated tail from table-cell wrapping, e.g. "... process? appeals process?"
        if text.count("?") > 1:
            rep.error(base, f"{tag}: multiple '?' in question text", text[:150])

        levels = q.get("levels", {})
        for missing in sorted(LEVEL_KEYS - set(levels)):
            rep.error(base, f"{tag}: missing {missing}")
        for extra in sorted(set(levels) - LEVEL_KEYS):
            rep.error(base, f"{tag}: unexpected level key {extra!r}")
        for key in sorted(LEVEL_KEYS & set(levels)):
            if not (levels[key] or "").strip():
                rep.error(base, f"{tag}.{key}: empty")
            rep.stats["bcm_levels"] += 1

        if "note" in q and not (q["note"] or "").strip():
            rep.error(base, f"{tag}: note present but empty")


def present_citations(details):
    """Table numbers the process steps cite by number, e.g. "See ... Table 4"."""
    return {int(n) for s in (details.get("process_steps") or [])
            if isinstance(s, str)
            for n in re.findall(r"\bTable (\d+)\b", s)}


def check_bpt_body(base, doc, rep: Report, rel):
    details = doc.get("process_details")
    if not isinstance(details, dict):
        rep.error(base, "process_details missing")
        return
    for missing in sorted(BPT_DETAIL_KEYS - set(details)):
        rep.error(base, f"process_details missing {missing!r}")
    for extra in sorted(set(details) - BPT_DETAIL_KEYS - BPT_OPTIONAL_DETAIL_KEYS):
        rep.warn(base, f"process_details has unexpected field {extra!r}")

    if not (details.get("description") or "").strip():
        rep.error(base, "empty description")
    if not (details.get("constraints") or "").strip():
        rep.error(base, "empty constraints")

    for key in ("results", "process_steps", "shared_data", "predecessor_processes",
                "successor_processes", "failures", "performance_measures"):
        value = details.get(key)
        if not isinstance(value, list):
            rep.error(base, f"process_details.{key} is not a list")
            continue
        if not value:
            rep.error(base, f"process_details.{key} is empty")
        for i, item in enumerate(value):
            if not isinstance(item, str):
                rep.error(base, f"{key}[{i}] is not a string")
            elif not item.strip():
                rep.error(base, f"{key}[{i}] is empty")
            elif len(item.strip()) < 3:
                rep.error(base, f"{key}[{i}] is degenerate: {item!r}")
    rep.stats["bpt_steps"] += len(details.get("process_steps") or [])

    triggers = details.get("trigger_events")
    if not isinstance(triggers, dict):
        rep.error(base, "trigger_events is not an object")
    else:
        for missing in sorted(TRIGGER_KEYS - set(triggers)):
            rep.error(base, f"trigger_events missing {missing!r}")
        for extra in sorted(set(triggers) - TRIGGER_KEYS):
            rep.error(base, f"trigger_events has unexpected key {extra!r}")
        if not any(triggers.get(k) for k in TRIGGER_KEYS):
            rep.error(base, "no trigger events of either kind")

    # reference_tables - optional, present only where the source carries them
    if "reference_tables" in details:
        tables = details["reference_tables"]
        if not isinstance(tables, list) or not tables:
            rep.error(base, "reference_tables present but not a non-empty list")
        else:
            page_range = (doc.get("metadata") or {}).get("source_page_range") or ""
            bounds = re.match(r"^(\d+)-(\d+)$", page_range.strip())
            seen = []
            for i, tb in enumerate(tables):
                tag = f"reference_tables[{i}]"
                if not isinstance(tb, dict):
                    rep.error(base, f"{tag} is not an object")
                    continue
                for missing in sorted(REFERENCE_TABLE_KEYS - set(tb)):
                    rep.error(base, f"{tag} missing {missing!r}")
                for extra in sorted(set(tb) - REFERENCE_TABLE_KEYS):
                    rep.warn(base, f"{tag} unexpected field {extra!r}")
                num = tb.get("table_number")
                if not isinstance(num, int):
                    rep.error(base, f"{tag}.table_number is not an integer")
                else:
                    seen.append(num)
                if not str(tb.get("title") or "").strip():
                    rep.error(base, f"{tag}.title is empty")
                page = tb.get("page_reference")
                if not isinstance(page, int):
                    rep.error(base, f"{tag}.page_reference is not an integer")
                elif bounds and not (int(bounds.group(1)) <= page <= int(bounds.group(2))):
                    rep.error(base, f"{tag}.page_reference {page} outside "
                                    f"source_page_range {page_range}")
                rows = tb.get("rows")
                if not isinstance(rows, list) or not rows:
                    rep.error(base, f"{tag}.rows is not a non-empty list")
                    continue
                for j, row in enumerate(rows):
                    rtag = f"{tag}.rows[{j}]"
                    if not isinstance(row, dict):
                        rep.error(base, f"{rtag} is not an object")
                        continue
                    for missing in sorted(REFERENCE_ROW_KEYS - set(row)):
                        rep.error(base, f"{rtag} missing {missing!r}")
                    for extra in sorted(set(row) - REFERENCE_ROW_KEYS):
                        rep.warn(base, f"{rtag} unexpected field {extra!r}")
                    for key in sorted(REFERENCE_ROW_KEYS & set(row)):
                        if not str(row.get(key) or "").strip():
                            rep.error(base, f"{rtag}.{key} is empty")
                    rep.stats["reference_table_rows"] += 1
            rep.stats["reference_tables"] += len(tables)
            if seen and seen != list(range(1, len(seen) + 1)):
                rep.error(base, "reference_tables table_number values are not 1..N "
                                "in document order", str(seen))
            for n in sorted(set(seen) - present_citations(details)):
                rep.warn(base, f"reference_tables has Table {n} but no step cites it")

    # A table a step cites must resolve. This runs whether or not the record has a
    # `reference_tables` field, because the state it guards against is precisely a
    # record that cites a table and carries no tables - a dangling reference this
    # dataset would own rather than CMS.
    resolvable = {tb.get("table_number")
                  for tb in (details.get("reference_tables") or [])
                  if isinstance(tb, dict)}
    for n in sorted(present_citations(details) - resolvable):
        rep.error(base, f"steps cite Table {n} but no such table is present in "
                        f"reference_tables")

    # diagrams
    diagrams = details.get("diagrams")
    if not isinstance(diagrams, list):
        rep.error(base, "diagrams is not a list")
        return
    page_range = (doc.get("metadata") or {}).get("source_page_range") or ""
    bounds = re.match(r"^(\d+)-(\d+)$", page_range.strip())
    referenced, descriptions, per_page = set(), [], Counter()
    for i, dg in enumerate(diagrams):
        if not isinstance(dg, dict):
            rep.error(base, f"diagrams[{i}] is not an object")
            continue
        for req in ("filename", "description", "page_reference"):
            if req not in dg:
                rep.error(base, f"diagrams[{i}] missing {req!r}")
        rep.stats["diagrams"] += 1
        # images live in an images/ directory beside the JSON file
        name = dg.get("filename")
        if name:
            referenced.add(name)
            img = os.path.join(REPO_ROOT, os.path.dirname(rel), "images", name)
            if not os.path.exists(img):
                rep.error(base, f"diagrams[{i}] filename not on disk: {name}")
        page = dg.get("page_reference")
        if not isinstance(page, int):
            rep.error(base, f"diagrams[{i}].page_reference is not an integer")
        else:
            per_page[page] += 1
            if bounds and not (int(bounds.group(1)) <= page <= int(bounds.group(2))):
                rep.error(base, f"diagrams[{i}].page_reference {page} outside "
                                f"source_page_range {page_range}")
        text = str(dg.get("description") or "").strip()
        if not text:
            rep.error(base, f"diagrams[{i}].description is empty")
        else:
            descriptions.append(text)

    # A figure is one region of one page. A page credited with many "diagrams" means
    # the extraction pulled out the fragments a figure is composed of and called each
    # one a diagram - which is exactly what this record shipped: 76 entries, all
    # page 2, all describing the same figure.
    for page, count in sorted(per_page.items()):
        if count > MAX_DIAGRAMS_PER_PAGE:
            rep.error(base, f"{count} diagram entries all cite page {page} - figure "
                            f"fragments recorded as separate diagrams?")
    duplicated = {text for text, n in Counter(descriptions).items() if n > 1}
    for text in sorted(duplicated):
        rep.error(base, f"diagram description is not unique within the record: "
                        f"{text[:70]!r}")

    # Orphan detection needs every record that shares the directory, so it cannot be
    # done here - an images/ directory is per business area, not per record. See
    # check_orphan_images().


def check_diagram_images(records, fitz_module, rep: Report):
    """Assert each diagram image actually contains a figure.

    The structural checks can see that a file exists and that a page is not credited
    with a suspicious number of diagrams. Neither can see that a file is blank, and
    this record shipped 76 files that were: single vector shapes lifted out of the
    page, including an empty grey box and a black box carrying the word "Eligible"
    upside down. Every check in the suite passed them, because a blank PNG is a real
    file at a real path.

    Distinct colour count is the discriminator. See MIN_DIAGRAM_COLOURS.
    """
    for rel, doc in records:
        diagrams = (doc.get("process_details") or {}).get("diagrams")
        if not diagrams:
            continue
        base = os.path.basename(rel)
        for i, dg in enumerate(diagrams):
            if not isinstance(dg, dict):
                continue
            name = dg.get("filename")
            if not name:
                continue
            path = os.path.join(REPO_ROOT, os.path.dirname(rel), "images", name)
            if not os.path.exists(path):
                continue        # absence is already an error from the structural pass
            try:
                pixmap = fitz_module.Pixmap(path)
                if pixmap.alpha:
                    pixmap = fitz_module.Pixmap(pixmap, 0)
            except Exception as exc:                      # noqa: BLE001
                rep.error(base, f"diagrams[{i}] image could not be decoded: {name}",
                          str(exc))
                continue
            # Subsampled: a full scan of nine renders is wasted work, and a figure's
            # colour variety shows up in any reasonable sample.
            pixel_count = pixmap.width * pixmap.height
            stride = max(1, pixel_count // 20000)
            channels, samples = pixmap.n, pixmap.samples
            colours = {samples[p * channels:(p + 1) * channels]
                       for p in range(0, pixel_count, stride)}
            if len(colours) < MIN_DIAGRAM_COLOURS:
                rep.error(base,
                          f"diagrams[{i}] image is effectively blank - "
                          f"{len(colours)} distinct colour(s), expected at least "
                          f"{MIN_DIAGRAM_COLOURS}: {name}")


def check_reference_table_pairing(records, index, rep: Report):
    """Assert each table row pairs the authority CMS printed beside that group.

    A row attaches a statutory citation to an eligibility group, so a pairing
    error is the most consequential defect this field can carry - it would tell a
    reader that a group is authorised by a regulation that does not authorise it.
    Token attestation cannot catch it: swapping two groups leaves every token
    present in the source, so the fidelity layer passes.

    What does catch it is reading order. In the PDF the left cell of a row is
    followed immediately by the right cell of the same row, so "<authority>
    <eligibility_group>" is contiguous in the extracted text for a correct row and
    is not for a swapped one. Verified against all 57 rows in the corpus.
    """
    for rel, doc in records:
        details = doc.get("process_details") or {}
        tables = details.get("reference_tables")
        if not tables:
            continue
        base = os.path.basename(rel)
        meta = doc.get("metadata") or {}
        src = meta.get("source_file")
        bounds = re.match(r"^(\d+)-(\d+)$", str(meta.get("source_page_range") or "").strip())
        if not src or not bounds or not os.path.exists(os.path.join(REPO_ROOT, src)):
            continue
        pages = index.pages(src)
        lo, hi = int(bounds.group(1)), int(bounds.group(2))
        haystack = canon("".join(pages[lo - 1:min(hi, len(pages))]))
        for i, tb in enumerate(tables):
            if not isinstance(tb, dict):
                continue
            for j, row in enumerate(tb.get("rows") or []):
                if not isinstance(row, dict):
                    continue
                authority = str(row.get("authority") or "")
                group = str(row.get("eligibility_group") or "")
                if not authority or not group:
                    continue
                if canon(f"{authority} {group}") not in haystack:
                    rep.error(base,
                              f"reference_tables[{i}].rows[{j}]: authority and "
                              f"eligibility_group are not adjacent in the source - "
                              f"pairing may be wrong",
                              f"{authority} | {group}")


def check_orphan_images(records, rep: Report):
    """An image on disk that no record's `diagrams` entry claims.

    Aggregated per directory rather than per record, because `images/` sits beside the
    JSON files and is therefore shared by every record in a business area. Checking it
    per record reports each of the area's other records as owning nothing, which is
    seven false findings per area here rather than one true one.

    A warning, not an error: an unreferenced file wastes space and misleads a reader
    about what the dataset contains, but it corrupts nothing.
    """
    claimed = defaultdict(set)
    directories = set()
    for rel, doc in records:
        image_dir = os.path.join(os.path.dirname(rel), "images")
        if os.path.isdir(os.path.join(REPO_ROOT, image_dir)):
            directories.add(image_dir)
        for dg in (doc.get("process_details") or {}).get("diagrams") or []:
            if isinstance(dg, dict) and dg.get("filename"):
                claimed[image_dir].add(dg["filename"])
    for image_dir in sorted(directories):
        on_disk = {n for n in os.listdir(os.path.join(REPO_ROOT, image_dir))
                   if not n.startswith(".")}
        for orphan in sorted(on_disk - claimed[image_dir]):
            rep.warn("<dataset>", f"{image_dir}/{orphan} is on disk but no diagram "
                                  f"entry references it")


def check_step_structure(records, rep: Report):
    """Assert the shape of `process_steps`, which fidelity checks cannot see.

    Every finding here was a real defect in this dataset that the fidelity layer
    passed, because it only asks whether text appears somewhere in the cited page
    range - and leaked table rows, figure labels and section headings all do. The
    defect is that they are in the wrong field, which is a structural question.
    """
    step_rx = re.compile(r"^\s*(\d+)\s*\.")
    # Case-insensitive: a step legitimately *cites* "Table 4" without a colon, and
    # those citations must stay allowed, but a "Table 4:" header in any casing is
    # the start of a table that has leaked out of `reference_tables`.
    table_rx = re.compile(r"\bTable \d+\s*:", re.IGNORECASE)

    for rel, doc in records:
        base = os.path.basename(rel)
        if doc.get("document_type") != "BPT":
            continue
        steps = (doc.get("process_details") or {}).get("process_steps")
        if not isinstance(steps, list) or not steps:
            continue

        expect_first = STEP_START_EXCEPTIONS.get(doc.get("process_id"), 1)
        previous = None
        for i, entry in enumerate(steps):
            if not isinstance(entry, str):
                continue
            tag = f"process_steps[{i}]"
            flat = re.sub(r"\s+", " ", entry).strip()

            # Content that belongs to another field, not to a step.
            if table_rx.search(flat):
                rep.error(base, f"{tag}: reference-table content inside a step",
                          flat[:160])
            label = ITEM_LABEL_TAIL_RX.search(flat)
            if label:
                rep.error(base,
                          f"{tag}: ends with the source table's {label.group(1)!r} "
                          f"row label - extraction ran past the end of the step cell",
                          flat[:160])
            for frag in FLOWCHART_FRAGMENTS:
                if frag in flat:
                    rep.error(base, f"{tag}: figure label text inside a step "
                                    f"({frag!r})", flat[:160])
                    break

            m = step_rx.match(entry)
            if not m:
                # A scenario heading. Classification is by exclusion, so this is
                # the permissive branch of a function whose job is to catch text
                # in the wrong field - assert its shape rather than trusting it.
                rep.stats["scenario_headings"] += 1
                if len(flat) > MAX_HEADING_LENGTH:
                    rep.error(base,
                              f"{tag}: entry is not a numbered step and is too long "
                              f"to be a scenario heading ({len(flat)} chars) - has a "
                              f"heading swallowed step prose?", flat[:160])
                # The heading may also still be glued to the tail of the step
                # above it, which is how the extraction originally lost it: the
                # label was absorbed rather than dropped. Adding the heading
                # without removing the absorbed copy leaves the step body
                # disagreeing with the source and the label present twice.
                prior = steps[i - 1] if i else None
                if isinstance(prior, str):
                    # Compare with trailing punctuation and whitespace removed: an
                    # absorbed copy is not always a byte-identical suffix, and an
                    # exact endswith() lets "... Capitation Payment." through.
                    def tail_key(s):
                        return re.sub(r"[\s.;:,]+$", "", canon(s)).casefold()
                    prior_key, head_key = tail_key(prior), tail_key(flat)
                    if head_key and prior_key.endswith(head_key):
                        rep.error(base,
                                  f"{tag}: heading is also absorbed into the tail of "
                                  f"the preceding step", flat[:120])
                continue

            number = int(m.group(1))
            if number > MAX_PLAUSIBLE_STEP_NUMBER:
                rep.error(base,
                          f"{tag}: opens with {number}., which is not a step number "
                          f"(citation split at its period?)", flat[:160])
                continue

            if previous is None:
                if number != expect_first:
                    rep.error(base, f"{tag}: first step is {number}, expected "
                                    f"{expect_first}", flat[:120])
            elif number == previous + 1:
                pass                                    # normal progression
            elif number == 1:
                # A new scenario. The source labels each one; if the label is
                # missing the restart is unexplained to any consumer.
                prior = steps[i - 1] if i else None
                if not (isinstance(prior, str) and not step_rx.match(prior)):
                    rep.error(base,
                              f"{tag}: step numbering restarts at 1 without a "
                              f"preceding scenario heading", flat[:120])
            else:
                rep.error(base, f"{tag}: step {number} does not follow step "
                                f"{previous}", flat[:120])
            previous = number


def check_control_characters(records, rep: Report):
    """Private-use glyphs and control characters are always extraction debris."""
    for rel, doc in records:
        base = os.path.basename(rel)
        for path, text in iter_strings(doc):
            for ch in text:
                cp = ord(ch)
                if 0xE000 <= cp <= 0xF8FF:
                    rep.error(base, f"{path}: private-use glyph U+{cp:04X} (bullet debris)",
                              text[:120])
                    break
                if unicodedata.category(ch) in ("Cc", "Cf") and ch != "\n":
                    rep.error(base, f"{path}: control character U+{cp:04X}", text[:120])
                    break
        # Dangling second-level bullet markers, e.g. "Contract information o".
        # Checked on every content string, not just a few list fields: the
        # instance that was found happened to be in shared_data, but
        # process_steps carries far more list text.
        for path, text in iter_strings(doc):
            if path.startswith(".metadata"):
                continue
            for line in text.split("\n"):
                if re.search(r"\S\s+o$", line.rstrip()):
                    rep.error(base, f"{path}: dangling ' o' sub-bullet marker",
                              line.strip()[:120])


def check_category_coverage(records, rep: Report):
    """Flag a BCM missing a quality category its siblings all have.

    Nothing else detects *missing* content: every check verifies that what is
    present is attested, not that everything that should be present is. This is
    the gap that let a whole capability question and its five level descriptions
    go unnoticed in `CO_Perform_Contractor_Outreach_BCM`.

    The six "Business Capability Quality" categories are a fixed rubric applied to
    every process, so a record lacking one is either a genuine CMS omission or a
    dropped question. Either way it warrants a look, so this reports a warning
    rather than an error.
    """
    bcm = [(os.path.basename(r), d) for r, d in records if d.get("document_type") == "BCM"]
    if len(bcm) < 10:                      # not meaningful on an --area subset
        return
    seen = Counter()
    per_file = {}
    for base, doc in bcm:
        cats = {q.get("category") for q in
                doc.get("maturity_model", {}).get("capability_questions", [])}
        per_file[base] = cats
        seen.update(c for c in cats if c)

    # a category present in almost every record is part of the rubric
    rubric = {c for c, n in seen.items()
              if c.startswith("Business Capability Quality") and n >= 0.9 * len(bcm)}
    for base, cats in sorted(per_file.items()):
        for missing in sorted(rubric - cats):
            rep.warn(base, f"no question in the {missing!r} category",
                     "present in every other record - check the source for a dropped question")


def check_cross_process_bleed(records, rep: Report):
    """Detect a question swept in from the next process's table.

    The BCM appendices pack several processes into one PDF, and a process's
    final row often shares a page with the next process's first row. Where the
    page range overlaps, the trailing file can absorb the neighbour's opening
    question. Signature: two files from the same source PDF with overlapping
    page ranges, where the *last* question of one equals the *first* question of
    the other.
    """
    bcm = [(os.path.basename(r), d) for r, d in records if d.get("document_type") == "BCM"]

    def span(doc):
        rng = str(doc.get("metadata", {}).get("source_page_range", ""))
        start, _, end = rng.partition("-")
        if not start.isdigit():
            return None
        return int(start), int(end) if end.isdigit() else int(start)

    for base_a, doc_a in bcm:
        qs_a = doc_a.get("maturity_model", {}).get("capability_questions") or []
        span_a = span(doc_a)
        if len(qs_a) < 2 or not span_a:
            continue
        last = qs_a[-1]
        for base_b, doc_b in bcm:
            if base_b == base_a:
                continue
            if doc_b.get("metadata", {}).get("source_file") != doc_a.get("metadata", {}).get("source_file"):
                continue
            span_b = span(doc_b)
            qs_b = doc_b.get("maturity_model", {}).get("capability_questions") or []
            if not span_b or not qs_b:
                continue
            # b starts on or before a's last page -> the tables share a page
            if not (span_a[0] < span_b[0] <= span_a[1]):
                continue
            first = qs_b[0]
            if (canon(last.get("question", "")) == canon(first.get("question", ""))
                    and last.get("category") == first.get("category")):
                rep.error(base_a,
                          f"q{len(qs_a) - 1}: appears to be bleed-over from "
                          f"{base_b} q0 (page ranges overlap at p{span_b[0]})",
                          canon(last.get("question", ""))[:110])


def check_header_leakage(records, rep: Report):
    """PDF page furniture must never appear in transcribed content."""
    # Fields whose whole purpose is to record the edition are exempt: their
    # correct value ("3.0", "May 2014") is also what the page furniture says.
    exempt = {".version", ".version_date"}
    for rel, doc in records:
        base = os.path.basename(rel)
        for path, text in iter_strings(doc):
            if path.startswith(".metadata") or path in exempt:
                continue
            flat = canon(text)
            for artifact in HEADER_ARTIFACTS:
                if artifact in flat:
                    rep.error(base, f"{path}: page furniture {artifact!r} in content",
                              flat[:140])


# --------------------------------------------------------------------------
# fidelity checks (PyMuPDF)
# --------------------------------------------------------------------------

class SourceIndex:
    """Lazily extracted, normalised text for each source PDF."""

    def __init__(self, fitz_module):
        self._fitz = fitz_module
        self._pages = {}
        self._flat = {}
        self._lines = {}
        self._linebreak_pairs = {}
        self._inline_pairs = {}
        self._span_tokens = {}
        self._span_starts = {}

    def pages(self, rel_src):
        if rel_src not in self._pages:
            doc = self._fitz.open(os.path.join(REPO_ROOT, rel_src))
            self._pages[rel_src] = [doc[i].get_text() for i in range(doc.page_count)]
            doc.close()
        return self._pages[rel_src]

    def lines(self, rel_src):
        """Every non-empty source line, in document order."""
        if rel_src not in self._lines:
            out = []
            for page in self.pages(rel_src):
                out.extend(ln.strip() for ln in page.splitlines() if ln.strip())
            self._lines[rel_src] = out
        return self._lines[rel_src]

    def flat(self, rel_src):
        """Whole document, canonicalised, for substring containment tests."""
        if rel_src not in self._flat:
            self._flat[rel_src] = canon("\n".join(self.pages(rel_src)))
        return self._flat[rel_src]

    def span(self, rel_src, page_range, pad=1):
        pages = self.pages(rel_src)
        start, _, end = str(page_range).partition("-")
        start = int(start)
        end = int(end) if end else start
        lo = max(0, start - 1 - pad)
        hi = min(len(pages), end + pad)
        return canon("\n".join(pages[lo:hi]))

    def span_page_starts(self, rel_src, page_range, pad=1):
        """Character offsets in `span` where each page begins.

        Used to require that a two-fragment reassembly actually straddles a page
        break. Every genuine wrapped cell in this corpus does; a fragmentation
        caused by a dropped word generally does not, which is what separates the
        expected warnings from that defect class.
        """
        key = (rel_src, str(page_range), pad, "starts")
        if key not in self._span_starts:
            pages = self.pages(rel_src)
            start, _, end = str(page_range).partition("-")
            start = int(start)
            end = int(end) if end else start
            lo = max(0, start - 1 - pad)
            hi = min(len(pages), end + pad)
            offsets, acc = [], ""
            for page in pages[lo:hi]:
                offsets.append(len(canon(acc)))
                acc += page + "\n"
            self._span_starts[key] = offsets
        return self._span_starts[key]

    def span_tokens(self, rel_src, page_range):
        """Multiset of words appearing on the record's own pages."""
        key = (rel_src, str(page_range), "tokens")
        if key not in self._span_tokens:
            self._span_tokens[key] = Counter(tokenise(self.span(rel_src, page_range)))
        return self._span_tokens[key]

    def linebreak_pairs(self, rel_src):
        """Lower-cased word pairs the PDF hyphenated across a line break.

        A JSON string containing "left- right" is an extraction artifact only if
        the source actually broke the line there. Suspended hyphens authored on
        one line (e.g. "pre- and post-approved") must be preserved, and are
        recognised by `inline_hyphen_pairs` instead.

        Pairs are collected across page boundaries as well as line boundaries,
        since a cell can wrap at the foot of a page, and are lower-cased so that
        a mid-sentence occurrence still matches a capitalised line-initial one.
        """
        if rel_src not in self._linebreak_pairs:
            pairs = set()
            lines = self.lines(rel_src)          # already page-spanning
            for a, b in zip(lines, lines[1:]):
                # CMS uses U+002D, U+2010, U+2013 and U+2014 interchangeably at
                # line ends; all four mean the same thing here.
                m = re.search(r"([A-Za-z][\w']*)[-\u2010\u2011\u2013\u2014]$", a)
                n = re.match(r"([A-Za-z][\w']*)", b)
                if m and n:
                    pairs.add((m.group(1).lower(), n.group(1).lower()))
            self._linebreak_pairs[rel_src] = pairs
        return self._linebreak_pairs[rel_src]

    def inline_hyphen_pairs(self, rel_src):
        """Lower-cased word pairs written as "left- right" within one source line.

        These are authored suspended hyphens, not extraction artifacts, and must
        survive untouched. Deciding this per occurrence from the source beats
        maintaining a global allowlist, which would silence a genuine line break
        involving the same words in a different document.
        """
        if rel_src not in self._inline_pairs:
            pairs = set()
            rx = re.compile(r"([A-Za-z][\w']*)[-\u2010\u2011\u2013\u2014]\s+([A-Za-z][\w']*)")
            for line in self.lines(rel_src):
                for m in rx.finditer(line):
                    pairs.add((m.group(1).lower(), m.group(2).lower()))
            self._inline_pairs[rel_src] = pairs
        return self._inline_pairs[rel_src]

    def page_count(self, rel_src):
        return len(self.pages(rel_src))


def check_fidelity(records, index: SourceIndex, rep: Report):
    hyphen_rx = re.compile(r"([A-Za-z][\w']*)-\s+([A-Za-z][\w']*)")

    for rel, doc in records:
        base = os.path.basename(rel)
        src = doc.get("metadata", {}).get("source_file")
        page_range = doc.get("metadata", {}).get("source_page_range")
        if not src or not page_range:
            continue
        if not os.path.exists(os.path.join(REPO_ROOT, src)):
            continue

        # --- page range sanity + provenance
        start, _, end = str(page_range).partition("-")
        end_page = int(end) if end else int(start)
        if end_page > index.page_count(src):
            rep.error(base, f"page range {page_range} exceeds {index.page_count(src)}-page source")
            continue
        span = index.span(src, page_range)
        # Where the two CMS appendices name a process differently, process_name
        # follows the framework's Business Architecture index so that a BCM pairs
        # with its BPT, and metadata.source_process_name records what this
        # record's own document publishes. Verify provenance against the latter.
        published = doc["metadata"].get("source_process_name") or doc.get("process_name", "")
        if canon(published) not in span:
            rep.error(base,
                      f"source_process_name {published!r} not found within source "
                      f"pages {page_range}")

        flat = index.flat(src)
        pairs = index.linebreak_pairs(src)
        inline = index.inline_hyphen_pairs(src)
        process_name = canon(doc.get("process_name", ""))
        published_name = canon(published)

        for path, text in iter_strings(doc):
            if path.startswith(".metadata") or path.endswith(".filename"):
                continue
            # A diagram description is the figure's published title, and a figure
            # about this process legitimately names it: "High Level Mapping to
            # Determine Member Eligibility". The splice check below would reject that,
            # and correctly by its own rule - CMS sets that particular title inside the
            # figure raster, so it is not in the page's text layer for any window to
            # match. The eight other titles are verbatim text-layer strings; this one
            # is transcribed from the rendered figure, which the render script records.
            is_diagram_description = re.search(r"\.diagrams\[\d+\]\.description$", path)

            # --- hyphen line-break artifacts
            #
            # Decided per occurrence from the source layout rather than from a
            # hand-maintained allowlist: if the source broke the line after the
            # hyphen the space is an artifact; if the same pair occurs spaced
            # within a single source line it is authored ("pre- and post-...").
            for m in hyphen_rx.finditer(text):
                pair = (m.group(1).lower(), m.group(2).lower())
                if pair in pairs:
                    rep.error(base,
                              f"{path}: hyphen line-break artifact "
                              f"{m.group(1)}- {m.group(2)!r}",
                              squash(text)[:140])
                elif pair in inline:
                    continue          # authored suspended hyphen, preserve as published
                else:
                    rep.warn(base,
                             f"{path}: unclassified hyphen split "
                             f"{m.group(1)!r}- {m.group(2)!r}",
                             squash(text)[:140])

            # --- page-header contamination: the process name spliced into content
            #
            # Word boundaries matter: "Manage Contract" must not match inside
            # "Manage Contractor Information", and "Authorize Treatment Plan"
            # must not match inside "Authorize Treatment Plans". The comparison
            # window is sliced from the text verbatim rather than rebuilt from
            # tokens, so punctuation stays attached ("Referral?" not "Referral ?").
            #
            # Windows are built per paragraph, never across a newline. A
            # paragraph break in the JSON is where the source had a page break,
            # and the raw PDF text stream has running headers sitting in that
            # gap - so a cross-paragraph window would never match even when the
            # transcription is correct.
            names = set() if is_diagram_description else {
                n for n in (process_name, published_name) if n and len(n) > 6}
            for pname in names:
                name_rx = re.compile(rf"\b{re.escape(pname)}\b")
                for segment in text.split("\n"):
                    seg = canon(segment)
                    for m in name_rx.finditer(seg):
                        lo = window_start(seg, m.start(), words=3)
                        hi = window_end(seg, m.end(), words=3)
                        if lo == m.start() and hi == m.end():
                            continue      # nothing around it to judge by
                        window = seg[lo:hi]
                        if window not in flat:
                            rep.error(base,
                                      f"{path}: process name spliced into content (page header)",
                                      "..." + window + "...")

        # --- transcribed text must trace back to the record's OWN pages
        #
        # Scoping to the page span, not the whole document, is essential. The
        # appendices pack up to 19 processes into one PDF, so a phrase lifted
        # from a neighbouring process traces cleanly against the full text and
        # the defect is invisible. That is the same structural fact behind the
        # cross-process bleed defect.
        # Two complementary checks, because they prove different things.
        #
        # Token attestation runs on every content string. Every word must occur
        # in the record's own pages. It is immune to the column interleaving that
        # defeats substring matching, so it works on the long, heavily wrapped
        # maturity-level cells, and it is what catches a word truncated at a page
        # break ("calend" where the source says "calendar"). It does not prove
        # word order.
        #
        # Sequence tracing runs on questions and notes, which are short enough to
        # appear contiguously. It does prove order and exact wording, which is
        # what catches a word inserted into an otherwise-real question.
        span_tokens = index.span_tokens(src, page_range)
        page_starts = index.span_page_starts(src, page_range)
        for field_path, text in traceable_text(doc):
            body = canon(text)
            if not body:
                continue

            unattested = Counter(tokenise(body)) - span_tokens
            if unattested:
                rep.error(base,
                          f"{field_path}: {len(unattested)} token(s) not present in "
                          f"source pages {page_range} - text truncated or fabricated",
                          ", ".join(f"{t!r}" for t in sorted(unattested))[:160])
                continue

            tail = dangling_tail(text)
            if tail:
                rep.error(base,
                          f"{field_path}: ends on {tail!r} with no terminal "
                          "punctuation - text likely lost at a page break",
                          squash(text)[-120:])
                continue

            if field_path.endswith((".question", ".note")):
                if len(body) < MIN_TRACE_LENGTH or body in span:
                    continue
                pieces = source_fragments(body, span, page_starts)
                if pieces is not None:
                    rep.stats["reassembled"] += 1
                    rep.warn(base,
                             f"{field_path}: reassembled from {len(pieces)} source "
                             "fragments (wrapped table cell)",
                             " + ".join(repr(p[:60]) for p in pieces))
                    continue
                rep.error(base,
                          f"{field_path}: word sequence not found in source pages "
                          f"{page_range}",
                          body[:170])


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Verify the MITA JSON dataset against its source CMS PDFs.")
    parser.add_argument("--structural-only", action="store_true",
                        help="skip PDF comparison (no PyMuPDF required)")
    parser.add_argument("--area", help="limit to one business-area directory")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="list every finding instead of a grouped summary")
    parser.add_argument("--max-detail", type=int, default=25,
                        help="max findings shown per message group (default 25)")
    args = parser.parse_args()

    print("=" * 78)
    print("MITA DATASET VERIFICATION")
    print("=" * 78)

    records, broken = load_dataset(args.area)
    rep = Report()

    for rel, message in broken:
        rep.error(os.path.basename(rel), message)

    if not records:
        print("\nNo JSON files found under data/. Nothing was verified.")
        print("Refusing to report success on an empty file set.")
        return 2

    print(f"Loaded {len(records)} files"
          + (f" (area filter: {args.area})" if args.area else ""))

    if args.area is None:
        if len(records) != EXPECTED_TOTAL:
            rep.error("<dataset>", f"expected {EXPECTED_TOTAL} files, found {len(records)}")

    check_structure(records, rep, args.area)
    check_step_structure(records, rep)
    check_orphan_images(records, rep)
    check_control_characters(records, rep)
    check_header_leakage(records, rep)
    check_cross_process_bleed(records, rep)
    check_category_coverage(records, rep)

    if args.area is None:
        for doc_type, count in (("BCM", rep.stats["files_BCM"]), ("BPT", rep.stats["files_BPT"])):
            if count != EXPECTED_PER_TYPE:
                rep.error("<dataset>", f"expected {EXPECTED_PER_TYPE} {doc_type} files, found {count}")
        if rep.stats["scenario_headings"] != EXPECTED_SCENARIO_HEADINGS:
            rep.error("<dataset>",
                      f"expected {EXPECTED_SCENARIO_HEADINGS} scenario headings, found "
                      f"{rep.stats['scenario_headings']} - debris misclassified as a "
                      f"heading, or a heading lost")

    if args.structural_only:
        print("Fidelity checks skipped (--structural-only)")
    else:
        try:
            import fitz  # PyMuPDF
        except ImportError:
            print("\nPyMuPDF is required for fidelity checks.")
            print("  pip install -r tools/requirements.txt")
            print("Or re-run with --structural-only.")
            return 2
        print("Comparing against source PDFs...")
        index = SourceIndex(fitz)
        check_fidelity(records, index, rep)
        check_reference_table_pairing(records, index, rep)
        check_diagram_images(records, fitz, rep)

    # ---- report
    def dump(title, findings):
        print("\n" + "=" * 78)
        print(f"{title}: {len(findings)}")
        print("=" * 78)
        if not findings:
            return
        grouped = defaultdict(list)
        for filename, message, detail in findings:
            key = re.sub(r"\bq\d+\b", "q*", message)
            key = re.sub(r"\[\d+\]", "[*]", key)
            grouped[key].append((filename, message, detail))
        for key in sorted(grouped, key=lambda k: -len(grouped[k])):
            items = grouped[key]
            print(f"\n  {len(items):4d}x  {key}")
            limit = len(items) if args.verbose else min(args.max_detail, len(items))
            for filename, message, detail in items[:limit]:
                print(f"          {filename}: {message}")
                if detail:
                    print(f"                {detail}")
            if limit < len(items):
                print(f"          ... {len(items) - limit} more (use --verbose)")

    dump("ERRORS", rep.errors)
    dump("WARNINGS", rep.warnings)

    print("\n" + "=" * 78)
    print("CONTENT STATISTICS")
    print("=" * 78)
    print(f"  BCM files ................ {rep.stats['files_BCM']}")
    print(f"  BPT files ................ {rep.stats['files_BPT']}")
    print(f"  BCM capability questions . {rep.stats['bcm_questions']}")
    print(f"  BCM level descriptions ... {rep.stats['bcm_levels']}")

    print(f"  BPT diagram references ... {rep.stats['diagrams']}")
    print(f"  BPT step entries ......... {rep.stats['bpt_steps']} "
          f"({rep.stats['bpt_steps'] - rep.stats['scenario_headings']} numbered steps "
          f"+ {rep.stats['scenario_headings']} scenario headings)")
    if rep.stats["reference_tables"]:
        print(f"  BPT reference tables ..... {rep.stats['reference_tables']} "
              f"({rep.stats['reference_table_rows']} rows)")
    if rep.stats["process_id_differs_from_name"]:
        print(f"  process_id differing from process_name ... "
              f"{rep.stats['process_id_differs_from_name']} "
              "(expected: CMS spells two processes differently across BPT/BCM)")

    print("\n" + "=" * 78)
    if rep.errors:
        print(f"FAILED - {len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
        return 1
    print(f"PASSED - 0 errors, {len(rep.warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
