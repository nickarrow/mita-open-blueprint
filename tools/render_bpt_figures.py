"""Render the nine real figures from the EE Determine Member Eligibility BPT pages.

The source composes each figure from many small raster fragments plus a text layer of
small-font labels. Extracting the fragments individually is what produced the 76
meaningless PNGs this replaces; the figure only exists as a region of the page, so a
clipped page render is the only faithful representation.

Region = union of the page's embedded-image and small-font-label bounding boxes,
excluding page furniture. That union is then clamped vertically by the body text
immediately above and below it, so the crop cannot swallow a step's prose - but the
clamp is never allowed to cut into the figure itself.

Nine figures, on pages 2, 4, 5, 6, 7, 9, 10, 13 and 14. Eight carry their title in the
page's text layer and it is transcribed from there. Page 2's title, "High Level Mapping
to Determine Member Eligibility", is set inside the figure raster and appears nowhere in
the text layer, so it is transcribed from the rendered image instead.

    .venv/bin/python tools/render_bpt_figures.py <output-dir>

Re-running reproduces the committed images. Written for one record because it is the
only one of 152 whose source pages contain a figure.
"""
import json
import os
import sys

import fitz

PDF = ("source-pdfs/may-2014-update/bpt/Eligibility and Enrollment Management/"
       "Eligibility and Enrollment Management BPT.pdf")
FOOTER_Y = 700.0        # CMS logo and page footer sit below this on every page
FURNITURE_SIZES = {8.0, 9.0, 11.0, 12.0}   # footer, reference tables, running headers
BODY_SIZE = 10.0
PAD = 3.0
SCALE = 2.0


def page_parts(page):
    """Embedded-image boxes, small-font label boxes, and body-text boxes."""
    data = page.get_text("dict")
    images = [b["bbox"] for b in data["blocks"]
              if b["type"] == 1 and b["bbox"][1] < FOOTER_Y]
    labels, body = [], []
    for block in data["blocks"]:
        if block["type"] != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if not span["text"].strip():
                    continue
                size, bbox = round(span["size"], 1), span["bbox"]
                if bbox[1] >= FOOTER_Y or size in FURNITURE_SIZES:
                    continue
                (labels if size < BODY_SIZE else body).append(bbox)
    return images, labels, body


def union(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def figure_clip(page):
    """The figure's clip rectangle, or None if the page carries no figure."""
    images, labels, body = page_parts(page)
    if not images and not labels:
        return None
    fx0, fy0, fx1, fy1 = union(images + labels)
    # Only body text that horizontally overlaps the figure can bound it vertically.
    # This keeps the Item-column labels ("Business Process Steps") out of the clamp,
    # since they sit to the left of the Details column the figure lives in.
    overlapping = [b for b in body if b[2] > fx0 and b[0] < fx1]
    above = [b[3] for b in overlapping if b[3] <= fy0 + 6]
    below = [b[1] for b in overlapping if b[1] >= fy1 - 6]
    # min() against the figure top: on page 2 the nearest text above ends 2pt from the
    # figure, so padding down from it clipped the title's ascenders.
    top = min(fy0, max(above) + 1.0) if above else fy0 - PAD
    bottom = min(below) - PAD if below else fy1 + PAD
    if bottom <= top:
        top, bottom = fy0 - PAD, fy1 + PAD
    return fitz.Rect(max(0, fx0 - PAD), max(0, top),
                     min(page.rect.width, fx1 + PAD),
                     min(page.rect.height, bottom))


def main(outdir, page_limit=16):
    doc = fitz.open(PDF)
    os.makedirs(outdir, exist_ok=True)
    manifest = {}
    for index in range(min(page_limit, doc.page_count)):
        page = doc[index]
        clip = figure_clip(page)
        if clip is None:
            continue
        pixmap = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=clip)
        path = os.path.join(outdir, f"p{index + 1:02d}.png")
        pixmap.save(path)
        manifest[index + 1] = {
            "clip": [round(v, 1) for v in (clip.x0, clip.y0, clip.x1, clip.y1)],
            "px": [pixmap.width, pixmap.height],
            "bytes": os.path.getsize(path),
        }
        print(f"  p{index + 1:>2}: {pixmap.width}x{pixmap.height}px "
              f"{os.path.getsize(path):>7,}B  clip y {clip.y0:.0f}-{clip.y1:.0f}")
    json.dump(manifest, open(os.path.join(outdir, "manifest.json"), "w"), indent=1)
    return manifest


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/figs3")
