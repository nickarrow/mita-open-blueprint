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

See [docs/DATA_STRUCTURE.md](docs/DATA_STRUCTURE.md) for complete schema documentation.

## Documentation

- **[Data Structure Guide](docs/DATA_STRUCTURE.md)** - Complete field definitions and schemas
- **[Conversion Methodology](docs/CONVERSION_METHODOLOGY.md)** - How PDFs were converted to JSON
- **[Usage Examples](docs/EXAMPLES.md)** - Common queries and usage patterns
- **[2014 Migration Project](docs/2014_MIGRATION_PROJECT.md)** - Details of the 2012→2014 migration
- **[Source PDFs](source-pdfs/)** - Original CMS MITA PDF documents
- **[Archived 2012 Data](data-archived-2012/)** - Previous MITA v3.0 (February 2012) data

## Validation

All JSON files have been validated for:
- Structural correctness
- Content completeness
- Accuracy against source PDFs

To validate the data yourself:

```bash
cd tools
python validate_2014.py           # Quick validation for 2014 schema
python comprehensive_validation.py # Full validation suite
```

A visual QA tool is also available at `tools/viewer.html` for browsing the JSON data.

See [tools/README.md](tools/README.md) for more information.

## Statistics

- **Total Files**: 152 (76 BCM + 76 BPT)
- **BCM Questions**: 815 capability questions
- **BCM Maturity Levels**: 4,075 level descriptions
- **BPT Process Steps**: 822 documented steps
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

### Version 2.0.0 (January 2026)
- **Major update**: Migrated from MITA v3.0 (February 2012) to MITA v3.0 Update (May 2014)
- Increased from 144 to 152 files (72 → 76 BCM, 72 → 76 BPT)
- Added 4 new Member-related processes in Eligibility & Enrollment Management:
  - Determine Member Eligibility
  - Enroll Member
  - Disenroll Member
  - Inquire Member Eligibility
- Enhanced trigger events with environment-based and interaction-based categorization
- Added diagrams field to BPT schema (populated for Eligibility & Enrollment processes)
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

**Last Updated**: January 2026  
**MITA Version**: 3.0 Update (May 2014)