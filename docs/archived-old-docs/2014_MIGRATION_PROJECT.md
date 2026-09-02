> **ARCHIVED — historical record of the February 2012 to May 2014 migration.**
> File paths and script names in this document reflect the repository as it was
> during that work and are no longer accurate. For current documentation start at
> [../../README.md](../../README.md); for the schema see
> [../DATA_STRUCTURE.md](../DATA_STRUCTURE.md).
>
> Note also that the process counts in this document were provisional. The audit
> it references suspected the 2014 BCM set contained 73 processes; the published
> appendices in fact contain all 76, and the dataset has 76.

# MITA 2014 Migration Project

## Project Overview

**Objective**: Replace the 2012 MITA v3.0 data with the May 2014 updated versions while preserving the 2012 data for historical reference.

**Start Date**: January 12, 2026  
**Status**: 🟢 Phase 6 Complete - Ready for Commit

---

## Background

### Why This Migration?

The original MITA data in this repository was extracted from the February 2012 version of MITA v3.0. CMS released an updated version in May 2014 ("3.0 Update") which is now the current standard. This project updates our JSON data to reflect the 2014 versions.

### Key Differences: 2012 vs 2014 Source Files

| Aspect | 2012 Version | 2014 Version |
|--------|--------------|--------------|
| File Structure | Individual PDF per process (144 files) | Two master PDFs (one for all BPTs, one for all BCMs) |
| Split Structure | N/A | Split into per-business-area PDFs |
| Total BCM Processes | 72 | 76 |
| Total BPT Processes | 72 | 76 |
| Publication Date | February 2012 | May 2014 |

### Source File Locations

- **2012 (Archived)**: `source-pdfs/archived-2012-versions/`
- **2014 Master PDFs**: `source-pdfs/may-2014-update/`
  - `Part I Appendix C Business Process Model Details 3 0 Update.pdf` (all BPTs)
  - `Part I Appendix D Business Capability Matrix Details 3 0 Final V1 0.pdf` (all BCMs)
- **2014 Split PDFs**: 
  - `source-pdfs/may-2014-update/bcm/[Business Area]/` 
  - `source-pdfs/may-2014-update/bpt/[Business Area]/`
  - `source-pdfs/may-2014-update/business-architecture/` (overviews)

---

## Implementation Phases

### Phase 1: Archive Current Data ✅ COMPLETE
- [x] Move `data/` → `data-archived-2012/`
- [x] Create fresh `data/` folder structure
- [x] Create project tracking document

### Phase 2: Analyze 2014 PDF Structure ✅ COMPLETE
- [x] Extract and analyze sample BCM PDF (Care Management)
- [x] Extract and analyze sample BPT PDF (Care Management)
- [x] Document process boundary markers
- [x] Identify any new metadata fields
- [x] Identify any structural changes
- [x] Compare process list: 2012 vs 2014

### Phase 3: Schema Review & Design ✅ COMPLETE
- [x] Review current JSON schema
- [x] Identify new fields needed for 2014 content
- [x] Decide: per-process vs per-business-area JSON files (per-process)
- [x] Finalize schema (user approved)
- [x] Document text formatting preservation strategy
- [ ] Update `docs/DATA_STRUCTURE.md` (will do after extraction)

**Schema finalized**: `docs/PROPOSED_SCHEMA_2014.md`

### Phase 4: Build Extraction Tools ✅ COMPLETE
- [x] Create text cleaning/formatting utilities
- [x] Create BPT extraction module
- [x] Create BCM extraction module with position-based table parsing
- [x] Create image extraction module (for EE area)
- [x] Test on Care Management (9 processes, no diagrams)
- [x] Test on Eligibility & Enrollment (8 processes + diagrams)

**Tool created**: `tools/extract_2014.py`

### Phase 5: Extract & Convert All Data ✅ COMPLETE
- [x] Process all BPT business areas (9 areas, 76 processes)
- [x] Process all BCM business areas (9 areas, 76 processes)
- [x] Generate all JSON files
- [x] Extract images for Eligibility & Enrollment BPTs

