# Contributing to MITA BCM & BPT Data Repository

Thank you for your interest in contributing! This repository aims to be the definitive source for machine-readable MITA data, and community contributions help ensure accuracy and completeness.

## Ways to Contribute

### 1. Report Data Quality Issues

If you find errors, omissions, or inconsistencies in the JSON data:

1. Check if the issue already exists in [GitHub Issues](../../issues)
2. If not, create a new issue using the "Data Quality Issue" template
3. Include:
   - The specific file(s) affected
   - Description of the issue
   - Reference to the source PDF (page number if possible)
   - Expected vs. actual content

### 2. Submit Corrections

To fix data quality issues:

1. Fork the repository
2. Make your corrections to the JSON files in `data/`
3. Verify your changes against the source PDFs in `source-pdfs/`
4. Run validation: `.venv/bin/python tools/verify_against_source.py`
5. Submit a Pull Request with:
   - Clear description of what was corrected
   - Reference to the source PDF
   - Before/after examples

### 3. Improve Documentation

Documentation improvements are always welcome:

- Clarify existing documentation
- Add usage examples
- Fix typos or formatting
- Improve code samples

Submit documentation changes via Pull Request.

### 4. Add New MITA Versions

When CMS releases new MITA versions:

1. Open an issue to discuss the new version
2. Follow the conversion methodology in `docs/CONVERSION_METHODOLOGY.md`
3. Archive existing data (see `docs/archived-old-docs/2014_MIGRATION_PROJECT.md` for reference)
4. Validate all conversions using `tools/verify_against_source.py`
5. Submit a Pull Request with the new data

### 5. Enhance Tooling

Improvements to validation or utility scripts:

1. Ensure backward compatibility
2. Add tests if applicable
3. Update tool documentation
4. Submit a Pull Request

## Contribution Guidelines

### Code of Conduct

- Be respectful and constructive
- Focus on improving data quality and accessibility
- Assume good faith in all interactions
- Help create a welcoming environment for all contributors

### Quality Standards

All contributions must:

- **Maintain accuracy**: Changes must match source CMS documents
- **Preserve structure**: Follow existing JSON schema patterns
- **Pass validation**: Run validation tools before submitting
- **Include documentation**: Update docs if changing structure or adding features

### Pull Request Process

1. **Fork & Branch**: Create a feature branch from `main`
2. **Make Changes**: Implement your contribution
3. **Test**: Validate your changes
4. **Document**: Update relevant documentation
5. **Submit PR**: Use the Pull Request template
6. **Review**: Respond to feedback and make requested changes
7. **Merge**: Maintainers will merge approved PRs

### Commit Message Format

Use clear, descriptive commit messages:

```
Fix: Correct process steps in CM_Establish_Case_BPT_v3.0.json

- Fixed step 5 description to match source PDF page 3
- Corrected typo in trigger_events array
- Verified against source document
```

Types of commits:
- `Fix:` - Corrections to existing data
- `Docs:` - Documentation changes
- `Add:` - New files or features
- `Update:` - Updates to existing content
- `Tool:` - Changes to validation or utility scripts

## Data Quality Standards

### Validation Requirements

Before submitting changes to JSON files:

1. **Structural Validation**: Ensure JSON is well-formed
2. **Schema Compliance**: Match existing field structure
3. **Content Accuracy**: Verify against source PDF
4. **Completeness**: Include all required fields
5. **Consistency**: Follow naming conventions
6. **Run Validation**: Execute `.venv/bin/python tools/verify_against_source.py` and confirm `0 errors`

A clean run reports five warnings. Those are expected - they flag questions whose
source table cell wraps across a line or page break, so the text is correctly
reassembled from more than one fragment. If your change adds a warning, check the
fragments the tool prints and make sure the reassembly is right.

### What not to "fix"

The source PDFs are authoritative, including where CMS is inconsistent. These are
faithful and should be left alone:

- Where CMS names a process differently in its two appendices (CM06 and PL07),
  `process_name` follows the framework's Business Architecture index so the BCM
  and BPT halves pair, and `metadata.source_process_name` records what the
  record's own appendix published. Do not "correct" either one to match the
  other.
- `predecessor_processes` and `successor_processes` contain free text as
  published, including prose `NOTE:` blocks and the literal string `None`. Of 616
  references, 130 do not resolve to a process in this dataset - most name Member
  Management processes, which the framework defines but never published.
- Two capability questions end in a full stop rather than a question mark.
- Performance measures contain blanks (`within __ days`) as published.

### Source Verification

All data changes must be verifiable against source PDFs:

- Reference specific page numbers
- Quote relevant source text
- Explain any interpretation decisions
- Document any ambiguities in source material
- Source PDFs are located in `source-pdfs/may-2014-update/` (current) and `source-pdfs/archived-2012-versions/` (historical)

## Issue Templates

We provide templates for common issue types:

- **Bug Report**: For technical issues with the repository
- **Data Quality Issue**: For errors or omissions in JSON data

Please use the appropriate template when creating issues.

## Review Process

### Timeline

- Initial review: Within 1 week
- Follow-up responses: Within 3-5 business days
- Merge decision: After all feedback addressed

### Criteria for Acceptance

Pull requests are evaluated on:

1. **Accuracy**: Does it correctly represent source material?
2. **Quality**: Is the code/data well-structured?
3. **Documentation**: Are changes properly documented?
4. **Testing**: Have validation checks passed?
5. **Impact**: Does it improve the repository?

## Getting Help

### Questions?

- **General questions**: Open a [GitHub Discussion](../../discussions)
- **Specific issues**: Create a [GitHub Issue](../../issues)
- **Contribution help**: Tag your issue with `help wanted`

### Resources

- [Data Structure Guide](docs/DATA_STRUCTURE.md)
- [Conversion Methodology](docs/CONVERSION_METHODOLOGY.md)
- [Tools](tools/README.md)
- [Remediation Plan](docs/REMEDIATION_PLAN.md) - defects found against the source PDFs, and how each was repaired
- [2014 Migration Project](docs/archived-old-docs/2014_MIGRATION_PROJECT.md)
- [Usage Examples](docs/EXAMPLES.md)
- [Official CMS MITA Documentation](https://www.medicaid.gov/medicaid/data-systems/medicaid-information-technology-architecture/medicaid-information-technology-architecture-framework)

## Recognition

Contributors will be recognized in:

- GitHub's contributor list
- Release notes for significant contributions
- Special acknowledgment for major improvements

## License Agreement

By contributing, you agree that:

- Your contributions will be licensed under the [MIT License](https://opensource.org/licenses/MIT)
- You have the right to submit the contribution
- You understand the contribution becomes part of the public repository

Note that the underlying MITA content is a U.S. Government work in the public domain. Corrections that bring the JSON closer to the source PDFs are transcription fixes, not creative contributions, and carry no separate copyright.

## Maintainer Responsibilities

Repository maintainers will:

- Review contributions promptly
- Provide constructive feedback
- Maintain data quality standards
- Keep documentation current
- Foster a welcoming community

## Future Contribution Opportunities

Areas where we'd especially welcome contributions:

- Additional usage examples in various programming languages
- Cross-reference mapping between related processes
- Automated testing improvements
- Documentation enhancements
- Tools for working with the data

---

Thank you for contributing to making MITA data more accessible!

**Questions?** Open an issue or discussion - we're here to help.
