#!/usr/bin/env python3
"""
Structural validation for the ARCHIVED February 2012 dataset.

This checks `data-archived-2012/` against the 2012 schema, which has `date` and
`page_count` top-level fields and a flat `trigger_events` array. It does NOT
understand the current May 2014 schema and must not be used on `data/`.

For the current dataset use:

    .venv/bin/python tools/verify_against_source.py

Historical note: this script previously walked a `json_output/` directory that
does not exist in the repository. It validated nothing and reported
"VALIDATION PASSED". It now resolves paths from the repository root and treats
an empty file set as a failure.

Usage:
    .venv/bin/python tools/archived-old-tools/comprehensive_validation.py

Requires pypdf. Note that the 2012 records reference source PDFs by their
original vault paths, which are not present in this repository, so the
PDF-comparison checks will report the sources as missing.
"""

import os
import json
import pypdf
import re
from collections import defaultdict
from datetime import datetime

# The dataset this script's schema actually describes.
DATA_DIR = "data-archived-2012"


def validate_bcm_structure(json_data, json_path):
    """Validate BCM file structure and return issues/warnings"""
    issues = []
    warnings = []
    
    # Check required fields
    required_fields = ["document_type", "version", "date", "business_area", 
                      "process_name", "process_code", "sub_category", "page_count",
                      "maturity_model", "metadata"]
    
    for field in required_fields:
        if field not in json_data:
            issues.append(f"Missing required field: {field}")
    
    # Check maturity model
    if "maturity_model" in json_data:
        if "capability_questions" not in json_data["maturity_model"]:
            issues.append("Missing capability_questions in maturity_model")
        else:
            questions = json_data["maturity_model"]["capability_questions"]
            if len(questions) == 0:
                issues.append("No capability questions found")
            elif len(questions) < 4:
                warnings.append(f"Only {len(questions)} questions (expected 4-15)")
            
            # Check each question
            for i, q in enumerate(questions):
                if "question" not in q or len(q.get("question", "")) < 15:
                    issues.append(f"Question {i+1}: Too short or missing")
                
                if "levels" not in q:
                    issues.append(f"Question {i+1}: Missing levels")
                else:
                    for level_num in range(1, 6):
                        level_key = f"level_{level_num}"
                        if level_key not in q["levels"]:
                            issues.append(f"Question {i+1}: Missing {level_key}")
                        elif len(q["levels"][level_key]) < 20:
                            warnings.append(f"Question {i+1}, {level_key}: Very short content")
    
    # Check process name for artifacts
    if "process_name" in json_data:
        pname = json_data["process_name"]
        if ".pdf" in pname.lower() or "v3.0" in pname:
            issues.append(f"Process name contains artifacts: {pname}")
    
    return issues, warnings


def validate_bpt_structure(json_data, json_path):
    """Validate BPT file structure and return issues/warnings"""
    issues = []
    warnings = []
    
    # Check required fields
    required_fields = ["document_type", "version", "date", "business_area", 
                      "process_name", "process_code", "sub_category", "page_count",
                      "process_details", "metadata"]
    
    for field in required_fields:
        if field not in json_data:
            issues.append(f"Missing required field: {field}")
    
    # Check process details
    if "process_details" in json_data:
        pd = json_data["process_details"]
        
        # Check description
        if "description" not in pd or len(pd.get("description", "")) < 100:
            warnings.append("Description is missing or very short")
        
        # Check process steps (critical)
        if "process_steps" not in pd:
            issues.append("Missing process_steps")
        elif len(pd["process_steps"]) == 0:
            issues.append("process_steps array is empty")
        elif len(pd["process_steps"]) < 5:
            warnings.append(f"Only {len(pd['process_steps'])} process steps (expected 10-20)")
        
        # Check other arrays
        for field in ["trigger_events", "results"]:
            if field not in pd:
                warnings.append(f"Missing {field}")
            elif len(pd[field]) == 0:
                warnings.append(f"{field} array is empty")
    
    # Check process name for artifacts
    if "process_name" in json_data:
        pname = json_data["process_name"]
        if ".pdf" in pname.lower() or "v3.0" in pname:
            issues.append(f"Process name contains artifacts: {pname}")
    
    return issues, warnings


MISSING_SOURCE_COUNT = 0


def validate_against_pdf(json_data, json_path):
    """Validate JSON content against source PDF.

    The archived 2012 records cite their source by the original vault path
    ("BCM Vault v3.0/..."), which this repository does not ship - the 2012 PDFs
    live under source-pdfs/archived-2012-versions/ with different names. A
    missing source is therefore an expected, dataset-wide caveat, counted and
    reported once, not a per-file failure.
    """
    global MISSING_SOURCE_COUNT
    issues = []
    
    # Get source PDF path
    source_file = json_data.get("metadata", {}).get("source_file", "")
    if not source_file:
        issues.append("No source_file in metadata")
        return issues
    
    if not os.path.exists(source_file):
        MISSING_SOURCE_COUNT += 1
        return issues
    
    try:
        # Read PDF
        reader = pypdf.PdfReader(source_file)
        
        # Check page count
        if json_data.get("page_count") != len(reader.pages):
            issues.append(f"Page count mismatch: JSON={json_data.get('page_count')}, PDF={len(reader.pages)}")
        
    except Exception as e:
        issues.append(f"Error reading PDF: {str(e)}")
    
    return issues


