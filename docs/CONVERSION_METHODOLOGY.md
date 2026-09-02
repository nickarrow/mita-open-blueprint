# Conversion Methodology

How the CMS MITA PDFs became the JSON in `data/`, and how the result is checked.

## Source documents

The dataset derives from two appendices of the MITA Framework 3.0, May 2014
Update, held in `source-pdfs/may-2014-update/`:

| Appendix | Content | Becomes |
|---|---|---|
| Part I Appendix C — Business Process Model Details | Per-process tables: description, trigger events, results, steps, shared data, predecessors, successors, constraints, failures, performance measures | 76 BPT records |
| Part I Appendix D — Business Capability Matrix Details | Per-process six-column maturity matrices: capability question plus Level 1–5 descriptions | 76 BCM records |

Each appendix is split by business area, so one PDF holds several processes. That
detail matters: process boundaries fall mid-page, which is the root cause of most
extraction defects described below.

## Layout, and why it is hard

Both appendices are tables, and `page.get_text()` returns words in stream order,
not reading order. Three consequences shape everything else:

**Columns interleave.** In Appendix D a Level 2 cell that wraps onto a second
line has the neighbouring columns' text between its two halves in the stream. A
correctly transcribed cell therefore does not appear as a contiguous substring of
the extracted text.

**Running headers land inside cells.** Every page repeats the process name in its
header. Where a page break falls inside a table cell, that header text lands
between the cell's two halves.

**Bullet hierarchy is font-encoded.** First-level bullets are `U+F0B7` in
SymbolMT; second-level are the letter `o` in Courier New. Both are separate text
runs from the content they introduce, and neither survives plain text extraction
as structure.

## Extraction

BPT records were extracted programmatically, then reviewed against the source.
BCM records were extracted programmatically and then **manually corrected**
against the source, because the maturity matrices defeated automated column
parsing; the original BCM extraction script is disabled in
`tools/archived-old-tools/` for that reason.

Where structure had to be represented inside a string, the convention is a
newline plus indent:

```
"3. Determine if CMS requires an APD.\n  a. Produce APD.\n  b. Modify APD as directed."
"Other Agency Information:\n  - Department of Motor Vehicles (DMV)\n  - Veterans Administration (VA)"
```

Two spaces for the first nesting level, four for the second.

## Transcription decisions

These are the judgement calls a reader should know about.

**The source is authoritative, including its inconsistencies.** Where CMS is
internally inconsistent, the JSON reproduces what each document says. CMS names
two processes differently between Appendix C and Appendix D, and both spellings
are preserved in `process_name`; `process_id` exists to make the pair joinable.
`predecessor_processes` and `successor_processes` reproduce whatever the source
put in those cells, including prose `NOTE:` blocks and the literal string
`None`. Two capability questions end in a full stop rather than a question mark,
as published.

**Dashes are normalised, quotes are not.** The PDFs mix `U+002D`, `U+2010`
hyphen, `U+2013` en dash and `U+2014` em dash; all become `U+002D` in the JSON so
that consumers can match on a single character. Curly apostrophes and quotation
marks (`U+2018`–`U+201D`) are preserved as published. The asymmetry is
deliberate but worth knowing.

**Hyphenation across line breaks is rejoined.** The source hyphenates at line
ends, so `state-` / `specific` becomes `state-specific`. Suspended hyphens
authored on a single line, such as `pre- and post-approved`, are preserved. The
two cases are distinguished by layout, not by text: whether the hyphen actually
ends a line in the PDF.

**Page furniture is excluded.** Running headers, footers, page numbers, and the
`Item` / `Details` / `Capability Question` / `Level N` table headings are not
content and do not appear in the JSON.

## Known defect classes

Every one of these was found in the dataset and repaired. They are documented
because they are what to look for when adding a new version, and because
`tools/verify_against_source.py` now detects each one.

| Defect | Cause |
|---|---|
| Page-header contamination | Page break inside a table cell; the running header's process name spliced into the text. |
| Merged questions | Page break between two capability questions; both collapsed into one record with their level text concatenated pairwise. |
| Dropped question | A question and all five of its levels sat alone on a page and were skipped entirely. |
| Cross-process bleed-over | A process's last row shares a page with the next process's first row; the trailing record absorbed the neighbour's opening question. |
| Bullet-marker leakage | Markers treated as trailing content rather than delimiters, shifting every marker onto the preceding item and destroying the parent/child relationship. |
| Line-wrap splitting | A wrapped continuation line treated as a new list item. |
| Lost words and sub-items | Content on the far side of a page break dropped, leaving a dangling hyphen or an orphaned branch. |
| Welded blocks | An `Alternate Path:` block concatenated onto the preceding numbered step. |

The pattern is consistent: **page breaks are where this dataset goes wrong.** Any
future extraction should treat every page boundary as a place to verify rather
than assume.

## Verification

`tools/verify_against_source.py` compares the JSON against the PDFs. See
[../tools/README.md](../tools/README.md) for what it checks and how to run it.

Its central design problem is telling "I cannot verify this" apart from "this is
wrong", given that a wrapped cell never matches contiguously. It uses two
complementary checks, because they prove different things.

**Token attestation**, on every content field: every word must occur on the pages
that record cites. Immune to the column interleaving that defeats substring
matching, so it works on the long, heavily wrapped level cells. It catches a word
truncated at a page break and text borrowed from a neighbouring process. It does
not prove word order.

**Sequence tracing**, on questions and notes: the exact wording must appear on
the record's own pages, allowing at most a two-fragment split for a cell that
wraps across a page break. This catches a word inserted into an otherwise-real
question.

Scoping to the cited pages rather than the whole PDF is essential — the
appendices pack up to 19 processes into one file, so a phrase lifted from a
neighbour traces cleanly against the full text and the defect stays invisible.

A third signal, **dangling tails**, flags a field ending on a function word with
no terminal punctuation. That is the signature of text lost at a page break where
the break fell on a word boundary, so every word present is still attested.

The checks were validated by a negative control: ten defect classes were injected
into a copy of the data and nine were detected, including a fabricated question,
a fabricated level description, a question lifted from a sibling process, a
truncated word, a duplicate `process_id`, and a page footer spliced into content.
The tenth — swapping two level descriptions between maturity ratings — was not
detected, and is documented as a known limitation in
[../tools/README.md](../tools/README.md).

## Adding a new MITA version

1. Add the source PDFs under `source-pdfs/<version>/`.
2. Archive the current dataset, following the pattern of `data-archived-2012/`.
3. Extract, then verify against the source. Expect page-break defects and look
   for them specifically.
4. Confirm every record's `source_page_range` actually contains its process, and
   that `process_id` pairs each BCM with exactly one BPT.
5. Update `docs/DATA_STRUCTURE.md` if the schema changes, and the statistics in
   `README.md` either way.

## Reproducibility

The source PDFs are in the repository, the page range for every record is in its
metadata, and the verification tooling is included. Any claim in the dataset can
be traced to a specific page of a specific CMS document and checked.

Per-area raw PDF text dumps from the 2014 migration are retained in
`tools/archived-old-tools/` as the evidence trail behind the transcription.
