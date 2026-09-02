# MITA Open Blueprint - A BCM & BPT Data Repository

A comprehensive, machine-readable dataset of CMS MITA (Medicaid Information Technology Architecture) Business Process Templates (BPT) and Business Capability Models (BCM) in JSON format.

## Overview

This repository contains all 152 MITA v3.0 documents (May 2014 Update) converted from PDF to structured JSON format:
- **76 BPT files** - Business Process Templates with detailed process steps and workflows
- **76 BCM files** - Business Capability Maturity models with 5-level maturity assessments

The data covers 9 MITA business areas:
- Business Relationship Management
- Care Management
- Contractor Management
- Eligibility and Enrollment Management
- Financial Management
- Operations Management
- Performance Management
- Plan Management
- Provider Management

> **Note**: Member Management is defined in the MITA framework but has no published BCM/BPT documents.

## Quick Start

### Use Data Directly from GitHub (Recommended)

You can fetch JSON files directly from GitHub without cloning the repository:

```python
import json
import urllib.request

# Base URL for raw GitHub content
BASE_URL = "https://raw.githubusercontent.com/nickarrow/mita-open-blueprint/main/data"

# Load a BCM file directly from GitHub
bcm_url = f"{BASE_URL}/bcm/care_management/CM_Establish_Case_BCM_v3.0.json"
with urllib.request.urlopen(bcm_url) as response:
    bcm = json.loads(response.read())

# Access maturity questions
for question in bcm['maturity_model']['capability_questions']:
    print(f"Question: {question['question']}")
    print(f"Level 1: {question['levels']['level_1']}")
```

```javascript
// JavaScript/Node.js example
const BASE_URL = "https://raw.githubusercontent.com/nickarrow/mita-open-blueprint/main/data";

// Load a BPT file directly from GitHub
const bptUrl = `${BASE_URL}/bpt/care_management/CM_Establish_Case_BPT_v3.0.json`;
const response = await fetch(bptUrl);
const bpt = await response.json();

// Access process steps
bpt.process_details.process_steps.forEach(step => {
    console.log(`Step: ${step}`);
});
```

### Browse the Data

All JSON files are organized in the `data/` directory:
```
data/
├── bcm/  - Business Capability Models
│   ├── business_relationship_management/
│   ├── care_management/
│   ├── contractor_management/
│   └── ...
└── bpt/  - Business Process Templates
    ├── business_relationship_management/
    ├── care_management/
    ├── contractor_management/
    └── ...
```

### Clone for Local Development (Optional)

If you prefer to work with local files:

```bash
git clone https://github.com/nickarrow/mita-open-blueprint.git
cd mita-open-blueprint
```

```python
import json

# Load from local file
with open('data/bcm/care_management/CM_Establish_Case_BCM_v3.0.json') as f:
    bcm = json.load(f)
```

## Use Cases

This dataset enables:

- **Maturity Assessment Tools** - Build applications that help state Medicaid agencies assess their MITA maturity levels
- **Process Documentation** - Generate human-readable process documentation from structured data
- **Workflow Automation** - Map MITA processes to automated workflows in your systems
- **Compliance Tracking** - Track implementation of MITA processes and capabilities
- **Research & Analysis** - Analyze patterns across Medicaid business processes
- **Training Materials** - Create interactive training tools for Medicaid staff
- **System Design** - Use as reference architecture for Medicaid system implementations

## Data Structure


### BPT (Business Process Template) Format