def main():
    print("=" * 80)
    print("COMPREHENSIVE VALIDATION - MITA PDF TO JSON CONVERSIONS")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get all JSON files.
    #
    # This walked "json_output", a directory that has not existed in this
    # repository since before the first public commit. It therefore found zero
    # files and still printed "VALIDATION PASSED". The path is now resolved from
    # the repository root, and an empty file set is a hard failure rather than a
    # silent pass.
    # this file lives at <repo>/tools/archived-old-tools/, so go up three levels
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(here))
    data_dir = os.path.join(repo_root, DATA_DIR)

    all_json_files = []
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith(".json"):
                all_json_files.append(os.path.join(root, file))

    print(f"Validating {DATA_DIR} against the February 2012 schema")
    print(f"Found {len(all_json_files)} JSON files to validate\n")

    if not all_json_files:
        print(f"No JSON files found under {data_dir}.")
        print("Nothing was validated - refusing to report success.")
        return 2
    
    # Statistics
    stats = {
        'total': len(all_json_files),
        'passed': 0,
        'warnings': 0,
        'failed': 0,
        'errors': 0
    }
    
    stats_by_area = defaultdict(lambda: {
        'bcm_count': 0, 'bpt_count': 0,
        'bcm_questions_total': 0, 'bpt_steps_total': 0
    })
    
    issues_list = []
    warnings_list = []
    
    # Validate each file
    print("Validating files...")
    print("-" * 80)
    
    for json_path in sorted(all_json_files):
        try:
            with open(json_path, 'r') as f:
                json_data = json.load(f)
            
            doc_type = json_data.get("document_type", "UNKNOWN")
            business_area = json_data.get("business_area", "Unknown")
            
            # Structural validation
            if doc_type == "BCM":
                file_issues, file_warnings = validate_bcm_structure(json_data, json_path)
                stats_by_area[business_area]['bcm_count'] += 1
                q_count = len(json_data.get('maturity_model', {}).get('capability_questions', []))
                stats_by_area[business_area]['bcm_questions_total'] += q_count
            elif doc_type == "BPT":
                file_issues, file_warnings = validate_bpt_structure(json_data, json_path)
                stats_by_area[business_area]['bpt_count'] += 1
                s_count = len(json_data.get('process_details', {}).get('process_steps', []))
                stats_by_area[business_area]['bpt_steps_total'] += s_count
            else:
                file_issues = [f"Unknown document type: {doc_type}"]
                file_warnings = []
            
            # PDF validation
            pdf_issues = validate_against_pdf(json_data, json_path)
            file_issues.extend(pdf_issues)
            
            # Categorize results
            if file_issues:
                stats['failed'] += 1
                issues_list.append({
                    "file": json_path,
                    "issues": file_issues,
                    "warnings": file_warnings
                })
                print(f"✗ {os.path.basename(json_path)}: {len(file_issues)} issues")
            elif file_warnings:
                stats['warnings'] += 1
                warnings_list.append({
                    "file": json_path,
                    "warnings": file_warnings
                })
                stats['passed'] += 1
            else:
                stats['passed'] += 1
        
        except Exception as e:
            stats['errors'] += 1
            issues_list.append({
                "file": json_path,
                "issues": [f"Error: {str(e)}"],
                "warnings": []
            })
            print(f"⚠ {os.path.basename(json_path)}: ERROR - {str(e)}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total files: {stats['total']}")
    print(f"✓ Passed: {stats['passed']}")
    print(f"⚠ Warnings: {stats['warnings']}")
    print(f"✗ Failed: {stats['failed']}")
    print(f"⚠ Errors: {stats['errors']}")
    if MISSING_SOURCE_COUNT:
        print(f"\nNote: {MISSING_SOURCE_COUNT} records cite a source PDF that is not "
              f"in this repository, so their\ncontent could not be compared against "
              f"the source. The 2012 PDFs are under\nsource-pdfs/archived-2012-versions/ "
              f"under different names. Structural checks still ran.")
    
    # Statistics by business area
    print("\n" + "=" * 80)
    print("STATISTICS BY BUSINESS AREA")
    print("=" * 80)
    
    for area in sorted(stats_by_area.keys()):
        s = stats_by_area[area]
        bcm_avg = s['bcm_questions_total'] / s['bcm_count'] if s['bcm_count'] > 0 else 0
        bpt_avg = s['bpt_steps_total'] / s['bpt_count'] if s['bpt_count'] > 0 else 0
        print(f"\n{area}:")
        print(f"  BCM: {s['bcm_count']} files (avg {bcm_avg:.1f} questions)")
        print(f"  BPT: {s['bpt_count']} files (avg {bpt_avg:.1f} steps)")
    
    # Report issues
    if issues_list:
        print("\n" + "=" * 80)
        print("FILES WITH ISSUES")
        print("=" * 80)
        for item in issues_list[:10]:
            print(f"\n{item['file']}:")
            for issue in item['issues']:
                print(f"  ✗ {issue}")
        
        if len(issues_list) > 10:
            print(f"\n... and {len(issues_list) - 10} more files with issues")
    
    # Final result
    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    
    if stats['failed'] == 0 and stats['errors'] == 0:
        print("✓ VALIDATION PASSED")
        if MISSING_SOURCE_COUNT:
            print("All files are structurally correct against the 2012 schema.")
            print("Source-PDF comparison was skipped - see the note above.")
        else:
            print("All files are structurally correct and match source PDFs")
        return 0
    else:
        print(f"✗ VALIDATION FAILED")
        print(f"{stats['failed'] + stats['errors']} files need attention")
        return 1


if __name__ == "__main__":
    exit(main())
