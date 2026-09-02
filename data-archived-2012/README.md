# ARCHIVED — MITA v3.0, February 2012

> **This is not the current dataset.** It is retained for historical reference
> only. The current data is in [`../data/`](../data/), converted from the
> **May 2014 Update**.
>
> | | This archive (Feb 2012) | Current (`../data/`, May 2014) |
> |---|---|---|
> | Files | 144 (72 BCM + 72 BPT) | 152 (76 BCM + 76 BPT) |
> | Eligibility & Enrollment | 4 processes, provider only | 8 processes, provider + member |
> | `trigger_events` | flat array | object with `environment_based` and `interaction_based` |
> | Extra top-level fields | `date`, `page_count` | `process_id`, `version_date` |
> | `diagrams` | absent | present |
> | Machine-verified against source PDFs | no | yes, every transcribed field |
>
> The 2014 release also added `process_id`, the join key for pairing a BCM with
> its BPT. This archive has no equivalent.
>
> The paths in the examples below are relative to this archive directory, not to
> `../data/`. To validate this archive against the 2012 schema:
>
> ```bash
> .venv/bin/python tools/archived-old-tools/comprehensive_validation.py
> ```
>
> Note that these records cite their source PDFs by their original vault paths,
> which this repository does not ship; the 2012 PDFs are under
> `../source-pdfs/archived-2012-versions/` with different names.

## Structure

```
data-archived-2012/
├── bcm/  - Business Capability Models (72 files)
│   ├── business_relationship_management/  (4 files)
│   ├── care_management/                   (9 files)
│   ├── contractor_management/             (9 files)
│   ├── eligibility_and_enrollment_management/ (4 files)
│   ├── financial_management/              (19 files)
│   ├── operations_management/             (9 files)
│   ├── performance_management/            (5 files)
│   ├── plan_management/                   (8 files)
│   └── provider_management/               (5 files)
└── bpt/  - Business Process Templates (72 files)
    ├── business_relationship_management/  (4 files)
    ├── care_management/                   (9 files)
    ├── contractor_management/             (9 files)
    ├── eligibility_and_enrollment_management/ (4 files)
    ├── financial_management/              (19 files)
    ├── operations_management/             (9 files)
    ├── performance_management/            (5 files)
    ├── plan_management/                   (8 files)
    └── provider_management/               (5 files)
```

## File Naming Convention

Files follow the original CMS naming convention:

- **Format**: `[ProcessCode]_[Process_Name]_[BCM|BPT]_v3.0.json`
- **Example**: `CM_Establish_Case_BCM_v3.0.json`

### Process Codes

- **BR** - Business Relationship Management
- **CM** - Care Management
- **CO** - Contractor Management
- **EE** - Eligibility and Enrollment Management
- **FM** - Financial Management
- **MM** - Member Management
- **OM** - Operations Management
- **PE** - Performance Management
- **PL** - Plan Management
- **PM** - Provider Management

## Business Areas

### Business Relationship Management (4 BCM + 4 BPT)
Processes for establishing and managing relationships with business partners, trading partners, and other agencies.

### Care Management (9 BCM + 9 BPT)
Processes for case management, treatment authorization, population health, and care coordination.

### Contractor Management (9 BCM + 9 BPT)
Processes for managing contracts with vendors, MCOs, and other contractors.

### Eligibility and Enrollment Management (4 BCM + 4 BPT)
Processes for determining and managing provider eligibility and enrollment.

### Financial Management (19 BCM + 19 BPT)
Processes for budgeting, payments, claims processing, accounting, and financial reporting.

### Member Management (0 BCM + 0 BPT)
Note: Member Management processes were not included in the source MITA v3.0 vault.

### Operations Management (9 BCM + 9 BPT)
Processes for claims processing, encounters, payments, and operational data management.

### Performance Management (5 BCM + 5 BPT)
Processes for compliance monitoring, fraud detection, and performance reporting.

### Plan Management (8 BCM + 8 BPT)
Processes for managing state plans, policies, benefits, and rates.

### Provider Management (5 BCM + 5 BPT)
Processes for provider communication, grievances, outreach, and information management.

## Data Quality

These files were validated for structural correctness against the 2012 schema.

They were **not** subjected to the source-PDF fidelity verification introduced for
the 2014 dataset in September 2026. That work found a range of extraction defects
in the 2014 data — merged and dropped capability questions, page-header text
spliced into content, lost sub-steps, corrupted bullet hierarchies — and this
archive was produced by the same class of tooling, so it very likely carries
comparable defects. Treat it as a historical snapshot, not as verified data.

See [../docs/REMEDIATION_PLAN.md](../docs/REMEDIATION_PLAN.md) for what was found
in the 2014 dataset.

See [../tools/README.md](../tools/README.md) for validation details.

## Usage

### Load All Files in a Business Area

```python
import json
import os
from pathlib import Path

def load_business_area(area_name, doc_type='bcm'):
    """Load all BCM or BPT files for a business area."""
    area_path = Path(f'data-archived-2012/{doc_type}/{area_name}')
    files = {}
    
    for json_file in area_path.glob('*.json'):
        with open(json_file) as f:
            files[json_file.stem] = json.load(f)
    
    return files

# Example: Load all Care Management BCMs
care_bcms = load_business_area('care_management', 'bcm')
print(f"Loaded {len(care_bcms)} Care Management BCM files")
```

### Find Files by Process Code

```python
import json
from pathlib import Path

def find_by_process_code(process_code, doc_type='bcm'):
    """Find all files matching a process code."""
    data_path = Path(f'data-archived-2012/{doc_type}')
    matching_files = []
    
    for json_file in data_path.rglob(f'{process_code}_*.json'):
        with open(json_file) as f:
            matching_files.append({
                'path': str(json_file),
                'data': json.load(f)
            })
    
    return matching_files

# Example: Find all Care Management (CM) processes
cm_processes = find_by_process_code('CM', 'bcm')
for process in cm_processes:
    print(process['data']['process_name'])
```

### Compare BCM and BPT for Same Process

```python
import json

def compare_bcm_bpt(process_file_name):
    """Load both BCM and BPT for the same process."""
    # Remove _BCM or _BPT suffix to get base name
    base_name = process_file_name.replace('_BCM_v3.0', '').replace('_BPT_v3.0', '')
    
    # Determine business area from file structure
    # This is simplified - you'd need to search for the actual file
    with open(f'data-archived-2012/bcm/[area]/{base_name}_BCM_v3.0.json') as f:
        bcm = json.load(f)
    
    with open(f'data-archived-2012/bpt/[area]/{base_name}_BPT_v3.0.json') as f:
        bpt = json.load(f)
    
    return {
        'bcm': bcm,
        'bpt': bpt,
        'process_name': bcm['process_name']
    }
```

## Statistics

- **Total Files**: 144
- **BCM Files**: 72
- **BPT Files**: 72
- **Business Areas**: 10 (9 with data)
- **Total Questions (BCM)**: 729
- **Total Maturity Levels (BCM)**: 3,645
- **Total Process Steps (BPT)**: 693

## Schema Reference

See [../docs/DATA_STRUCTURE.md](../docs/DATA_STRUCTURE.md) for complete schema documentation.

## Source Attribution

All data derived from CMS MITA Framework v3.0 (February 2012), superseded by the May 2014 Update.

Original PDFs available in [../source-pdfs/](../source-pdfs/).