BPT files contain detailed process information:

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
    "description": "Full process description",
    "trigger_events": {
      "environment_based": ["Periodic review is due"],
      "interaction_based": ["Receive enrollment from Enroll Member process"]
    },
    "results": ["Result 1", "Result 2"],
    "process_steps": ["1. START: First step", "2. Second step"],
    "diagrams": [],
    "predecessor_processes": ["Prior Process"],
    "successor_processes": ["Next Process"],
    "shared_data": ["Data Source 1"],
    "constraints": "Process constraints",
    "failures": ["Failure condition 1"],
    "performance_measures": ["Measure 1"]
  },
  "metadata": {
    "source_file": "source-pdfs/may-2014-update/bpt/Care Management/Care Management BPT.pdf",
    "source_page_range": "1-4",
    "extracted_date": "2026-01-12"
  }
}
```

### BCM (Business Capability Model) Format

BCM files contain maturity assessment questions with 5 levels of capability:

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
        "question": "Question text?",
        "levels": {
          "level_1": "Basic capability description",
          "level_2": "Improved capability description",
          "level_3": "Enhanced capability description",
          "level_4": "Advanced capability description",
          "level_5": "Optimized capability description"
        }
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

### Pairing a BCM with its BPT

All three of these work, and all three give 76 pairs:

- **`process_id`** — recommended. A stable identifier, identical across a pair.
- **`process_name`** — identical across a pair.
- **The filename stem** — `CM_Establish_Case_BCM_v3.0.json` and
  `CM_Establish_Case_BPT_v3.0.json` share the code `CM_Establish_Case`.

Two processes are named differently in CMS's own two appendices. Appendix C (the
BPT source) and the framework's Business Architecture index, which assigns the
official process codes, both use one spelling; Appendix D (the BCM source) uses
another. The dataset follows the framework index so that pairing works, and
records what each BCM document actually published in
`metadata.source_process_name`:

| Process | Used throughout | Appendix D publishes |
|---|---|---|
| CM06 | Manage Treatment Plan and Outcomes | Manage Treatment Plan**s** and Outcomes |
| PL07 | **Manage** Reference Information | **Maintain** Reference Information |

See [docs/DATA_STRUCTURE.md](docs/DATA_STRUCTURE.md) for complete schema documentation.

## Documentation

- **[Data Structure Guide](docs/DATA_STRUCTURE.md)** - Complete field definitions and schemas
- **[Conversion Methodology](docs/CONVERSION_METHODOLOGY.md)** - How PDFs were converted, and the transcription decisions behind it
- **[Usage Examples](docs/EXAMPLES.md)** - Common queries and usage patterns
- **[Tools](tools/README.md)** - Validation and inspection utilities
- **[Remediation Plan](docs/REMEDIATION_PLAN.md)** - Defects found against the source PDFs and how each was repaired
- **[2014 Migration Project](docs/archived-old-docs/2014_MIGRATION_PROJECT.md)** - Historical record of the 2012→2014 migration
- **[Source PDFs](source-pdfs/)** - Original CMS MITA PDF documents
- **[Archived 2012 Data](data-archived-2012/)** - Previous MITA v3.0 (February 2012) data

## Validation

Every record is checked against the source PDF it came from, scoped to the pages
that record cites.

```bash
python3 -m venv .venv
.venv/bin/pip install -r tools/requirements.txt

