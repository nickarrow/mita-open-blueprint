# MITA Data Structure Reference

This document provides detailed schema definitions for BCM and BPT JSON files.

## Overview

All JSON files follow consistent schemas based on document type:
- **BPT** (Business Process Template) - Detailed process workflows and steps
- **BCM** (Business Capability Model) - Maturity assessment questions with 5 levels

## Common Fields

Both BPT and BCM files share these top-level fields:

```json
{
  "document_type": "BPT" | "BCM",
  "version": "3.0",
  "version_date": "May 2014",
  "business_area": "string",
  "sub_category": "string",
  "process_name": "string",
  "process_code": "string",
  "process_id": "string",
  "metadata": {
    "source_file": "string",
    "source_page_range": "string",
    "extracted_date": "YYYY-MM-DD",
    "manually_corrected": true
  }
}
```

### Field Definitions

- **document_type**: Either "BPT" or "BCM"
- **version**: MITA version (currently "3.0")
- **version_date**: Publication date from source document (e.g., "May 2014")
- **business_area**: High-level business domain
- **sub_category**: Process subcategory from source document
- **process_name**: Specific process being described, **exactly as its own source
  document names it**. See the warning below before using this as a key.
- **process_code**: Two-letter abbreviation (BR, CM, CO, EE, FM, OM, PE, PL, PM)
- **process_id**: Canonical, stable identifier (e.g. `CM_ESTABLISH_CASE`).
  **Identical for a BCM/BPT pair. This is the join key.** 76 distinct values, each
  with exactly one BCM and one BPT.
  **Read this field; do not derive it.** It usually equals the process code plus
  the upper-snake-case process name, but not always: for the two processes CMS
  spells differently across the appendices the id follows the BPT spelling, so
  computing it from a BCM's `process_name` reproduces the exact bug the field
  exists to prevent.
- **metadata.source_file**: Relative path to source PDF
- **metadata.source_page_range**: Page range in source PDF (e.g., "1-4")
- **metadata.extracted_date**: Date of JSON extraction
- **metadata.source_process_name** (string, optional): Present only where CMS
  names a process differently in the appendix this record came from than in the
  framework's Business Architecture index. Records the name exactly as this
  record's own source document publishes it, while `process_name` follows the
  index so that a BCM pairs with its BPT. Currently on 2 records.
- **metadata.manually_corrected** (boolean, optional): Present on records whose
  content was corrected by hand against the source because automated extraction
  could not reproduce the table. Currently on
  `FM_Manage_Estate_Recovery_BCM` and `FM_Prepare_Member_Premium_Invoice_BCM`.

### Pairing a BCM with its BPT

`process_id`, `process_name` and the filename stem all pair correctly and all
give 76 pairs. `process_id` is recommended because it is insensitive to naming
and punctuation.

Two processes are named inconsistently by CMS itself. Appendix C (the BPT source)
and the Business Architecture index — which assigns the official process codes —
use one spelling; Appendix D (the BCM source) uses another:

| Code | Used throughout this dataset | Appendix D publishes |
|---|---|---|
| CM06 | Manage Treatment Plan and Outcomes | Manage Treatment Plan**s** and Outcomes |
| PL07 | **Manage** Reference Information | **Maintain** Reference Information |

`process_name` and the filename follow the framework index so the two halves
pair. The Appendix D spelling is retained in `metadata.source_process_name` on
those two records, and the verification tooling checks provenance against that
field, so fidelity to the source document is preserved.

### Text conventions

**Dashes are normalised; quotes are not.** The source PDFs mix `U+002D`,
`U+2010` hyphen, `U+2013` en dash and `U+2014` em dash. All appear as `U+002D`
in the JSON so consumers can match on one character. Curly apostrophes and
quotation marks (`U+2018`–`U+201D`) are preserved as published. The asymmetry is
intentional but worth knowing when comparing against a PDF.

**Nesting inside a string** uses a newline plus indent. Depth is signalled by
increasing indent, but the widths are not uniform across the corpus: one space
(77 occurrences), two spaces (155) and four spaces (39) are all present. Parse on
*relative* indent, not on a fixed width.

