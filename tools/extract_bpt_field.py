#!/usr/bin/env python3
"""
Extract a single BPT row from a source PDF, preserving its list hierarchy.

Appendix C renders each business process as a two-column table whose left column
holds row labels (Description, Trigger Event, Shared Data, Predecessor, ...) and
whose right column holds the content. Nested lists in that content use two
different bullet glyphs, and long entries wrap onto continuation lines. Plain
text extraction loses all of that, which is how bullet markers ended up welded
onto the wrong array elements in the JSON.

Three signals recover the structure:

  font    SymbolMT U+F0B7 marks a first-level bullet; Courier New "o" marks a
          second-level bullet.
  x0      confirms the indent depth of the text that follows a marker.
  y-gap   distinguishes a wrapped continuation line (~11.5pt below its
          predecessor) from the start of a new item (~17.5pt or more). This is
          the decisive signal: line width alone cannot tell them apart, because
          a line can end short simply because the next word did not fit.

Usage:
    .venv/bin/python tools/extract_bpt_field.py <json-file> --row "Shared Data"
    .venv/bin/python tools/extract_bpt_field.py <json-file> --row Failures --json

The JSON file supplies the source PDF path and page range from its metadata, so
the extraction is always scoped to the right process.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROW_LABELS = (
    "Description", "Trigger Event", "Result", "Business Process Steps",
    "Shared Data", "Predecessor", "Successor", "Constraints", "Failures",
    "Performance Measures",
)
ROW_RE = re.compile(r"^(" + "|".join(l.replace(" ", r"\s*") for l in ROW_LABELS) + r")\s*$")
FURNITURE_RE = re.compile(
    r"^(Part\s|Appendix|Model\s*Details|Matrix\s*Details|May 2014|Version 3\.0"
    r"|Item$|Details$|Part I, Appendix)")

BULLET_1 = "\uf0b7"
CONTINUATION_GAP = 14.0     # points; below this a line continues its predecessor
INDENT_L1 = "  "
INDENT_L2 = "    "


def _lines(doc, first_page, last_page, row_label, process_name):
    """Yield (page_index, y0, x0, font, text) for the requested row only."""
    want = re.compile("^" + row_label.replace(" ", r"\s*") + r"\s*$")
    active = False
    label_buffer: list[str] = []
    for page_index in range(first_page - 1, min(last_page, doc.page_count)):
        for block in doc[page_index].get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = line["spans"]
                text = "".join(s["text"] for s in spans).replace("\xa0", " ").strip()
                if not text:
                    continue
                font = spans[0]["font"]
                if font.startswith("Calibri"):        # page furniture is set in Calibri
                    continue
                x0 = round(spans[0]["bbox"][0], 1)

                # Row labels sit in the left column and may wrap across lines,
                # e.g. "Business" / "Process Steps". Accumulate and test the
                # joined form, longest first.
                if x0 < 150:
                    if FURNITURE_RE.match(text) or text == process_name:
                        continue
                    label_buffer.append(text)
                    del label_buffer[:-3]
                    for size in (3, 2, 1):
                        if len(label_buffer) < size:
                            continue
                        joined = " ".join(label_buffer[-size:])
                        if ROW_RE.match(joined):
                            active = bool(want.match(joined))
                            label_buffer.clear()
                            break
                    continue

                label_buffer.clear()
                if not active:
                    continue
                if FURNITURE_RE.match(text) or text == process_name:
                    continue
                yield page_index, round(spans[0]["bbox"][1], 1), x0, font, text


def extract_items(doc, first_page, last_page, row_label, process_name):
    """Return a list of (level, text) with level 0 = top, 1 and 2 = nested."""
    items: list[list] = []
    pending_level = None
    prev_y = None
    prev_page = None

    for page_index, y0, _x0, font, text in _lines(
            doc, first_page, last_page, row_label, process_name):

        if font.startswith("SymbolMT") and text == BULLET_1:
            pending_level, prev_y, prev_page = 1, y0, page_index
            continue
        if font.startswith("CourierNew") and text == "o":
            pending_level, prev_y, prev_page = 2, y0, page_index
            continue

        new_page = prev_page is not None and page_index != prev_page
        gap = float("inf") if (prev_y is None or new_page) else y0 - prev_y

        if pending_level is not None:
            items.append([pending_level, text])
            pending_level = None
        elif gap <= CONTINUATION_GAP and items:
            items[-1][1] += " " + text
        else:
            items.append([0, text])

        prev_y, prev_page = y0, page_index

    return [(level, re.sub(r"\s+", " ", text).strip()) for level, text in items]


def to_array(items):
    """Collapse (level, text) pairs into the repository's array convention.

    One array element per top-level item. Nested items are appended to their
    parent as indented lines, matching how process_steps already represents
    sub-steps ("parent\\n  a. child").
    """
    out: list[str] = []
    for level, text in items:
        if level == 0 or not out:
            out.append(text)
        else:
            indent = INDENT_L1 if level == 1 else INDENT_L2
            out[-1] += f"\n{indent}- {text}"
    return out


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("json_file", help="BPT JSON file (supplies source PDF + page range)")
    parser.add_argument("--row", default="Shared Data",
                        help="row label to extract (default: Shared Data)")
    parser.add_argument("--json", action="store_true",
                        help="emit the array as JSON instead of an outline")
    args = parser.parse_args()

    import fitz

    path = args.json_file if os.path.isabs(args.json_file) else os.path.join(REPO_ROOT, args.json_file)
    with open(path, encoding="utf-8") as fh:
        doc_json = json.load(fh)

    meta = doc_json["metadata"]
    start, _, end = str(meta["source_page_range"]).partition("-")
    first, last = int(start), int(end) if end else int(start)

    pdf = fitz.open(os.path.join(REPO_ROOT, meta["source_file"]))
    items = extract_items(pdf, first, last, args.row, doc_json["process_name"])
    pdf.close()

    if not items:
        print(f"no content found for row {args.row!r} in pages {first}-{last}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(to_array(items), indent=2, ensure_ascii=False))
    else:
        print(f"{doc_json['process_name']} - {args.row} "
              f"(source pp {meta['source_page_range']})\n")
        for level, text in items:
            print(f"{'  ' * level}{'-' if level else '*'} {text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