.venv/bin/python tools/verify_against_source.py                    # full check
.venv/bin/python tools/verify_against_source.py --structural-only  # no dependencies
.venv/bin/python tools/verify_against_source.py --area care_management
```

What the checks establish, so you can calibrate how much to trust the data:

**Established**

- Every word of every transcribed field occurs on the pages that record cites.
  This is what catches a word truncated at a page break — the defect class this
  dataset actually suffered from.
- Exact wording and word order for capability questions and notes.
- Structure, naming, `process_id` uniqueness and pairing, page-range provenance,
  and the known extraction artifacts (bullet debris, hyphen splits, page
  furniture, cross-process bleed-over).

**Not established**

- **Where content sits.** Word-level attestation does not prove placement. Two
  maturity levels swapped between ratings, a reordered `process_steps` array, or
  `results` and `failures` exchanged would all pass. Maturity level and BPT prose
  wrap across many lines of a six-column table that the PDF text layer does not
  reproduce in reading order, which is why they are verified at the word level
  and not as sequences.
- **Missing content**, except where a record lacks one of the standard capability
  quality categories, which is flagged. A deleted question or a truncation that
  happens to end on a content word with punctuation is not detected.
- **Text borrowed from an adjacent process in the same PDF** is only sometimes
  caught. BCM level text is heavily boilerplate across the processes packed into
  one appendix file, so word-level attestation has limited power there.

The in-code docstrings in `tools/verify_against_source.py` state per-check scope.
Prefer them over any summary if the two ever disagree.

A clean run reports `PASSED - 0 errors` with 57 warnings. The warnings flag
capability questions whose source table cell wraps across a page break, so the
text is correctly reassembled from two fragments of the PDF; the tool prints the
fragments so you can judge each one.

For side-by-side BPT and BCM inspection in a browser:

```bash
python3 -m http.server 8000
# open http://localhost:8000/tools/viewer.html
```

See [tools/README.md](tools/README.md) for what each check does.

## Statistics

- **Total Files**: 152 (76 BCM + 76 BPT)
- **BCM Questions**: 837 capability questions
- **BCM Maturity Levels**: 4,185 level descriptions
- **BPT Process Steps**: 826 documented steps
- **Business Areas**: 9 complete domains

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- How to report data quality issues
- Guidelines for submitting corrections
- Process for adding new MITA versions

## Attribution & Disclaimer

This dataset is derived from the **CMS Medicaid Information Technology Architecture (MITA) Framework Version 3.0 (May 2014 Update)**, published by the Centers for Medicare & Medicaid Services (CMS).

**Original Source**: [CMS MITA Framework](https://www.medicaid.gov/medicaid/data-systems/medicaid-information-technology-architecture/medicaid-information-technology-architecture-framework)

**Disclaimer**: This is an unofficial conversion of CMS MITA documents to JSON format. While every effort has been made to ensure accuracy, users should refer to the [official CMS MITA documentation](https://www.medicaid.gov/medicaid/data-systems/medicaid-information-technology-architecture/medicaid-information-technology-architecture-framework) for authoritative information. This repository is not affiliated with, endorsed by, or approved by CMS.

The MITA content itself is a work of the U.S. Government and is in the public domain under 17 U.S.C. § 105. You do not need permission from this repository to use it.

### How to Cite

The MIT License asks only that you retain the copyright notice. If you'd like to credit the dataset more visibly, it's appreciated but not required:

> MITA Open Blueprint by Nick Aretakis — https://github.com/nickarrow/mita-open-blueprint

Structured citation metadata is in [CITATION.cff](CITATION.cff).

## Future Enhancements

Potential additions we're considering:
- API-style documentation with detailed field descriptions
- Additional code examples in multiple languages
- Cross-reference mapping between related processes
- MITA version comparison tools

Suggestions welcome via [GitHub Issues](../../issues)!

## License

Everything in this repository — the dataset, the tooling, and the documentation — is licensed under the [MIT License](LICENSE).

**What this means in practice**: use it for anything, including commercial products. No copyleft, no share-alike, no restrictions on how you license your own work. Just keep the copyright notice.

**Two clarifications** (see [NOTICE](NOTICE) for detail):

- The underlying MITA content is a work of the U.S. Government, in the public domain under 17 U.S.C. § 105. The MIT License here covers what was added — the conversion to structured JSON, the schema, the extraction metadata, and the tooling. It asserts nothing over the CMS content itself, which you're free to use regardless.
- For the avoidance of doubt, "the Software" in the MIT License includes the JSON dataset, not just the code.

## Changelog

### Version 2.1.1 (September 2026)

**Breaking for consumers that fetch these two files by URL.** Two BCM files were
renamed so that every capability's BCM and BPT halves share one code:

| Was | Now |
|---|---|
| `CM_Manage_Treatment_Plans_and_Outcomes_BCM_v3.0.json` | `CM_Manage_Treatment_Plan_and_Outcomes_BCM_v3.0.json` |
| `PL_Maintain_Reference_Information_BCM_v3.0.json` | `PL_Manage_Reference_Information_BCM_v3.0.json` |

Their `process_name` was changed to match. CMS names these two processes
differently in its own two appendices; Appendix C and the Business Architecture
index (which assigns the codes CM06 and PL07) agree on the names now used, so
Appendix D is the outlier. The as-published Appendix D spelling is preserved in
the new optional `metadata.source_process_name` field, so nothing is lost and
each record still traces to its source.

Why it matters: a consumer pairing the two halves by filename or by
`process_name` previously built 74 capabilities from 152 files, silently dropping
these two entirely. Pairing now yields 76 by filename, by `process_name`, or by
`process_id`.

### Version 2.1.0 (September 2026)

Data-quality release. Every record was re-verified against the source CMS PDFs,
and the defects found were repaired. Full detail, with per-defect evidence and
page references, is in [docs/REMEDIATION_PLAN.md](docs/REMEDIATION_PLAN.md).

**Recovered content** (previously missing from the dataset):

- `CO_Perform_Contractor_Outreach_BCM` — an entire capability question and its
  five maturity levels ("Effort to Perform; Efficiency", source page 25)
- `PE_Prepare_REOMB_BCM` — the sampling-algorithm question, which had been
  merged into the preceding question with their level text concatenated
- `PM_Perform_Provider_Outreach_BCM` — the efficiency question, likewise merged,
  with its level descriptions truncated mid-sentence
- `EE_Determine_Provider_Eligibility_BPT` — moderate-risk and high-risk provider
  screening sub-steps, including unannounced site visits, criminal background
  checks and fingerprinting
- `EE_Enroll_Provider_BPT` — a word dropped across a page break (`follow-up`)

**Corrected content**:

- 84 maturity-level descriptions across 25 files had the PDF running header's
  process name spliced into them
- 274 hyphenation artifacts rejoined (`state- specific` → `state-specific`),
  leaving the 4 authored suspended hyphens intact
- `shared_data` rebuilt in 4 BPT files where bullet markers had been welded onto
  the wrong entries, destroying the parent/child structure
- 2 capability questions had a duplicated tail
- 1 question was filed under the wrong capability category
- `EE_Enroll_Provider_BCM` had absorbed a question belonging to Disenroll Provider
- 4 BPT files had an `Alternate Path:` block welded onto the preceding step
- `FM_Manage_Estate_Recovery_BCM` had a CMS note concatenated into a question

**Added**:

- `process_id` on every record — a stable join key, so a BCM pairs with its BPT
  even where CMS spells the process differently in the two appendices
- `tools/verify_against_source.py` — validates structure *and* compares text
  against the source PDFs
- `tools/extract_bpt_field.py` — recovers list hierarchy from the source tables

**Statistics** changed accordingly: 837 capability questions (was 835 in the
data, 815 as reported), 4,185 level descriptions, 826 process steps.

No files were renamed and no fields were removed, so existing consumers continue
to work.

### Version 2.0.0 (January 2026)
- **Major update**: Migrated from MITA v3.0 (February 2012) to MITA v3.0 Update (May 2014)
- Increased from 144 to 152 files (72 → 76 BCM, 72 → 76 BPT)
- Added 4 new Member-related processes in Eligibility & Enrollment Management:
  - Determine Member Eligibility
  - Enroll Member
  - Disenroll Member
  - Inquire Member Eligibility
- Enhanced trigger events with environment-based and interaction-based categorization
- Added diagrams field to BPT schema (populated for one process, Determine Member Eligibility)
- Archived 2012 data to `data-archived-2012/` for historical reference
- New validation tools: `validate_2014.py`, `viewer.html`
- Updated extraction tooling for 2014 PDF structure

### Version 1.0.0 (December 2025)
- Initial release with all MITA v3.0 BCM and BPT documents (February 2012)
- 144 files converted and validated
- Complete documentation and validation tools

## Contact & Support

- **Issues**: Report bugs or data quality issues via [GitHub Issues](../../issues)
- **Discussions**: Ask questions or share ideas in [GitHub Discussions](../../discussions)
- **Pull Requests**: Submit corrections or enhancements via [Pull Requests](../../pulls)

---

**Last Updated**: September 2026  
**MITA Version**: 3.0 Update (May 2014)