```
"3. Determine if CMS requires an APD.\n  a. Produce APD.\n  b. Modify APD as directed."
"Other Agency Information:\n  - Department of Motor Vehicles (DMV)\n  - Veterans Administration (VA)"
"The Establish Case business process ...:\n• Identify target members\n - Home and Community-Based Services (HCBS)"
```

Marker style also varies by field: `description` uses `•` and `✓`,
`process_steps` uses `a.` / `i.`, and `shared_data` uses `-`. Treat the marker as
decoration and the indent as the structure.

**Category naming.** The `category` values use `Cost Effectiveness`, while the
PDFs write `Cost-Effectiveness`. The value in the data is the one to match on.

## BPT Schema

Business Process Template files contain detailed process information.

### Complete BPT Structure

```json
{
  "document_type": "BPT",
  "version": "3.0",
  "version_date": "May 2014",
  "business_area": "Care Management",
  "sub_category": "Case Management",
  "process_name": "Establish Case",
  "process_code": "CM",
  "process_id": "CM_ESTABLISH_CASE",
  "process_details": {
    "description": "Full process description text",
    "trigger_events": {
      "environment_based": [
        "Periodic review to scan for new cases is due."
      ],
      "interaction_based": [
        "Receive enrollment of member from Enroll Member business process."
      ]
    },
    "results": [
      "Expected outcome of the process"
    ],
    "process_steps": [
      "1. START: First step description",
      "2. Second step description"
    ],
    "diagrams": [],
    "shared_data": [
      "Data source or store used"
    ],
    "predecessor_processes": [
      "Process that comes before"
    ],
    "successor_processes": [
      "Process that follows"
    ],
    "constraints": "Process constraints and limitations",
    "failures": [
      "Failure condition"
    ],
    "performance_measures": [
      "Performance metric"
    ]
  },
  "metadata": {
    "source_file": "source-pdfs/may-2014-update/bpt/Care Management/Care Management BPT.pdf",
    "source_page_range": "1-4",
    "extracted_date": "2026-01-12"
  }
}
```

### BPT-Specific Fields

**process_details.description** (string)
- Full text description of the process
- May contain multiple paragraphs
- Often includes notes and additional context

**process_details.trigger_events** (object)
- Events that initiate the process, categorized by type
- Contains two sub-arrays:
  - **environment_based**: Events triggered by schedules, timers, or system conditions
  - **interaction_based**: Events triggered by external inputs, alerts, or other processes
- Either array may be empty if no triggers of that type exist

**process_details.results** (array of strings)
- Expected outcomes when process completes
- Typically 2-10 results
- Examples:
  - "Case established in system"
  - "Member assigned to case manager"

**process_details.process_steps** (array of strings)
- Ordered list of process steps
- Typically 5-20 steps
- Often numbered in the text (e.g., "1. START: Receive request")
- May include sub-steps with lettered items (e.g., "a.", "b.")
- **Step numbers are not unique within a file.** Where the source defines more
  than one scenario for a process, each scenario restarts its numbering at 1.
  This is faithful to the published document; do not treat the step number as a
  key.
- **`go to step N` can cross a scenario boundary.** In
  `EE_Determine_Member_Eligibility`, the alternate scenario's only step says
  "approve Medicaid eligibility and go to step 14. If not, go to step 6" — and
  neither step exists in that scenario. Both resolve against the main scenario.
  CMS wrote it that way, so resolving such a reference means searching the whole
  record rather than the current scenario.
- **Scenario headings share the array.** An element that does not begin with
  `<digits>.` is a scenario heading transcribed verbatim from the source, and it
  labels the steps that follow it — for example `Capitation Payment`,
  `Alternate Path: Suspended Claim`, `Manage FMAP`. Test for
  `^\d+\.` to tell the two apart. 20 headings appear across 12 BPT files;
  `FM_Manage_Fund` has four scenarios in one array.
- One file starts at step 10 rather than 1, because the source does. See
  [SOURCE_DEFECTS.md](SOURCE_DEFECTS.md).

