# Tools

Utilities for validating and inspecting the dataset in `data/`.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r tools/requirements.txt
```

Only `verify_against_source.py`'s fidelity checks and `extract_bpt_field.py`
need the dependency (PyMuPDF, for PDF text extraction with layout). Structural
validation runs on the standard library alone.

---

## verify_against_source.py

The quality gate. Run it before opening a pull request.

```bash
.venv/bin/python tools/verify_against_source.py              # everything
.venv/bin/python tools/verify_against_source.py --structural-only
.venv/bin/python tools/verify_against_source.py --area care_management
.venv/bin/python tools/verify_against_source.py --verbose     # every finding
```

Two layers:

**Structural** (no dependencies) — schema shape, required fields, filename
agreement with `process_code` / `document_type` / `process_name` / directory,
`process_id` present and correctly prefixed, BCM↔BPT pairing on `process_id`,
metadata completeness, source-PDF paths resolving, diagram references existing
on disk, and degenerate or duplicate content.

**Fidelity** (needs PyMuPDF) — compares transcribed text against the source PDFs
and detects the extraction artifacts this dataset has actually suffered from:

| Check | What it catches |
|---|---|
| page-range provenance | `process_name` absent from the pages the record claims |
| page-header contamination | the running header's process name spliced into cell text |
| hyphen line-break artifacts | `state- specific` where the source hyphenated across a line |
| bullet-marker leakage | `U+F0B7` glyphs and dangling `o` sub-bullet markers |
| merged questions | a question whose text continues past its own `?` |
| cross-process bleed-over | a question absorbed from the next process's table |
| token attestation | a word not present on the pages the record cites - a truncation or a fabrication |
| dangling tail | a field ending on a function word with no terminal punctuation - text lost at a page break |
| question and note sequence | wording or word order that does not appear on the record's own pages |
| process_id uniqueness | a duplicate id, which would silently merge two processes for any consumer indexing by it |
| implausible step number | an entry opening `435.` — a CFR citation split at its period and read as a step |
| step sequence | a step number that neither continues the sequence nor restarts at 1 |
| unlabelled scenario restart | numbering that restarts at 1 with no scenario heading to explain it |
| absorbed scenario heading | a heading present as its own entry *and* still glued to the tail of the step above it |
| scenario heading count | debris misclassified as a heading, or a heading lost by a re-extraction |
| table text in a step | `Table N:` content, any casing, or figure-legend labels sitting in `process_steps` |
| row label in a step tail | a step ending on the source table's own `Shared Data` or `Performance Measures` label, meaning extraction ran past the end of the step cell |
| reference table shape | missing or empty cells, `table_number` not 1..N, `page_reference` outside the record's pages |
| unresolvable table citation | a step citing `Table N` with no such table present — checked even when the record has no `reference_tables` at all |
| reference table pairing | an `authority` attached to the wrong `eligibility_group`, which token attestation cannot see because both strings still occur in the source |

### Exit codes

| Code | Meaning |
|---|---|
| 0 | no errors (warnings may be present) |
| 1 | one or more errors |
| 2 | could not run meaningfully — no files found, or PyMuPDF missing |

Exit code 2 matters. An earlier validator in this repository walked a directory
that did not exist, validated zero files, and printed `VALIDATION PASSED`. This
tool refuses to report success on an empty file set.

### Errors vs warnings

An **error** is something to fix. A **warning** is something to be aware of.

The expected warnings are reassembly notices. Appendix D lays each capability
question out in a six-column table, and a cell that wraps onto another line — or
across a page break — is split in the raw PDF text stream by the neighbouring
columns and the running header. Correctly transcribed text therefore does not
appear verbatim in the extracted stream even though every piece of it does, in
order. The tool reports these as warnings, naming the fragments, and reserves
errors for text that cannot be traced to the record's own pages at all.

57 such warnings are expected on a clean run.

### What the checks do and do not establish

Be precise about this when relying on the tool.

**Established for every transcribed field**: every word occurs on the pages that
record cites. This catches truncation at a page break, which is the defect class
this dataset actually suffered from. `traceable_text()` names the few excluded
fields — metadata, fixed enumerations, and the `diagrams` entries, whose
filenames and descriptions are generated by the tooling rather than transcribed.

**Established for questions and notes only**: exact wording and word order. These
are short enough to verify as sequences, and the two-fragment fallback requires
the split to straddle a page boundary.

**Not established — placement.** Word-level attestation says nothing about where
content sits. All of these pass: two maturity levels swapped between ratings, all
five levels rotated, a reversed `process_steps` array, `results` exchanged with
`failures`, `predecessor_processes` exchanged with `successor_processes`,
`description` exchanged with `constraints`, and reordered questions. Detecting
these needs geometric table reconstruction; two attempts proved unreliable enough
that shipping them would have given false confidence.

The structural step checks narrow this for `process_steps` but do not close it.
Established by injecting nine variants one at a time, of which eight are caught:

- bare table rows added as their own entries — caught, by the scenario-heading count
- table debris appended into a step body — caught when the splice introduces a token
  that is not on the cited pages, which a citation split at its period does
- a `Table N:` header in any casing — caught
- an `Item`-column row label appended after a step's own sentence — caught
- a citation split leaving a number below the step-number threshold — caught by the
  sequence check colliding with the real step of that number
- prose appended to a scenario heading, and a heading replaced by leaked debris —
  both caught by attestation

**Not caught: figure box labels taken from the record's own pages.** Only the legend
phrases in `FLOWCHART_FRAGMENTS` are recognised, so text like `Step 12 - Deny
Medicaid Yes No Set Emergency Service Flag` appended to a step passes everything —
every token is genuinely on the cited pages and only the field is wrong. Closing
this properly needs font-aware source indexing, since figure labels sit below 10pt
while step body text is exactly 10pt; a hardcoded phrase list is whack-a-mole.
Finding this class still needs someone reading the source.

`reference_tables` is the one field where placement *is* checked, via
`check_reference_table_pairing`. Reading order does the work: a row's left cell is
followed immediately by its right cell in the PDF, so a swapped `authority` and
`eligibility_group` breaks contiguity even though both strings remain present. Six
cross-row pairings in the corpus stay contiguous and so evade it, but all six are
between rows that share an identical `authority`, where a swap cannot attach a
citation to the wrong group. No harmful mis-pairing evades the check.

A reference-table title truncated to a prefix of the real one passes both
attestation and pairing, since every token is present and no pairing is disturbed.

**Not established — completeness.** Every check verifies that what is present is
attested, not that everything that should be present is. `check_category_coverage`
covers the one case that bit this dataset (a dropped question leaving a record
without one of the standard quality categories). A deleted question that does not
empty a category, or a truncation ending on a content word with punctuation, is
not detected.

**Weak — cross-process borrowing.** Page scoping catches a phrase lifted from a
*distant* process in the same appendix. It often misses an *adjacent* one, because
BCM level text is heavily boilerplate across the processes packed into one file.

---

## extract_bpt_field.py

Extracts one row of a BPT table from the source PDF with its list hierarchy
intact. Useful when correcting a field and you need to see exactly what the
source says.

```bash
.venv/bin/python tools/extract_bpt_field.py \
    data/bpt/financial_management/FM_Manage_TPL_Recovery_BPT_v3.0.json \
    --row "Shared Data"