**Extraction Results:**
- 76 BPT processes with full content extraction
- 76 BCM processes with position-based maturity level parsing
- 76 diagram images extracted for EE area

### Phase 6: Validation & QA ✅ COMPLETE
- [x] Create validation script for 2014 schema (`tools/validate_2014.py`)
- [x] Run comprehensive validation (152 files, 0 errors)
- [x] Fix "Capability Question" prefix artifact in BCM extraction
- [x] Manual fix for `OM_Calculate_Spend-Down_Amount_BCM_v3.0.json` (special deprecated process)
- [x] Verify `FM_Manage_Capitation_Payment_BPT_v3.0.json` (2 steps is correct per source)
- [x] Create HTML viewer for visual QA (`tools/viewer.html`)
- [x] Fix BPT description formatting (preserve bullets, sub-bullets, paragraphs)
- [x] Fix BPT process steps formatting (preserve sub-steps a/b/c and NOTE blocks)
- [x] Remove duplicate bullet artifacts from trigger events and results
- [x] Defer image/table extraction for manual handling (edge case in EE area only)
- [x] Fix BCM page break issues causing truncated/merged questions
- [x] Fix BCM process boundary detection (find process names, not table headers)
- [x] Add category header filtering (exclude section headers like "Accounts Payable Management")
- [x] Fix BCM question separation (detect new questions even with level content on same row)
- [x] Add NOTE display support in viewer.html (yellow background, below question text)
- [x] Remove spurious category header BCM files (18 files removed)
- [x] Add 3-level step hierarchy (numbered → letter sub-steps → roman numeral sub-sub-steps)
- [x] Add Alternate Path separators for alternate process flows
- [x] Convert Wingdings checkmarks to proper Unicode ✓ character
- [x] Fix "Manage 1099" BCM extraction (title case check was rejecting digit-starting words)

**Validation Results:**
- 152 files validated, all pass schema validation
- 76 BPT files: 822 total process steps (includes alternate path separators)
- 76 BCM files: 815 total capability questions
- 1 informational warning (FM_Manage_Contractor_Payment_BPT has 4 steps - correct per source)

### Phase 7: Documentation Updates 🔴 NOT STARTED
- [ ] Update `docs/DATA_STRUCTURE.md`
- [ ] Update `docs/CONVERSION_METHODOLOGY.md`
- [ ] Update `data/README.md`
- [ ] Update `source-pdfs/README.md`
- [ ] Update root `README.md`
- [ ] Archive/update `docs/EXAMPLES.md`

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-12 | Archive 2012 data (not delete) | Preserve for historical reference |
| 2026-01-12 | Re-evaluate JSON schema | 2014 may have new fields; opportunity to improve |
| 2026-01-12 | Keep per-process JSON files | Simpler edits, better git diffs, matches user workflows; extraction tool will split from per-area PDFs |
| 2026-01-12 | Add trigger_event sub-categories to schema | 2014 explicitly categorizes triggers as environment-based vs interaction-based |
| 2026-01-12 | Add image/diagram extraction support | Eligibility & Enrollment BPTs contain process flow diagrams; other areas don't have diagrams |
| 2026-01-12 | Use pymupdf (fitz) for PDF processing | Better image extraction support than pypdf; can render pages and extract embedded images |
| 2026-01-12 | Schema approved | User approved proposed schema with trigger event categorization, diagrams support, and formatting preservation |
| 2026-01-12 | No image dimensions in JSON | Not useful for consumers; keep schema simple |
| 2026-01-12 | Manual fix for edge cases | OM_Calculate_Spend-Down_Amount is a special deprecated process (L4/L5 not applicable); manual correction preferred over over-engineering extraction |
| 2026-01-12 | Remove category header BCM files | Section headers (e.g., "Accounts Payable Management", "Case Management") were incorrectly extracted as processes; added filtering |
| 2026-01-12 | Skip table headers in BCM extraction | "Capability Question Level 1" headers that repeat on each page were triggering false stop conditions |
| 2026-01-12 | 3-level step hierarchy for BPT | Consistent formatting: numbered steps (level 1), letter sub-steps a/b/c (level 2), roman numeral sub-sub-steps i/ii/iii (level 3) |
| 2026-01-12 | Alternate Path separators | Insert `--- Alternate Path: [name] ---` markers to visually distinguish alternate process flows |
| 2026-01-12 | Preserve checkmarks as Unicode | Convert Wingdings checkmarks (U+F0FC) to proper Unicode ✓ (U+2713) in JSON |
| 2026-01-12 | Allow digits in process names | Title case check now allows words starting with digits (e.g., "Manage 1099") |