**process_details.reference_tables** (array, optional)
- Numbered lookup tables published alongside the steps, which steps cite by
  number ("Note: See Mandatory MAGI Groups Table 1").
- Present on **one** record only, `EE_Determine_Member_Eligibility_BPT_v3.0.json`
  (7 tables, 57 rows). It is the only record in the corpus whose source pages
  carry numbered tables, so the key is absent everywhere else — treat it as
  optional and ignore it if your consumer does not need it.
- Each entry is an object with:
  - **table_number**: Integer, 1..N in document order
  - **title**: Table title as published (e.g., "Medically Needy Groups")
  - **page_reference**: Page number in the source PDF
  - **rows**: Array of objects, each with **authority** (the statutory or
    regulatory citation, e.g. `42 CFR 435.301`) and **eligibility_group**
    (e.g. `Pregnant Women`)

**process_details.diagrams** (array)
- Process flow diagrams extracted from source PDFs
- Empty (`[]`) in 75 of the 76 BPT files
- Only `EE_Determine_Member_Eligibility_BPT_v3.0.json` has any, with 76 images in
  `data/bpt/eligibility_and_enrollment_management/images/`
- Each entry is an object with:
  - **filename**: Image filename (e.g., "EE_Determine_Member_Eligibility_diagram_2_2.png")
  - **description**: Brief description of the diagram
  - **page_reference**: Page number in source PDF

**process_details.shared_data** (array of strings)
- Data sources, stores, or systems used
- One element per top-level item. Where the source nests sub-items under an
  entry, they are carried inside that element as indented lines rather than as
  separate elements — so an element may span several lines. Four files use this:
  `EE_Determine_Provider_Eligibility`, `EE_Enroll_Provider`,
  `EE_Inquire_Provider_Information` and `FM_Manage_TPL_Recovery`.
- Examples:
  - "Member data store including demographics"
  - "Health Information Exchange (HIE) data store"
  - "Provider data store including provider network information"

**process_details.predecessor_processes** (array of strings)
- Processes that typically occur before this one
- **Free text as published by CMS, not resolvable identifiers.** See the caveat below.

**process_details.successor_processes** (array of strings)
- Processes that typically follow this one
- **Free text as published by CMS, not resolvable identifiers.** See the caveat below.

> **Caveat: these are not a process graph.**
>
> Of 616 predecessor/successor references, 130 do not resolve to any process in
> this dataset. All of them are verbatim in the source PDFs and are preserved as
> published. The unresolvable ones fall into four groups:
>
> - **Member Management processes** — `Send Outbound Transaction` (43),
>   `Receive Inbound Transaction` (37), `Manage Applicant and Member
>   Communication` (27), `Manage Member Information`, `Perform Population and
>   Member Outreach`, `Manage Member Grievance and Appeal`. The framework defines
>   Member Management but CMS never published BPT or BCM documents for it.
> - **CMS name variants** — `Manage Contractor Communications` (the process is
>   `Manage Contractor Communication`), `Manage Accounts Payment Disbursement`
>   (`Manage Accounts Payable Disbursement`), `Manage Program Policy`
>   (`Maintain Program Policy`), `Send Outbound Information`,
>   `Maintain Member Information`.
> - **Prose** — three entries are explanatory `NOTE:` paragraphs that CMS placed
>   in the predecessor cell rather than a process name.
> - **The literal string `None`** — in `PE_Prepare_REOMB_BPT`.
>
> If you are building a dependency graph, resolve these against `process_name`
> case-insensitively, expect misses, and decide deliberately how to handle them.

**process_details.constraints** (string)
- Limitations, requirements, or rules
- May include regulatory requirements
- May include timing constraints

**process_details.failures** (array of strings)
- Conditions that cause process failure
- Error scenarios
- Examples:
  - "Member not eligible for case management"
  - "Required information not available"

**process_details.performance_measures** (array of strings)
- Metrics for measuring process performance
- May contain placeholders (e.g., "within __ days")
- Examples:
  - "Time to establish case = within __ business days"
  - "Accuracy with which rules are applied = __%"

## BCM Schema

Business Capability Model files contain maturity assessment questions.

### Complete BCM Structure

