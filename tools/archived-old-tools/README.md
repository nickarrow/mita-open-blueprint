> **ARCHIVED.** This described the tooling as it stood during the 2014
> migration. For the current tools see [../README.md](../README.md).
> Paths and commands below may be stale.

# MITA Tools

This directory contains tools for extracting and validating MITA JSON data files.

## Available Tools

### extract_bpt_2014.py

Extracts BPT (Business Process Table) data from the May 2014 MITA PDFs.

**Usage:**

```bash
# Extract a single business area
.venv/bin/python3 tools/extract_bpt_2014.py --area "Care Management"

# Extract with process diagrams
.venv/bin/python3 tools/extract_bpt_2014.py --area "Care Management" --with-images

# Extract all business areas
.venv/bin/python3 tools/extract_bpt_2014.py --all

# Force overwrite existing files
.venv/bin/python3 tools/extract_bpt_2014.py --all --force
```

**Note:** By default, existing files are NOT overwritten. Use `--force` to overwrite.

### extract_bcm_2014.py.archived

**⚠️ ARCHIVED - DO NOT USE**

The BCM extraction script has been archived because the BCM JSON files in `data/bcm/` were **manually verified and corrected** against the source PDFs. The automated extraction had systematic issues that required manual fixes.

The file is preserved for reference only. Running it will display an error message and exit.

### validate_2014.py

Validates all extracted JSON files for structural correctness and content quality.

**Usage:**

```bash
.venv/bin/python3 tools/validate_2014.py
.venv/bin/python3 tools/validate_2014.py --verbose  # Show detailed warnings
```

### comprehensive_validation.py

Comprehensive validation script that checks all JSON files for structural correctness and content quality.

**Usage:**

```bash
# Validate all files
python comprehensive_validation.py

# Or with virtual environment
source ../.venv/bin/activate && python comprehensive_validation.py
```

**What it validates:**

1. **File Completeness**
   - All expected files present
   - Correct directory structure
   - No missing files

2. **Structural Validation**
   - Valid JSON syntax
   - Required fields present
   - Correct data types
   - Proper nesting

3. **Content Validation**
   - BCM: Questions have 5 levels
   - BCM: Questions are complete sentences
   - BPT: Process steps present
   - BPT: Major sections populated
   - Metadata fields complete

4. **Quality Indicators**
   - Question length (BCM)
   - Level description length (BCM)
   - Process step count (BPT)
   - Description length (BPT)

**Expected Output:**

```
✓ VALIDATION PASSED - All files are structurally correct and match source PDFs

Summary:
- Total files validated: 144
- BCM files: 72
- BPT files: 72
- Pass rate: 100%
```

## Validation Criteria

### BCM Files Must Have:

- ✓ document_type = "BCM"
- ✓ maturity_model.capability_questions array
- ✓ Each question has 5 levels (level_1 through level_5)
- ✓ Questions are complete sentences (>15 characters)
- ✓ Level descriptions have substantial content (>20 characters)
- ✓ Metadata fields populated

### BPT Files Must Have:

- ✓ document_type = "BPT"
- ✓ process_details object
- ✓ process_steps array with content
- ✓ trigger_events array
- ✓ results array
- ✓ Description text (>100 characters)
- ✓ Metadata fields populated

## Running Validation

### Prerequisites

```bash
# Ensure you have Python 3.x installed
python --version

# Install required packages (if not already installed)
pip install pypdf
```

### Validate After Changes

Always run validation after:
- Making corrections to JSON files
- Adding new files
- Updating existing files
- Converting new PDFs

### Continuous Validation

Consider running validation:
- Before committing changes
- As part of CI/CD pipeline
- After pulling updates
- Periodically to ensure data integrity

## Interpreting Results

### Success

```
✓ VALIDATION PASSED
```

All files are valid and ready for use.

### Failure

```
✗ VALIDATION FAILED

Issues found:
- File: data/bcm/care_management/CM_Example_BCM_v3.0.json
  Problem: Missing level_5 in question 3
```

Fix the reported issues and re-run validation.

## Custom Validation

You can create custom validation scripts for specific needs:

```python
import json
from pathlib import Path

def validate_custom_rule(json_file):
    with open(json_file) as f:
        data = json.load(f)
    
    # Your custom validation logic
    if data['document_type'] == 'BCM':
        # Check something specific
        pass
    
    return True

# Run on all files
for json_file in Path('../data').rglob('*.json'):
    validate_custom_rule(json_file)
```

## Contributing

If you develop useful validation tools:
1. Add them to this directory
2. Document usage in this README
3. Submit a Pull Request

## Troubleshooting

### "File not found" errors

Ensure you're running from the `tools/` directory:

```bash
cd tools
python comprehensive_validation.py
```

### "Module not found" errors

Install required dependencies:

```bash
pip install pypdf
```

### Validation fails on valid files

1. Check if source PDF matches JSON content
2. Review validation criteria
3. Open a GitHub Issue if validation is incorrect

## Future Enhancements

Potential additions:
- Schema validation using JSON Schema
- Cross-reference validation (predecessor/successor links)
- Performance benchmarking
- Automated PDF comparison

## Questions?

- Check [../docs/DATA_STRUCTURE.md](../../docs/DATA_STRUCTURE.md) for schema details
- See [../docs/CONVERSION_METHODOLOGY.md](../../docs/CONVERSION_METHODOLOGY.md) for conversion process
- Open a GitHub Issue for validation questions
