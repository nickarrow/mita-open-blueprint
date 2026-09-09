# Defects in the source documents

This dataset transcribes the CMS MITA 3.0 framework (May 2014). Where the source
PDFs contain errors, **this dataset reproduces them**. That is deliberate: the
value of the dataset is that a page reference can be cited back to CMS, and a
reader who follows the citation must find the same text.

The rule the repository applies:

- If the JSON disagrees with the PDF, the extraction is wrong and gets fixed.
- If the JSON agrees with the PDF and the PDF is wrong, the defect is mirrored
  and recorded here.

This file exists so that these are not "found" and silently corrected later, and
so that consumers reporting them can be answered quickly. CMS is not expected to
revise 3.0; work has moved to MITA 4.0.

Everything below has been checked against the cited page and confirmed to be
present in the published document.

---

## FM_Manage_Estate_Recovery_BPT — steps numbered 10-21

**Source:** `bpt/Financial Management/Financial Management BPT.pdf` p.6
(Part I, Appendix C - Page 107)

The Business Process Steps for Manage Estate Recovery are numbered **10 through
21**. There are no steps 1-9, anywhere in the document.

Nothing is missing. Step 10 carries the `START:` label and step 21 carries `END`,
so the process is complete end to end; only the numerals 1-9 go unused.

The cause is visible two pages earlier. The preceding process in the same
document, **Manage TPL Recovery**, ends at step 9 (p.3), and CMS carried the
numbering forward instead of restarting. The process after it, Manage Drug
Rebate, restarts correctly at 1 (p.8), so this is an isolated slip rather than a
document-wide convention. It is the only one of 76 BPT records that does not
begin at step 1.

The validator holds this as an explicit exception
(`STEP_START_EXCEPTIONS` in `tools/verify_against_source.py`); every other record
is required to start at 1.

## EE_Determine_Member_Eligibility_BPT — three typographic errors

**Source:** `bpt/Eligibility and Enrollment Management/Eligibility and Enrollment Management BPT.pdf`
pages 11, 14 and 15

| Published as | Would read | Where |
|---|---|---|
| `eligibile` | eligible | step 14c, p.14 |
| `orHealth` (no space) | or Health | step 14g, p.15 |
| `Medicaid..` (two periods) | Medicaid. | NOTE under step 11g, p.11 |

All three are inside step text that this dataset restored from the source in a
later repair. They are reproduced exactly as published.

## EE_Disenroll_Member_BCM — sentence ends with two periods

**Source:** `bcm/Eligibility and Enrollment Management/Eligibility and Enrollment Management BCM.pdf`

> An individual seeking eligibility for health insurance applies online, via
> phone, via mail, or in person**..**

CMS's own document contains the identical sentence with a single period
elsewhere, so the doubled period is unambiguously a slip rather than a
convention. It is still reproduced as published.

## CM_Manage_Population_Health_Outreach_BPT — repeated word in `failures`

**Source:** `bpt/Care Management/Care Management BPT.pdf`

> **Inter-agency agency** communication or lack of access to information impairs
> ability to...

Unlike the cases above, the correct reading here is a judgment call — "Inter-agency
communication" and "Inter-agency agency communication" are both plausible
intents. Correcting it would mean deciding what CMS meant, which is
interpretation rather than transcription, so the text is left exactly as
published.

---

## Not defects

Two things that look like extraction problems but are faithful:

**Step numbering restarting at 1 mid-array.** Nine BPT records define more than
one scenario, and the source restarts numbering for each. See
[DATA_STRUCTURE.md](DATA_STRUCTURE.md) on `process_steps`.

**A scenario with no `START:` or `END`.** The `Alternate Scenario 1 - Auto
Eligible` scenario in `EE_Determine_Member_Eligibility_BPT` is a single unlabelled
step. CMS publishes it that way (Appendix C p.75), so a completeness check that
expects every scenario to open with `START:` and close with `END` will flag it. The
main scenario in that record does carry both.

**Cross-scenario step references.** That same alternate scenario says "go to step
14" and "go to step 6", neither of which exists within it. Both resolve against the
main scenario. CMS's own wording.

**Unresolvable predecessor and successor references.** 130 references name a
process that does not exist under that name elsewhere in the framework. These are
CMS's cross-references, reproduced as written. See
[REMEDIATION_PLAN.md](REMEDIATION_PLAN.md).

---

## Normalisations this dataset does apply

For completeness, the places where the JSON deliberately does *not* match the
PDF byte for byte. These are presentation-layer choices, applied uniformly, and
they change no words:

- **Dashes** are normalised to ASCII `-` (U+002D). The sources also use U+2013,
  U+2010 and U+2014.
- **Bullet glyphs** in the source are private-use Wingdings characters
  (U+F0B7); list items are carried as `- ` instead.
- **Curly apostrophes and quotation marks** (U+2019, U+201C, U+201D) are
  preserved as published.
- **Page furniture** (running headers, footers, page numbers) is removed.

See [CONVERSION_METHODOLOGY.md](CONVERSION_METHODOLOGY.md) for the full set of
transcription decisions.