```json
{
  "document_type": "BCM",
  "version": "3.0",
  "version_date": "May 2014",
  "business_area": "Care Management",
  "sub_category": "Case Management",
  "process_name": "Establish Case",
  "process_code": "CM",
  "process_id": "CM_ESTABLISH_CASE",
  "maturity_model": {
    "capability_questions": [
      {
        "category": "Business Capability Descriptions",
        "question": "Is the process primarily manual or automatic?",
        "levels": {
          "level_1": "Description of basic capability",
          "level_2": "Description of improved capability",
          "level_3": "Description of enhanced capability",
          "level_4": "Description of advanced capability",
          "level_5": "Description of optimized capability"
        },
        "note": "Optional explanatory note (not present in all questions)"
      }
    ]
  },
  "metadata": {
    "source_file": "source-pdfs/may-2014-update/bcm/Care Management/Care Management BCM.pdf",
    "source_page_range": "1-7",
    "extracted_date": "2026-01-12"
  }
}
```

### BCM-Specific Fields

**maturity_model.capability_questions** (array)
- Array of capability assessment questions
- 10 to 15 per file (10 in 32 files, 11 in 20, 12 in 19, 13 in 3, 15 in 2)
- Each question has 5 maturity levels

**capability_questions[].category** (string)
- Question category/grouping
- Common categories:
  - "Business Capability Descriptions"
  - "Business Capability Quality: Timeliness of Process"
  - "Business Capability Quality: Data Access and Accuracy"
  - "Business Capability Quality: Cost Effectiveness"
  - "Business Capability Quality: Effort to Perform; Efficiency"
  - "Business Capability Quality: Accuracy of Process Results"
  - "Business Capability Quality: Utility or Value to Stakeholders"

**capability_questions[].question** (string)
- The capability question being assessed
- Usually ends with "?". Two do not: `CO_Perform_Contractor_Outreach` and
  `PM_Perform_Provider_Outreach` both ask `How efficient is the process.` with a
  full stop, as published.
- Examples:
  - "Is the process primarily manual or automatic?"
  - "How timely is this end-to-end process?"
  - "How accurate is the information in the process?"

**capability_questions[].levels** (object)
- Contains 5 maturity level descriptions
- Keys: level_1, level_2, level_3, level_4, level_5
- Each level describes increasing capability maturity

**capability_questions[].note** (string, optional)
- Additional explanatory information for the question
- Not present in all questions
- Found primarily in Eligibility & Enrollment and Operations Management BCMs

### Maturity Level Progression

Levels generally follow this pattern:

- **Level 1**: Manual, basic compliance, state-specific standards
- **Level 2**: Some automation, HIPAA standards, improved over Level 1
- **Level 3**: Significant automation, MITA Framework adoption, intrastate interoperability
- **Level 4**: Advanced automation, interstate/regional interoperability
- **Level 5**: Optimized automation, national/international interoperability

## Process Codes

| Code | Business Area |
|------|---------------|
| BR | Business Relationship Management |
| CM | Care Management |
| CO | Contractor Management |
| EE | Eligibility and Enrollment Management |
| FM | Financial Management |
| OM | Operations Management |
| PE | Performance Management |
| PL | Plan Management |
| PM | Provider Management |

> **Note**: Member Management (MM) is defined in the MITA framework but has no published BCM/BPT documents.

## Data Types

All JSON files use standard JSON data types:

- **string**: Text values
- **array**: Ordered lists
- **object**: Key-value structures
- **boolean**: `metadata.manually_corrected` only
- **number**: `process_details.diagrams[].page_reference` only

## Validation Rules

Valid JSON files must:

1. Be well-formed JSON
2. Include all required top-level fields
3. Have correct document_type ("BCM" or "BPT")
4. Include type-specific content (maturity_model or process_details)
5. Have populated metadata fields
6. Match content from source PDF

## Usage Examples

See [EXAMPLES.md](EXAMPLES.md) for code examples using these schemas.

## Schema Evolution

Future versions may add:
- Additional optional fields
- New process codes
- Extended metadata
- Cross-reference links

Breaking changes will be versioned appropriately.