.venv/bin/python tools/extract_bpt_field.py <json-file> --row Failures --json
```

The JSON file supplies the source PDF and page range from its own metadata, so
extraction is always scoped to the right process.

Three signals recover structure that plain text extraction discards:

- **font** — `SymbolMT U+F0B7` is a first-level bullet, Courier New `o` a
  second-level one.
- **x-indent** — confirms the depth of the text following a marker.
- **y-gap** — separates a wrapped continuation line (~11.5pt below its
  predecessor) from the start of a new item (~17.5pt or more). This is the
  decisive one: line width cannot tell them apart, because a line may end short
  simply because the next word did not fit.

---

## viewer.html

Side-by-side BPT and BCM inspection in a browser. Requires an HTTP server,
because it reads directory listings to discover files:

```bash
python3 -m http.server 8000
# then open http://localhost:8000/tools/viewer.html
```

It pairs each BPT with its BCM on `process_id` rather than by deriving one
filename from the other. Filenames now agree across every pair, so the derived
name is tried first and matches immediately; the `process_id` confirmation keeps
the viewer correct if a naming inconsistency is ever reintroduced.

---

## archived-old-tools/

Superseded scripts, kept for provenance. Nothing here is part of the current
workflow.

| File | Status |
|---|---|
| `validate_2014.py` | Superseded by `verify_against_source.py`, which covers the same structural checks and adds source comparison. Use `--structural-only` for the equivalent fast run. |
| `comprehensive_validation.py` | Validates the **2012** schema (`date`, `page_count`, flat `trigger_events`). Repaired to check `data-archived-2012/` and to fail rather than pass on an empty file set. Do not run it against `data/`. |
| `extract_bpt_2014.py` | Original BPT extraction script for the 2014 migration. |
| `extract_bcm_2014.py.archived` | Original BCM extraction. Deliberately disabled: the BCM records were manually corrected against the source, so re-running it would regress them. |
| `dump_bpt_pdfs.py` | Dumps raw PDF text. |
| `temp_*_dump.txt`, `temp_*_progress.md` | Per-area PDF text dumps and working notes from the 2014 migration. Retained as the evidence trail behind the transcription. |

---

## Adding a tool

Two properties matter more than features:

1. **Never report success without having checked something.** Exit non-zero when
   there is nothing to validate.
2. **Distinguish "I could not verify this" from "this is wrong."** The source
   PDFs are awkward to parse, and a checker that cries wolf gets ignored — which
   is worse than having no checker.