---

## Open Questions

1. **JSON Granularity**: Should we keep one JSON file per process (current approach) or switch to one JSON file per business area (matching 2014 PDF structure)?
   - Pro per-process: Simpler edits, smaller files, matches 2012 approach
   - Pro per-area: Matches source structure, fewer files to manage
   - **RECOMMENDATION**: Keep per-process (see Decision Log)

2. ~~**Schema Changes**: What new fields exist in 2014 that weren't in 2012?~~
   - **ANSWERED**: Trigger events now have sub-categories (Environment-based vs Interaction-based)
   - Content is more detailed but structure is largely the same

3. ~~**Process Changes**: Are there new processes added or processes removed in 2014?~~
   - **ANSWERED**: Care Management has same 9 processes; full audit needed for all areas

4. ~~**Member Management**: The 2012 version had no Member Management data. Does 2014 include it?~~
   - **ANSWERED**: No, Member Management folder is still empty in 2014

---

## Notes & Findings

### Phase 2 Findings (2026-01-12)

#### PDF Structure Analysis

**BCM PDFs (2014)**
- One PDF per business area containing all processes for that area
- Process boundary marker: `[CODE] – [Sub-Category]\n[Process Name]\nCapability`
- Example: `CM – Case Management\nEstablish Case\nCapability`
- Table format with columns: Capability Question, Level 1-5
- Categories within each process (same as 2012):
  - Business Capability Descriptions
  - Business Capability Quality: Timeliness of Process
  - Business Capability Quality: Data Access and Accuracy
  - Business Capability Quality: Cost Effectiveness
  - Business Capability Quality: Effort to Perform; Efficiency
  - (and others)

**BPT PDFs (2014)**
- One PDF per business area containing all processes for that area
- Process boundary marker: `[CODE] [Sub-Category]\n[Process Name]\nItem Details`
- Example: `CM Case Management\nEstablish Case\nItem Details`
- Fields in each process (same as 2012):
  - Description
  - Trigger Event (now split into "Environment-based" and "Interaction-based")
  - Result
  - Business Process Steps
  - Shared Data
  - Predecessor
  - Successor
  - Constraints
  - Failures
  - Performance Measures

#### Key Observations

1. **Sub-Categories Exist**: Within Care Management, there are sub-categories:
   - "CM Case Management" (6 processes)
   - "CM Authorization Determination" (3 processes: Authorize Referral, Service, Treatment Plan)

2. **Process Count Matches**: Care Management has 9 processes in both 2012 and 2014

3. **Trigger Events Enhanced**: 2014 explicitly categorizes triggers as:
   - "Environment-based Trigger Events"
   - "Interaction-based Trigger Events"

4. **Member Management Still Empty**: The folder exists but contains no PDFs (same as 2012)

5. **Page References**: Each page includes "Part I, Appendix [C/D] - Page XX" and "May 2014 Version 3.0"

6. **Content Changes**: Descriptions appear more detailed in 2014 (e.g., Establish Case description includes specific claim indicators like "PWK - Attachments", "NTE - Notes", etc.)

#### Image/Diagram Analysis

