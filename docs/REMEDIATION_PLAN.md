# Remediation Plan — Round 1: Extraction Defects and Documentation Drift

**Opened**: 2026-09-02
**Scope**: MITA v3.0 (May 2014 Update) dataset in `data/`, plus repository documentation and tooling
**Baseline commit**: `c804abb` (`chore(license): relicense from GPL-3.0 to MIT`)

> **Every figure in this section is as of the end of round 1.** A second round
> followed — see [Round 2](#round-2--september-2026) — which changed some of them.
> For current dataset figures use the
> [README statistics](../README.md#statistics) or run
> `tools/verify_against_source.py`.

This document exists so the work can be resumed if interrupted. Every defect below was
confirmed by comparing the JSON against the source PDFs in `source-pdfs/may-2014-update/`.
Each item records the evidence, the chosen fix, and the reason for that choice.

---

## Guiding principle

**The source PDFs are authoritative.** A JSON value that faithfully reproduces the CMS
document is correct even when the CMS document is internally inconsistent, ungrammatical,
or unhelpful. Fixes in this plan repair *transcription* errors only. Where CMS itself is
inconsistent, the fix is to add navigational metadata or documentation, never to "improve"
the transcribed content.

Two consequences worth stating up front:

- The BCM/BPT process-name divergence (`Manage Treatment Plan` vs `Plans and Outcomes`;
  `Manage` vs `Maintain Reference Information`) is **faithful to CMS**. It is addressed with
  an additive join key, not by editing `process_name`.
- The odd `predecessor_processes` / `successor_processes` entries (prose `NOTE:` blocks, the
  literal string `None`, names like `Manage Contractor Communications` that match no
  process) are all **verbatim in the source PDFs**. They are documented, not edited.

---

## Baseline state (verified before any changes)

Confirmed healthy, and to be preserved as regression checks:

| Check | Result |
|---|---|
| Files | 152 (76 BCM + 76 BPT), all valid JSON |
| Top-level key shape | 1 uniform signature per document type |
| `process_details` keys | 11, uniform across all 76 BPTs |
| `trigger_events` keys | 2 (`environment_based`, `interaction_based`), uniform |
| `levels` keys | 5 (`level_1`..`level_5`), uniform across all 835 questions |
| Filename ↔ `process_code` ↔ `document_type` ↔ `process_name` ↔ directory | 0 mismatches |
| `metadata.source_file` paths resolve | 152 / 152 |
| Page-range provenance (`process_name` appears within claimed span) | 152 / 152 |
| Diagram references resolve to files on disk | 76 / 76, 0 orphans |
| Empty required fields | none |
| BCM questions verbatim in source PDF | 825 / 835 (98.8%) |

Actual content counts (README currently misstates two of these — see X3):

- BCM capability questions: **835**
- BCM level descriptions: **4,175**
- BPT process steps: **822**

---

## Data fixes

### D1 — `PE_Prepare_REOMB_BCM_v3.0.json`: two questions merged into one

**Status**: done

**Evidence** — source PDF `bcm/Performance Management/Performance Management BCM.pdf`,
pages 29–30, contains two distinct capability questions:

1. `Does the State Medicaid Agency use standards in the process?`
2. `If sampling is used, what sampling algorithm is used?`

The JSON collapses both into `capability_questions[1]`, with the question text reading
`"Does the State Medicaid Agency use standards in the process? algorithm is used?"` and
each of the five level cells holding the two source cells concatenated. Example:

```
level_4: "SMA adopts MITA Framework, industry standards, and other nationally recognized
          standards for clinical and interstate information exchange. Maturity level is
          not applicable."
```

`Maturity level is not applicable.` belongs to the *sampling* question's level 4, not to
the standards question. `level_2` additionally contains the page-header artifact
`Prepare REOMB` (see D4).

**Impact**: file reports 10 questions where the PDF has 11; 5 level descriptions are not
independently addressable.

**Fix**: split into two question objects, both categorised
`Business Capability Descriptions`, with level text taken from the PDF table cells.
Insert the sampling question at index 2 to preserve source order.

---

### D2 — `PM_Perform_Provider_Outreach_BCM_v3.0.json`: two questions merged across a page break

**Status**: done

**Evidence** — source PDF `bcm/Provider Management/Provider Management.pdf`, page 34 ends
mid-table with `Business Capability Quality: Effort to Perform; Efficiency` / `How
efficient is the process.`, and page 35 opens with the continuation of that row followed by
`Business Capability Quality: Accuracy of Process Results` / `How accurate are the results
of the process?`.

The JSON has a single `capability_questions[9]`:

```
category: "Business Capability Quality: Data Access and Accuracy"
question: "How efficient is the process. How accurate are the results of the process?"
level_1:  "Process is labor intensive. There is Manual processes result in greater
           opportunity for human error. ..."
```

The efficiency level text is truncated mid-sentence (`There is` — the source continues
`wasted effort or expense to accomplish tasks. Process meets minimum state process
guidelines and SMA performance standards. Efficiency is low.`) and the accuracy text is
appended to it. The assigned category matches neither source question.

**Impact**: file reports 11 questions where the PDF has 12; 5 efficiency level
descriptions are truncated and 5 accuracy descriptions are polluted; one category label is
wrong. This is also why the file appeared to be missing two standard categories.

**Fix**: split into two questions with their correct categories and full level text from
pages 34–35.

---

### D3 — `CO_Perform_Contractor_Outreach_BCM_v3.0.json`: one question missing entirely

**Status**: done

**Evidence** — source PDF `bcm/Contractor Management/Contractor Management BCM.pdf`
page 25 contains the category header `Business Capability Quality: Effort to Perform;
Efficiency` and the question `How efficient is the process.` with all five level
descriptions. Neither the question nor its levels appear anywhere in the JSON.

**Impact**: file reports 11 questions where the PDF has 12; 5 level descriptions lost.

**Fix**: insert the question between the Cost-Effectiveness and Accuracy of Process
Results entries, matching source order.

> Note: the source writes this question with a full stop rather than a question mark
> (`How efficient is the process.`) in both this file and D2. That is reproduced as
> published.

---

### D4 — Page-header contamination in 84 `level_2` fields across 25 BCM files

**Status**: done

**Evidence**: the BCM PDFs repeat the process name in the running page header. Where a
page break falls inside a Level 2 table cell, the header text was spliced into the cell.
Confirmed by checking each occurrence's surrounding word window against the source: 84
occurrences, **all of them in `level_2`**, none legitimate.

Representative cases:

| File | Field | Contaminated text |
|---|---|---|
| `PE_Establish_Compliance_Incident_BCM` | q0.level_2 | `...other stakeholders in `**`Establish Compliance Incident`**` relation to the...` |
| `PL_Develop_Agency_Goals_and_Objectives_BCM` | q1.level_2 | `...with collaboration from `**`Develop Agency Goals and Objectives`**` other agencies...` |
| `PM_Manage_Provider_Grievance_and_Appeal_BCM` | q0.level_2 | `...where the law `**`Manage Provider Grievance and Appeal`**` requires paper documents.` |
| `OM_Process_Claim_BCM` | q8.level_2 | `...improving cost effectiveness `**`Process Claim`**` ratio over Level...` |
| `PL_Manage_Performance_Measures_BCM` | q0.level_2 | `...to accomplish tasks. `**`Manage Performance Measures`** (trailing) |

Distribution: 7 in `PM_Manage_Provider_Grievance_and_Appeal`, 6 each in `PE_Prepare_REOMB`,
`PL_Develop_Agency_Goals_and_Objectives`, `PL_Maintain_Reference_Information`,
`PL_Manage_Health_Benefit_Information`, 5 each in `PE_Establish_Compliance_Incident`,
`PE_Manage_Compliance_Incident_Information`, `PM_Terminate_Provider`, and 1–4 across 17
further files.

**Fix**: remove the injected process name and normalise the resulting whitespace. Each
repaired string must then be confirmed against the source PDF text.

---

### D5 — Corrupted `shared_data` hierarchies in 4 BPT files

**Status**: done

**Affected files**:

- `EE_Determine_Provider_Eligibility_BPT_v3.0.json`
- `EE_Enroll_Provider_BPT_v3.0.json`
- `EE_Inquire_Provider_Information_BPT_v3.0.json`
- `FM_Manage_TPL_Recovery_BPT_v3.0.json`

**Evidence**: the source uses a two-level bullet list (Symbol-font `` for level 1, Courier
`o` for level 2). The extractor treated the markers as trailing content rather than as
delimiters, shifting every marker onto the *preceding* item. Source (PDF p32,
`Enroll Provider`):

```
Provider data store including:
   Provider demographics
   Provider network
   Contract information
     o Type
     o Specialty
     o Enrolled Program
     o Jurisdiction
     o Payment Information
   Provider taxonomy
```

Current JSON:

```json
["Provider data store including: \uf0b7", "Provider demographics \uf0b7",
 "Provider network \uf0b7", "Contract information o", "Type o", "Specialty o",
 "Enrolled Program o", "Jurisdiction o", "Payment Information \uf0b7",
 "Provider taxonomy", "\uf0b7", ...]
```

Damage: 24 stray `U+F0B7` private-use glyphs, 18 trailing `" o"` markers, and 2 array
elements consisting of nothing but a bullet glyph. Parent/child relationships are lost —
a consumer cannot tell that `Type` and `Specialty` qualify `Contract information`.

**Fix**: rebuild each array from the source. One array element per top-level bullet;
second-level items appended to their parent element as indented lines, matching the
convention already used in `process_steps` (`"parent\n  a. child"`). Sub-items use
`"\n  - "` since the source bullets are unlettered.

---

### D6 — Malformed BCM question texts

**Status**: done

| File | Index | Current | Source |
|---|---|---|---|
| `CO_Manage_Contractor_Grievance_and_Appeal_BCM` | q1 | `How central is the grievance and appeals process? appeals process?` | `How central is the grievance and appeals process?` |
| `PM_Manage_Provider_Grievance_and_Appeal_BCM` | q1 | `How central is the grievance and appeals process? grievance and appeals process?` | `How central is the grievance and appeals process?` |
| `CO_Perform_Contractor_Outreach_BCM` | q0 | `Is the process manual or automatic?` | `Is the process primarily manual or automatic?` |
| `PM_Perform_Provider_Outreach_BCM` | q0 | `Is the process manual or automatic?` | `Is the process primarily manual or automatic?` |

The first two are duplicated tails from table-cell line wrapping; the last two drop a word.

**Fix**: replace with the source text.

---

### D7 — Miscategorised question

**Status**: done

`PM_Manage_Provider_Communication_BCM_v3.0.json` q9 (`How accurate are the process
results?`) is labelled `Business Capability Quality: Data Access and Accuracy`. The source
places it under `Business Capability Quality: Accuracy of Process Results`. This is why the
file appeared to lack that standard category.

**Fix**: correct the `category` value.

---

### D8 — Source note concatenated into question text

**Status**: done

`FM_Manage_Estate_Recovery_BCM_v3.0.json` q5:

```
"How timely is the end-to-end process? Note: Due to the variables involved in estate
 recovery process (i.e., wills, lawsuits, claims and other procedural steps inherent in
 the probate process), it is difficult to estimate the end-to-end timeline."
```

The schema already defines an optional `note` field for exactly this, used by 5 questions
elsewhere. This is the only question in the corpus whose text does not end at its question
mark.

**Fix**: `question` becomes `How timely is the end-to-end process?`; the remainder moves
to `note`. No content is discarded.

---

### D9 — Hyphen line-break artifacts

**Status**: done

278 occurrences of `word- word` where the source hyphenated across a line break, e.g.
`Decision- making` (129×), `state- specific` (55×), `machine- readable` (9×),
`near- real` (6×).

**Care required**: some are genuine suspended hyphens and must be preserved — `pre- and`
(as in `pre- and post-approved`), `payer- to`/`to- payer` (from `payer-to-payer` split
differently), `up- to`, `point- of`. The distinguishing test is *layout*, not text: if the
hyphen ends a line in the PDF and the next word starts the following line, the space is an
extraction artifact; if `X- Y` occurs within a single line, it is authored.

**Fix**: use per-line PDF text to classify each occurrence, join only line-break cases,
and report any that cannot be classified rather than guessing.

---

### D10 — No stable BCM↔BPT join key

**Status**: done

CMS uses different process names in the BPT and BCM documents for two processes, and the
extraction faithfully reproduces both:

| Area | BPT says | BCM says |
|---|---|---|
| Care Management | `Manage Treatment Plan and Outcomes` | `Manage Treatment Plans and Outcomes` |
| Plan Management | `Manage Reference Information` | `Maintain Reference Information` |

Filenames diverge to match. Any consumer joining a BCM to its BPT on `process_name` or on
filename stem silently drops these two processes — a 2-in-76 silent data loss that is easy
to miss and hard to debug. (An unrelated project independently hit the `Plan`/`Plans`
case.)

**Fix**: add a `process_id` field to all 152 files — a canonical, stable slug that is
identical for a BCM/BPT pair, e.g. `CM_MANAGE_TREATMENT_PLAN_AND_OUTCOMES` and
`PL_MANAGE_REFERENCE_INFORMATION`.

**Why additive rather than a rename**: the README advertises fetching files by raw GitHub
URL, so renaming files or changing `process_name` would break existing consumers and would
also discard the faithful record of what each CMS document actually says. Adding a field is
backward compatible: existing code keeps working, and new code gets a reliable key.
Canonical form follows the BPT spelling, since Appendix C is the process-model source of
record. The divergence is documented in `DATA_STRUCTURE.md` (X5).

---

### D11 — `EE_Enroll_Provider_BCM_v3.0.json`: question bled in from the next process

**Status**: done
**Found by**: `tools/verify_against_source.py` (not caught in the initial manual sweep)

**Evidence**: the file carries 13 questions, one more than any sibling, and `q12` repeats
`Is the process primarily manual or automatic?` — already present as `q1`.

The BCM appendix packs several processes into one PDF. Page 50 holds the tail of
`Enroll Provider`'s final question *and* the opening rows of `Disenroll Provider`. The
extraction's page range (42–50) swept in the neighbour's first question. Proof: `q12`'s
`level_3` reads *"SMA fully automates the provider **disenrollment** process within the
intrastate"* — it describes Disenroll Provider. It is a truncated copy of
`EE_Disenroll_Provider_BCM` `q0`.

Page range 42–50 is otherwise correct: page 50 genuinely contains the tail of
`Enroll Provider` `q11`, which is captured correctly.

**Fix**: delete `q12`. 13 → 12 questions. Page range unchanged.

A detector for this defect class (`check_cross_process_bleed`) is part of the verification
tool: same source PDF + overlapping page ranges + last question of one file equal to the
first question of the other. It reports exactly this one instance across the corpus.

---

### D12 — `EE_Enroll_Provider_BPT_v3.0.json`: word lost across a page break

**Status**: done

**Evidence** — source pages 30→31. Page 30 ends:

> The appropriate communications and outreach processes for follow-up

Page 31 resumes (after the running header):

> with the affected parties, including informing parties of their procedural rights.

The JSON `description` reads `"...outreach processes for follow- with the affected
parties..."` — the word **`up`** was dropped and a dangling hyphen left behind.

**Fix**: restore to `follow-up with the affected parties`.

**Note for D9**: this string matches the `word- word` pattern but must not be repaired by
joining — that would yield `followwith`. D9 must run after D12, or exclude it.

---

### D13 — Dash characters normalised to ASCII (documentation only)

**Status**: done (documentation)

The source PDFs use U+002D (3,243×), U+2013 en dash (768×), U+2010 hyphen (199×) and
U+2014 em dash (3×). The JSON contains **only** U+002D — every dash was normalised during
extraction. Curly apostrophes (U+2019), by contrast, were preserved as published.

This inconsistency is defensible as a usability choice and is **not** being reversed:
mass-rewriting 970 characters carries real regression risk for no practical gain, and ASCII
hyphens are easier for consumers to match on. It is, however, undocumented, and the
asymmetry with quotes is surprising.

**Fix**: document both behaviours in `DATA_STRUCTURE.md` (X5).

One consequence does need a data fix. In `CM_Authorize_Referral_BPT` `process_steps[6]` the
source uses an en dash as a *separator*:

> 7. Member eligibility– for social service model, ...

Normalised to ASCII with no surrounding space, this reads as a broken hyphenation
(`eligibility- for`) and is a trap for the D9 repair pass. The sibling file
`CM_Authorize_Service_BPT` `process_steps[6]` already renders the same construction as
` - `. Align the two so the separator is unambiguous and D9 cannot corrupt it.

---

### D14 — Alternate-path block welded onto the final numbered step (4 BPT files)

**Status**: done
**Found by**: `tools/extract_bpt_field.py` while rebuilding D5

Appendix C ends several processes with a numbered step and then a separate
`Alternate Path:` / `Alternate Business Process Path:` block. In four files that
block was concatenated onto the last step, so the step's text runs past its own
full stop into unrelated content.

| File | Step | Welded-on text |
|---|---|---|
| `CM_Authorize_Referral_BPT` | 19 | `Alternate Path: For the authorization of some services, ...` |
| `CM_Authorize_Service_BPT` | 19 | `Alternate Path: For the authorization of some services, ...` |
| `CM_Manage_Treatment_Plan_and_Outcomes_BPT` | 5 | `Alternate Path:` |
| `EE_Determine_Provider_Eligibility_BPT` | 20 | `Alternate Business Process Path: ... ` + 3 raw `U+F0B7` bullets |

**Fix**: split at the alternate-path boundary so the block becomes its own array
element, matching both the source layout and the treatment already used in
`FM_Manage_1099_BPT` and `OM_Process_Claim_BPT`. The EE file's raw bullet glyphs
become `\n  - ` sub-items. Content is preserved exactly — verified by comparing
word counts before and after.

**Note**: this fix is deliberately surgical. An earlier attempt regenerated the
whole `process_steps` array from the source and flattened the existing three-level
`a.` / `i.` sub-step nesting, which is correct in the current data and was added
deliberately. Only the alternate-path boundary is touched.

---

### D15 — `EE_Determine_Provider_Eligibility_BPT`: sub-steps lost across a page break

**Status**: done
**Found by**: word-count comparison during D14

Source step 12 (`Assess categorical risk to determine appropriate required
screening level`) has three lettered sub-items. Source page 26 carries `a. Limited
Risk includes:` with its three roman-numeral items; page 27 continues with
`b. Moderate Risk includes:` (2 items) and `c. High Risk includes:` (3 items).

Only branch `a.` was extracted. Branches `b.` and `c.` — seven lines in total,
including the substantive screening requirements *Unscheduled or Unannounced Site
Visits*, *Criminal Background Check* and *Fingerprinting* — were dropped.

This matters beyond completeness: provider screening levels are a federal
requirement, and a consumer reading this process would conclude that moderate and
high risk screening are undefined.

**Fix**: append the missing branches using the nesting already present in that
step (two spaces for `a.`/`b.`/`c.`, four for roman numerals). Each restored
fragment was confirmed present in the source before insertion.

---

## Documentation and tooling fixes

### X1 — Broken documentation links and unrunnable validation instructions

**Status**: done

Commit `0879669` moved files into `docs/archived-old-docs/` and
`tools/archived-old-tools/` without updating the documents that reference them. Currently
broken:

| Referenced from | Target | Resolution |
|---|---|---|
| README, CONTRIBUTING | `docs/CONVERSION_METHODOLOGY.md` | restored, rewritten for the 2014 dataset and current tooling |
| README, CONTRIBUTING | `docs/EXAMPLES.md` | restored; four examples that treated `trigger_events` as a flat array corrected; `process_id` join example added |
| README, CONTRIBUTING | `docs/2014_MIGRATION_PROJECT.md` | stays archived as a historical record; links repointed to `docs/archived-old-docs/` and an archive banner added |
| README | `tools/README.md` | written fresh for the current tools |
| README, CONTRIBUTING | `tools/validate_2014.py` | superseded by `verify_against_source.py` (same structural checks, plus source comparison, plus `--structural-only`); references replaced |
| README, CONTRIBUTING | `tools/comprehensive_validation.py` | broken and 2012-schema only — see X2; references removed |
| README | `tools/viewer.html` | restored, with its BCM pairing fixed to use `process_id` |
| `docs/DATA_STRUCTURE.md` | `EXAMPLES.md` | resolves now that EXAMPLES.md is back |
| `data-archived-2012/README.md` | `../tools/README.md` | resolves now that tools/README.md exists |

The README's Validation section instructed `cd tools && python validate_2014.py`, which
could not run. `../../issues`-style links are intentional GitHub-relative links and are fine.

**Verified**: every relative Markdown link in the repository resolves, every documented
command runs as written, and all 17 runnable Python examples in `EXAMPLES.md` execute
successfully. Stale internal paths remain only inside `tools/archived-old-tools/temp_*`
working notes, which are labelled scratch material from the 2014 migration.

---

### X2 — `comprehensive_validation.py` reports success without validating anything

**Status**: done

Two independent faults:

1. It walks `json_output/`, a directory that does not exist anywhere in the repo. It finds
   0 files and prints `✓ VALIDATION PASSED / All files are structurally correct and match
   source PDFs`. Verified by running it.
2. It validates the **2012** schema, requiring fields (`date`, `page_count`) that the 2014
   schema does not have. Even pointed at `data/`, it would fail all 152 files.

Both README and CONTRIBUTING name this script as the contributor quality gate, so the one
command a contributor is told to run before opening a PR is a guaranteed false pass.

`validate_2014.py` is sound — it correctly reports 152/152 passing and accurate statistics.

**Fix**: retire the broken script as the documented gate and replace it with something that
genuinely validates, including source-PDF fidelity checks. Never let a validator exit 0 on
an empty file set.

---

### X3 — Stale README statistics

**Status**: done

| Statistic | README claims | Actual |
|---|---|---|
| BCM questions | 815 | **835** |
| BCM maturity levels | 4,075 | **4,175** |
| BPT process steps | 822 | 822 ✓ |

Counts will change again once D1–D3 add three questions and 15 level descriptions. Update
last, after the data fixes land.

---

### X4 — Archived 2012 dataset presents itself as current

**Status**: done

`data-archived-2012/README.md` is titled *"MITA Data Directory"*, opens with "This
directory contains all MITA v3.0 documents", documents `data/` paths rather than its own,
and states 144 files with 4 EE processes. Nothing marks it as superseded, so a reader who
lands there will take it as live data.

**Fix**: add a prominent archive banner, correct the paths to point at the archive
directory, and cross-link to the current dataset.

---

### X5 — Undocumented and inaccurate schema documentation

**Status**: done

In `docs/DATA_STRUCTURE.md`:

- `process_id` (new in D10) needs documenting as the recommended join key.
- `metadata.manually_corrected` exists in 2 files (`FM_Manage_Estate_Recovery_BCM`,
  `FM_Prepare_Member_Premium_Invoice_BCM`) but is not documented.
- The BCM/BPT `process_name` divergence needs an explicit warning so consumers do not
  join on it.
- `predecessor_processes` / `successor_processes` need a caveat: they are free text as
  published by CMS, not resolvable identifiers. Of 616 references, 130 do not resolve to a
  process in this dataset. Most point at Member Management processes, which the framework
  defines but never published as BPT/BCM documents; a few are prose `NOTE:` blocks, the
  literal string `None`, or CMS's own name variants (`Manage Contractor Communications`,
  `Manage Accounts Payment Disbursement`, `Send Outbound Information`). **All are verbatim
  in the source PDFs and must not be edited.**
- The `diagrams` description says "primarily in Eligibility & Enrollment BPTs", implying
  several. Exactly 1 of 76 BPT files (`EE_Determine_Member_Eligibility`) has any, with 76
  images.
- `Business Capability Quality: Cost Effectiveness` is the value used in the data, while
  the PDFs write `Cost-Effectiveness`. Worth noting so the category list is unambiguous.

---

## Deliberately not changed

| Item | Reason |
|---|---|
| `predecessor_processes` / `successor_processes` contents | Verbatim in source PDFs, including the `NOTE:` prose, `None`, and name variants. Documented in X5 instead. |
| `process_name` values, including `Plan`/`Plans` and `Manage`/`Maintain` | Faithful to CMS. Addressed additively via `process_id` (D10). |
| `How efficient is the process.` full stop | As published in the source. |
| Filenames | Renaming would break the raw-URL access pattern the README advertises. |
| `FM_Manage_Capitation_Payment_BPT` having only 2 process steps | Verified correct against PDF p21. |
| 36 scratch dump files in `tools/archived-old-tools/` (3.4 MB) | They are the PDF text dumps used to verify extraction. Harmless, and useful provenance. Flagged for the maintainer to decide; not deleted here. |

---

## Fix ordering constraint

D12 must land before D9. `follow- with` matches the hyphen-artifact pattern but the correct
repair is to restore a dropped word, not to join the fragments. Likewise D13's separator fix
protects `eligibility- for` from D9. Run D9 last among the text repairs.

## Validation strategy

1. A reusable checker (`tools/verify_against_source.py`) compares JSON against the source
   PDFs: BCM question and level text, BPT fields, page-header contamination, bullet-marker
   leakage, hyphen artifacts, cross-process bleed-over, and structural invariants.
2. Run it before any edits to capture a baseline, then after each fix.
3. Re-run the full baseline invariant table above to confirm no regressions.
4. Independent sub-agent review of the data changes and the documentation changes.

## Final verification

### Invariants (re-checked after every change in round 1)

Both columns are **round 1** figures: "Before" is the state at the start of that
round, "After" is the state at its end. Two rows moved again in round 2 and are
annotated below; for current figures see
[README statistics](../README.md#statistics) or run the validator.

| Check | Before | After |
|---|---|---|
| Files, all valid JSON | 152 | 152 |
| BCM / BPT top-level key shapes | 1 / 1 | 1 / 1 |
| `process_details` key shapes | 1 (11 keys) | 1 (11 keys) — round 2: 2 shapes, 11 keys ×75 plus 12 keys ×1 (the optional `reference_tables`) |
| `trigger_events` key shapes | 1 | 1 |
| `levels` key shapes | 1 | 1 |
| Filename ↔ code ↔ type ↔ name mismatches | 0 | 0 |
| `metadata.source_file` resolving | 152/152 | 152/152 |
| Page-range provenance holds | 152/152 | 152/152 |
| Diagram refs / on disk / orphans | 76 / 76 / 0 | 76 / 76 / 0 |
| Empty required fields | 0 | 0 |
| `process_id` values, each with one BCM + one BPT | — | 76, all paired |
| Private-use bullet glyphs | 27 | **0** |
| Dangling `o` sub-bullet markers | 18 | **0** |
| Questions continuing past their `?` | 4 | **0** |
| Process name spliced into `level_2` | 85 occurrences / 25 files | 1 / 1 (legitimate, corroborated by the source) |
| `word- word` occurrences | 278 | 4 (all authored suspended hyphens) |
| Fields with a word absent from their cited pages | 12 | **0** |
| Fields ending on a dangling function word | 10 | **0** |
| BCM capability questions | 835 | 837 |
| BCM level descriptions | 4,175 | 4,185 |
| BPT process steps | 822 | 826 — round 2: 832 entries, being 812 numbered steps plus 20 scenario headings |

`tools/verify_against_source.py` reports **0 errors, 57 warnings**. Every warning
is a capability question whose source cell wraps across a page break, reassembled
from two fragments; the tool prints both fragments for inspection.

### Change-scope audit

Every changed string in `data/` was classified against the declared fix list.
**Nothing was changed that this plan does not account for:**

| Strings | Fix |
|---|---|
| 257 | D9 hyphen join |
| 152 | D10 `process_id` added |
| 77 | D4 header splice removed (73 alone, 4 combined with a hyphen join) |
| 57 | D1 question split (re-indexed) |
| 26 | D2 and D3 question split / restore (re-indexed) |
| 25 | D16 / D17 truncation restored |
| 23 | D5, D14, D15 restructuring (re-indexed) |
| 7 | D17 wrapped-cell joins (re-indexed) |
| 5 | D6 duplicated tail, D7 category, D8 note split |
| 1 | D16 page-furniture entry removed |
| **0** | **unexplained** |

Every changed string was classified mechanically against the declared fix list.
Nothing in `data/` changed that this plan does not account for.

### Negative control

Ten defect classes were injected into a copy of the dataset. **Nine were
detected**: a question lifted from a sibling process in the same PDF, a fabricated
maturity level, a truncated word, a word-boundary truncation, a duplicate
`process_id`, a page footer spliced into a level, a dangling `o` marker in
`process_steps`, a lower-case hyphen artifact, and a duplicated question tail.

**One was not**: swapping `level_1` and `level_5` between maturity ratings. Level
text is verified at the word level, not the sequence level, so a reordering whose
words are all correct passes. This is a real limitation, documented in
`README.md` and `tools/README.md` rather than papered over.

The data was then restored and re-verified clean.

### Documentation

- Every relative Markdown link in the repository resolves (0 broken).
- Every documented command runs as written.
- All 17 runnable Python examples in `EXAMPLES.md` execute successfully.
- `tools/viewer.html` was exercised in a browser across all 9 business areas:
  76/76 processes pair correctly, no console errors.

---

## Review round: what the first pass got wrong

Four independent reviews were run against the completed first pass. They found a
transcription error introduced *by* the remediation, a design flaw in the verifier
that allowed it, and a large coverage gap. All are fixed. Recording them because
the failure modes are instructive.

### R1 — a word was fabricated, and the verifier could not see it

`PM_Perform_Provider_Outreach_BCM` q0 was changed to `Is the process primarily
manual or automatic?`. The source pages that record cites, 29–30 of
`Provider Management.pdf`, read `Is the process` / `manual or` / `automatic?`. The
word `primarily` there belongs to the Level 1 cell.

The mistake was counting occurrences across the whole PDF instead of within the
record's own pages: `Is the process primarily manual or automatic?` occurs four
times in that file, on pages 1, 8, 14 and 21 — all *other* Provider Management
processes. D6's premise was wrong for both outreach files; the CO half was never
applied, so `CO_Perform_Contractor_Outreach` was correct all along.

**Reverted.** This is the same cross-process contamination as D11, committed by
the remediation rather than found by it.

### R2 — the verifier searched the whole document, not the cited pages

`check_fidelity` traced question text against the entire PDF while using the page
span only for the `process_name` provenance check. That is precisely why R1 passed
with 0 errors. Now scoped to the span. Re-injecting R1 is detected.

### R3 — 95.6% of the corpus text was never compared to the source

Only BCM questions and notes were traced. A reviewer demonstrated that replacing
**all 4,185 maturity level descriptions** with a fabricated sentence still
reported `PASSED - 0 errors`. The plan's own validation section claimed level and
BPT text were compared; they were not.

Fixed by adding token attestation over every content field. This immediately
surfaced **12 previously unknown defects** — fields containing a truncated word
(`calend` for `calendar`, `Payro` for `Payroll Deducted and Other Group Premium`,
`modificatio` for `modifications to`) and two entries that were page furniture
rather than content. A dangling-tail check then found **10 more**, where the
truncation fell on a word boundary. All 22 are repaired: see D16 and D17.

### R4–R7 — verifier hardening

`line_assembly` accepted arbitrary line subsequences with a 98.3% false-accept
rate on fabricated text and never fired on real data; removed. `MAX_FRAGMENTS`
reduced from 4 to 2. `process_id` uniqueness was documented as an invariant but
not enforced — a duplicate passed silently; now an error. Page footers were absent
from the furniture list and two entries carried dashes the dataset's own
normalisation never produces. The dangling-`o` check covered 4 list fields of 12.
The hyphen pair test was case-sensitive. `window_start` returned one fewer word
than asked for. The `AUTHORED_HYPHEN_SPLITS` allowlist was replaced by a
per-occurrence layout test, which also made D13's text edit unnecessary — that
edit is reverted, and the source's `eligibility- for` is preserved as published.

### D16 — 12 fields with a word absent from their cited pages

**Status**: done

Text lost at a page break leaving a truncated word. Repaired from the cited pages:
`CM_Authorize_Referral` (`especially in the case where the member required`),
`CM_Establish_Case` (`Other Procedure`), `CO_Award_Contract` (`verify proposal
content against`), `CO_Manage_Contractor_Grievance_and_Appeal` (`This business
process supports the Manage Performance Measures`),
`FM_Manage_Accounts_Payable_Disbursement` (`Payroll Deducted and Other Group
Premium`), `FM_Manage_Contractor_Payment` (`Agency staff responsible for
Contract`), `OM_Submit_Electronic_Attachment` (`Process`),
`PE_Manage_Compliance_Incident_Information` (`modifications to`),
`PM_Manage_Provider_Grievance_and_Appeal` (`SMA formally notifies provider of`),
`PM_Terminate_Provider` (`calendar days before the effective date of termination
for a`). Two further entries — `OM_Calculate_Spend-Down_Amount` `results[3]` and
`OM_Process_Claim` `performance_measures[4]` — were page furniture with no source
counterpart and were removed.

### D17 — 10 fields truncated at a word boundary

**Status**: done

Same cause, but every remaining word is attested, so only the dangling tail
betrays it. Six restorations, including two substantive ones in
`EE_Determine_Member_Eligibility` `process_steps[6]` and `[7]` that recover
mandatory MAGI eligibility-group logic, and `OM_Process_Claim` `process_steps[3]`
and `[14]`. Four were wrapped cells split across adjacent array elements and were
rejoined: `EE_Inquire_Provider_Information` `results`,
`FM_Manage_Incentive_Payment` `shared_data`,
`PL_Manage_Health_Benefit_Information` `results`,
`PL_Manage_Performance_Measures` `shared_data`.

### Second review round

The hardened verifier was reviewed again. It confirmed R1–R7 were genuinely fixed
— the experiment that previously replaced all 4,185 level descriptions with
fabricated text and still printed `PASSED` now yields 4,185 errors — and found
three more problems, all fixed:

**The artifact list could not match.** `canon()` collapses `"- "` to `"-"`, and the
artifact literals were written by hand in un-normalised form. Six of eleven
entries were dead code, including the page footer added in R6 — the furniture
most likely to be spliced into a cell. The list is now normalised at import, with
an assertion that each entry is `canon()`-stable so this cannot recur silently.

**Missing content was not checked at all.** Deleting a whole capability question
passed with 0 errors. Every check verified that what is present is attested, not
that everything that should be present is — which is exactly how D3 went
unnoticed in the first place. `check_category_coverage` now flags a record lacking
one of the standard capability-quality categories; re-deleting D3's question is
detected.

**The documented limitation understated the gap.** It said "word order within
maturity level descriptions or BPT prose". The reviewer demonstrated eleven
passing permutations, including all five levels rotated corpus-wide, `results`
exchanged with `failures`, and reordered questions. The honest statement is that
**placement is not established at all**: any permutation of strings across fields,
array positions or level keys passes provided the words stay within the record's
page span. `README.md` and `tools/README.md` now say that.

Two further improvements came out of it. The two-fragment fallback now requires
the split to straddle a page boundary — all 57 legitimate warnings do, which both
tightens the check and separates them from word-deletion defects. And `category`,
`predecessor_processes` and `successor_processes` are now attested, having been
silently excluded; that is 55,000 characters of CMS prose, including the `NOTE:`
blocks, previously unverified.

### Documentation corrections

README and `CITATION.cff` claimed every record was verified against source when
the sequence check covered questions and notes only; both now state what is and
is not established. The false claim that "duplicated or reordered text still
fails" is removed from `CONVERSION_METHODOLOGY.md` and `tools/README.md`. Counts
in the invariant and change-scope tables were recomputed. `DATA_STRUCTURE.md` now
warns that `process_id` must be read rather than derived, records that two
questions end in a full stop, documents the three indent widths actually present
rather than claiming two, describes the nested `shared_data` elements, and lists
the `boolean` and `number` types the data contains.

### D18 — the BCM/BPT naming divergence, reconciled

**Status**: done

D10 addressed this additively with `process_id` and deliberately left filenames and
`process_name` alone, on the reasoning that both spellings are faithful to their own
CMS appendix and that renaming would break raw-URL consumers.

That reasoning was incomplete. A downstream consumer pairs the two halves by
extracting a code from the filename, so it built **74 capabilities from 152 files**
and silently dropped CM06 and PL07 entirely — they appeared nowhere in its
dashboard, browser or exports. An additive key does not help a consumer that
cannot know to use it.

**New evidence settles which name is correct.** The framework's own
`business-architecture/Business Architecture Table of Contents.pdf` assigns the
official process codes and uses:

- `CM06 Manage Treatment Plan and Outcomes`
- `PL07 Manage Reference Information`

Occurrence counts confirm the split is systematic rather than a transcription slip:
Appendix C uses those names (10× and 13×), Appendix D uses `Manage Treatment
Plans and Outcomes` (8×) and `Maintain Reference Information` (8×). So the two CMS
documents genuinely disagree, and Appendix D is the outlier against both Appendix C
and the framework index.

**Fix**: the two BCM files were renamed and their `process_name` updated to the
framework-index name. The as-published Appendix D spelling is retained in a new
optional `metadata.source_process_name`, and the verifier checks page-range
provenance against that field, so no fidelity is lost. `process_id` values were
already the framework-index form and did not change.

Pairing now yields 76 by filename, by `process_name`, and by `process_id`. No
cross-references needed updating: the Appendix D spellings appeared nowhere else in
the corpus. Corpus-wide, filename and `process_name` agree on all 152 records, so
no other pair has latent drift.

This is a breaking change for anyone fetching those two files by URL, and is
called out as such in the README changelog.

## Progress log

| Item | Status |
|---|---|
| Plan document | done |
| Verification tooling | done — `tools/verify_against_source.py`, `tools/extract_bpt_field.py` |
| D1 PE_Prepare_REOMB split | done — 10 → 11 questions |
| D2 PM_Perform_Provider_Outreach split | done — 11 → 12 questions |
| D3 CO_Perform_Contractor_Outreach missing question | done — 11 → 12 questions |
| D4 level_2 header contamination | done — 84 fields across 25 files |
| D5 shared_data hierarchies (4 files) | done — 67 → 21 elements, zero words changed |
| D6 malformed question texts | done — 2 duplicated tails; the two `primarily` claims were wrong (see R1) |
| D7 miscategorised question | done |
| D8 note extraction | done |
| D9 hyphen artifacts | done — 274 joined, 4 authored ones preserved |
| D10 process_id join key | done — 76 unique ids, all paired |
| D11 EE_Enroll_Provider_BCM bleed-over question | done |
| D12 EE_Enroll_Provider_BPT lost word (`follow-up`) | done |
| D13 dash normalisation | documented; the separator edit was reverted (see R7) |
| D14 alternate-path block welded to final step (4 files) | done |
| D15 EE_Determine_Provider_Eligibility lost sub-steps | done |
| D16 truncated words (12 fields) | done — found by the review round |
| D17 word-boundary truncations (10 fields) | done — found by the review round |
| D18 BCM/BPT naming divergence reconciled | done — 2 files renamed; pairing now 76 |
| R1 revert the fabricated `primarily` | done |
| R2 page-scope the verifier's trace | done |
| R3 extend tracing to level and BPT text | done |
| R4 tighten fragment fallback, remove line assembly | done |
| R5 enforce `process_id` uniqueness | done |
| R6 verifier hardening (footers, case, indices, window) | done |
| R7 revert the D13 text edit | done |
| X1 documentation links | done — all relative links resolve; examples execute |
| X2 validator | done — `comprehensive_validation.py` repointed at `data-archived-2012/`, exits 2 on an empty file set |
| X3 README statistics | done — 837 questions, 4,185 levels, 826 steps |
| X4 archive labelling | done |
| X5 schema documentation | done |
| Full re-validation | done — 0 errors, 57 warnings |
| Sub-agent review | done — 4 reviews; findings recorded above and all addressed |
---

# Round 2 — September 2026

Prompted by an external reviewer reporting that `FM_Manage_Estate_Recovery_BPT`
publishes steps 10-21. They were right that the transcription is accurate and the
defect is CMS's. Checking it surfaced a second, unrelated file that *was*
misextracted.

**The rule applied throughout this round**, and now the repository's stated
policy: if the JSON disagrees with the PDF, the extraction is wrong and gets
fixed. If the JSON agrees with the PDF and the PDF is wrong, the defect is
mirrored and recorded in [SOURCE_DEFECTS.md](SOURCE_DEFECTS.md). No editorial
corrections. One consequence worth noting: because every fix moves the data
toward the source, no validator exception mechanism was needed — the alternative
policy (correcting CMS's typos) would have required one, since the fidelity layer
raises a hard error for any text it cannot find in the cited pages.

## D19 — `EE_Determine_Member_Eligibility_BPT` step array

Only 5 of 21 entries were clean. Found by reconstructing the step column from the
PDF text layer using font metrics: step body text is 10.0pt ArialMT, section
headings 10.0pt Arial-BoldMT, table content 9.0pt, and every figure label is
below 10pt. That separation is what made the repair tractable; the earlier attempt
at geometric column reconstruction (documented in round 1) had failed at 17.8%
miss rate.

| Defect | Detail |
|---|---|
| 6 truncated steps | 2, 4, 7, 8, 11, 14 — text lost at page boundaries. Steps 7 and 8 were missing sub-items outright; step 11 was missing all of sub-item `h`, which step 11e directs the reader to. |
| A NOTE dropped entirely | The `Verifications` NOTE on p.3, 397 characters, styled identically to the five NOTEs that were retained. It is the only place the source says steps 2-4 may be performed in any order, and the only place it cites 42 CFR 435.945(j). It sits between step 1c and step 2 and states its own scope, so it is carried as a trailing NOTE line on step 1 — the convention every other NOTE in the corpus uses; there are no standalone NOTE entries anywhere in the data. |
| Space before a comma removed | Step 7e reads `go to 7f , if not` in the source. The extraction tidied it. Restored, since "reads better than the source" is a defect under this policy. |

3,126 characters of published text restored in total.
| 5 spurious entries | `42 CFR 435.` split at its period, so `435.` read as a step number and Table 6/7 rows became steps. |
| Figure text in step 5 | The page-4 swim-lane diagram's labels, ~600 characters. The figure itself is already in `diagrams`, so nothing is lost by removing them. |
| Table text in steps 9 and alt-1 | Table 3 and Table 7 rows. |
| Section headings absorbed | Tails of steps 3, 10 and 13. |
| Step 15 merged with a heading | `15. END Alternate Scenario 1 - Auto Eligible` split into the step and the heading. |

Entries went 21 → 18. The three CMS typos inside the restored text — `eligibile`,
`orHealth`, `Medicaid..` — were reproduced as published, and the validator now
confirms they are still present.

## D20 — dropped scenario headings (11 headings across 6 records)

Where a process defines more than one scenario the source labels each one. The
extraction had dropped the labels, so step numbering restarted at 1 with nothing
to explain it. Restored verbatim:

| Record | Headings restored |
|---|---|
| `CM_Manage_Registry` | `Alternate Path:` |
| `FM_Manage_1099` | `Preparation/Maintenance` |
| `FM_Manage_Fund` | `Manage Fund`, `Manage FMAP`, `Manage FFP`, `Draw and Report FFP` |
| `OM_Prepare_Provider_Payment` | `HCBS Payment`, `Capitation Payment` |
| `PL_Manage_Reference_Information` | `Designate Approved Services and Drug Formulary` |
| `EE_Determine_Member_Eligibility` | `Full Eligibility Determination or Renewal`, `Alternate Scenario 1 - Auto Eligible` |

The numbering restarts themselves were **not** touched — they are faithful. 9 of
76 BPT records contain more than one scenario; `FM_Manage_Fund` has four.

**The first attempt at this was wrong, and a review caught it.** For 5 of the 11
headings the extraction had not dropped the label at all — it had *absorbed* it
into the tail of the preceding step. Adding the heading as a new entry without
removing the absorbed copy left the step body disagreeing with the source and the
label present twice:

| Record | Step ended | Source ends |
|---|---|---|
| `FM_Manage_Fund` step 11 | `...over allocations. Manage FMAP` | `over allocations.` |
| `FM_Manage_Fund` FMAP step 6 | `...approved rates. Manage FFP` | `approved rates.` |
| `FM_Manage_Fund` FFP step 8 | `...Send Outbound Transaction. Draw and Report FFP` | `Send Outbound Transaction.` |
| `OM_Prepare_Provider_Payment` step 5 | `...information to member. Capitation Payment` | `to member.` |
| `PL_Manage_Reference_Information` step 7 | `...addition or modification. Designate Approved Services and Drug Formulary` | `modification.` |

All five absorbed copies were stripped and each step tail re-verified against the
source. This is the same defect class D19 fixed inside the EE record; diagnosing
it as "the label is missing" is what hid it, because once that is the diagnosis,
adding the label looks like the whole fix. `check_step_structure()` now detects
it directly.

## D21 — invented heading decoration (3 headings, 2 records)

The inverse defect: text the extraction added that CMS never wrote.
`--- Alternate Path: Suspended Claim ---` and two others carried `---` wrappers,
and `FM_Manage_1099` had gained a colon the source does not use. Normalised to
the exact source labels (`Alternate Path - Additional Requests`,
`Alternate Path - Corrections`, `Alternate Path: Suspended Claim`,
`Alternate Path: Third Party Liability Failures`, `Alternate Path: Suspended
Encounter`).

## D22 — dropped word

`EE_Disenroll_Provider_BPT` step 9 ended at `...with disenrollment`; the source
continues `information.` after a page break. Same class as D12.

## D23 — reference tables absent from the schema

`EE_Determine_Member_Eligibility_BPT` steps cite seven numbered tables. Tables 1,
2 and 4 had been dropped entirely and 3, 5, 6 and 7 had leaked into step text, so
the capture was inconsistent either way.

Added `process_details.reference_tables` — 7 tables, 57 rows of
`{authority, eligibility_group}`, shaped after the existing `diagrams` field and
optional, since this is the only record in the corpus whose source pages carry
numbered tables (0 of 76 BCM, 1 of 76 BPT).

**Why add a field for one record rather than drop the tables.** Dropping them
would leave step 11 citing "Table 4, ... Table 5 and ... Table 6" while the
dataset contained no such tables — a dangling reference that, unlike the 130
unresolvable predecessor references, would be *ours* rather than CMS's. All 57
rows and 7 titles were verified verbatim against the source before writing.

## X6 — structural checks in the validator

The fidelity layer passed every defect above, because it asks whether text
appears somewhere in the cited page range — and leaked table rows, figure labels
and section headings all do. The defect was that they sat in the wrong field,
which is a structural question. `check_step_structure()` now rejects:

- an entry opening with a number above 60 (a citation split at its period)
- step numbers that neither continue the sequence nor restart at 1
- a restart at 1 with no preceding scenario heading
- `Table N:` content or figure-legend fragments inside a step

- a scenario heading that is also still absorbed into the tail of the step above
- a scenario-heading count other than the expected 20, in either direction

`FM_Manage_Estate_Recovery_BPT` is held as an explicit `STEP_START_EXCEPTIONS`
entry, being the only record that legitimately does not begin at step 1. It is
keyed by `process_id` rather than filename, so a version bump cannot silently drop
the exemption.

`reference_tables` is validated for shape, `table_number` ordering,
`page_reference` within the record's page range, and that every table a step cites
exists — that last check runs whether or not the record has the field, since the
state it guards against is a record that cites a table and carries none.

The table cells are also under fidelity attestation, and separately under a
**pairing** check. Attestation alone cannot catch a swapped `authority` and
`eligibility_group`, because both strings still occur in the source. The pairing
check uses reading order instead: in the PDF a row's left cell is followed
immediately by its right cell, so `"<authority> <eligibility_group>"` is
contiguous in the extracted text for a correct row and is not for a swapped one.
Verified contiguous for all 57 rows.

Each check was confirmed to fire by injecting the corresponding defect into a
scratch copy of the dataset — a green run alone does not demonstrate that a check
works. The pairing check was validated against a deliberate Aged/Disabled swap and
a rotated citation, both of which the fidelity layer passed.

**What this still does not catch.** A title truncated to a prefix of the real one
passes both attestation and pairing, since every token is present and no pairing
is disturbed. Titles are few and short, so this is a documented limit rather than
an open defect.

## Round 2 status

| Item | Status |
|---|---|
| D19 EE_Determine step array (21 → 18 entries) | done — all entries word-attested against source; 3,126 characters restored |
| D20 dropped scenario headings (11 headings, 6 records) | done — all verbatim in source; 5 absorbed copies also stripped after review |
| D21 invented `---` decoration (2 records) | done |
| D22 dropped word in EE_Disenroll_Provider | done |
| D23 `reference_tables` (7 tables, 57 rows) | done — every cell attested and pairing-checked |
| X6 structural validator checks | done — each check proven to fire |
| Review round | 5 independent reviews; 2 blocking findings (absorbed headings, bisect order) and 5 lesser ones, all addressed |
| CMS defects documented rather than corrected | done — [SOURCE_DEFECTS.md](SOURCE_DEFECTS.md) |
| Full re-validation | done — 0 errors, 57 warnings (unchanged baseline) |
| Regression | done — 152 files, 0 unpaired, 76 capabilities, archive validator exit 0, no format drift |