**Eligibility and Enrollment BPTs contain process flow diagrams!**
- Page 2 of EE BPT has ~42 large images (>400px) that form process flow diagrams
- These appear to be visual representations of the Business Process Steps
- Largest images are ~663x615 and ~695x503 pixels
- Other business areas (Care Management, Financial Management) do NOT have diagrams

**Image Extraction Strategy:**
- Use pymupdf (fitz) library for image extraction
- Filter for meaningful images (>200x200 pixels to exclude borders/lines)
- Store images in `data/bpt/[area]/images/` folder
- Reference images in JSON via `process_details.diagrams` array

#### Business Areas Confirmed (2014)

| Business Area | BCM PDF | BPT PDF |
|---------------|---------|---------|
| Business Relationship Management | ✅ 4 processes | ✅ 4 processes |
| Care Management | ✅ 9 processes | ✅ 9 processes |
| Contractor Management | ✅ 9 processes | ✅ 9 processes |
| Eligibility and Enrollment Management | ✅ 8 processes | ✅ 8 processes |
| Financial Management | ✅ 19 processes | ✅ 19 processes |
| Member Management | ❌ (empty) | ❌ (empty) |
| Operations Management | ✅ 9 processes | ✅ 9 processes |
| Performance Management | ✅ 5 processes | ✅ 5 processes |
| Plan Management | ✅ 8 processes | ✅ 8 processes |
| Provider Management | ✅ 5 processes | ✅ 5 processes |
| **TOTAL** | **76 processes** | **76 processes** |

---

## Files Modified/Created

| File | Action | Date |
|------|--------|------|
| `data/` | Moved to `data-archived-2012/` | 2026-01-12 |
| `data/bcm/` | Created with 76 JSON files | 2026-01-12 |
| `data/bpt/` | Created with 76 JSON files + 76 images | 2026-01-12 |
| `docs/2014_MIGRATION_PROJECT.md` | Created | 2026-01-12 |
| `docs/PROPOSED_SCHEMA_2014.md` | Created | 2026-01-12 |
| `docs/2014_PROCESS_AUDIT.md` | Created | 2026-01-12 |
| `tools/extract_2014.py` | Created (BPT + BCM extraction) | 2026-01-12 |
| `tools/validate_2014.py` | Created (2014 schema validation) | 2026-01-12 |
| `OM_Calculate_Spend-Down_Amount_BCM_v3.0.json` | Manual fix (15 questions, L4/L5 N/A) | 2026-01-12 |
| `tools/viewer.html` | Created (visual QA tool with NOTE display) | 2026-01-12 |

---

## Pending Changes (Not Yet Committed)

The following changes are staged for the next commit:

- **22 files modified** (21 JSON files + extract_2014.py)
- **tools/extract_2014.py**: 
  - Added 3-level step hierarchy (numbered → letter → roman numeral)
  - Added Alternate Path separator detection and insertion
  - Converted Wingdings checkmarks to Unicode ✓
  - Fixed BCM process name detection to allow digit-starting words (e.g., "Manage 1099")
  - Preserved indentation in clean_text() and clean_extracted_text() functions
- **BPT files affected**: Process steps now have proper sub-step indentation and alternate path markers
- **BCM files affected**: FM_Manage_1099_BCM now properly extracted

**Suggested commit message:**
```
BPT formatting: 3-level hierarchy, alternate paths, checkmarks

- Added 3-level step hierarchy: numbered (1.), letter (a.), roman (i.)
- Added "--- Alternate Path: [name] ---" separators for alternate flows
- Converted Wingdings checkmarks (U+F0FC) to Unicode ✓ (U+2713)
- Fixed BCM "Manage 1099" extraction (allow digits in process names)
- Preserved indentation in text cleaning functions

Validation: 152 files pass (76 BPT, 76 BCM), 822 steps, 815 questions
```

---

## Team

- **Lead**: User + Kiro AI Assistant
- **Repository**: mita-open-blueprint
