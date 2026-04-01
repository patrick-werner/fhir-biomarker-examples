# FHIR Biomarker Examples Repository

## Overview

This repository collects real-world example data of **biomarker representations in FHIR**.

Biomarkers are currently **not consistently standardized** in FHIR:
- LOINC defines concept codes, but not full profile structures
- Representation patterns (e.g. components, grouping, units) vary significantly
- Implementations differ across vendors, projects, and use cases

The goal of this repository is to:
- Capture **real-world implementations**
- Enable **comparison across approaches**
- Support **community consensus building**
- Provide **reference examples for implementers**

This is a **community-driven effort** with a **low barrier to contribution**.

---

## Scope

We accept examples of:
- FHIR `Observation` resources representing biomarkers
- Biomarker-related structures (e.g. panels)
- Biomarkers within a `DiagnosticReport` context
- Genomic / molecular biomarkers
- Standalone observations or fully structured bundles

Examples do **not need to be perfect or fully valid**.  
Capturing real-world data is more important than correctness.

---

## What is a Biomarker?

For the purposes of this repository, a biomarker is:

> A measurable indicator of a biological state, condition, or process, used for diagnosis, prognosis, or treatment decisions.

---

## Repository Structure

```
/input/
  <submission-id>/
    README.md
    example.json

/validated/
  <example-id>/
    README.md
    example.json
```

### Input
- Raw submissions from the community
- May be incomplete or non-conformant
- Each submission should include a README and a named custodian

### Validated
- Reviewed by subject matter experts (SMEs)
- May include:
  - Profile validation results
  - Improved or normalized versions
  - Notes on interpretation

---

## Submission Guidelines

We intentionally keep submission simple.

You can contribute by:
- Opening a Pull Request
- Sharing examples via Zulip or email (maintainers will add them)
- Contributing during HL7 Connectathons

### Minimal Requirements

Each submission should include:
- Example file(s) (JSON or XML)
- A short `README.md` describing:
  - Context / use case
  - Origin (vendor, project, synthetic, etc.)
  - Contact person (custodian)

### Important Notes

- Examples do **not need to validate**
- Errors are acceptable
- Do not include sensitive or identifiable patient data

---

## Evaluation & Quality Indicators

We plan to introduce a **lightweight rating system** to help users understand example quality, e.g.:

- ⭐ Real-world example
- ⭐⭐ Reviewed by SME
- ⭐⭐⭐ Validated against profile
- ⭐⭐⭐⭐ Consensus example

This system is **informational only** and does not block submissions.

---

## Guiding Principles

- **Open collection** – no gatekeeping of submissions
- **Reality over perfection**
- **No blame** – examples are not used to criticize implementations
- **Community consensus over time**

---

## Nature of the Content

This repository contains example data only.

Examples:
- may be incomplete
- may not validate
- may not follow best practices

They are intended to reflect real-world implementations, not ideal models.

---

## Data Disclaimer

All examples must be fully de-identified.

No real patient-identifiable information (PII) must be included.
Contributors are responsible for ensuring that shared examples comply with applicable data protection regulations.

---

## Related Work & References

Structured document examples:
- https://build.fhir.org/ig/HL7/CDA-Examples/
- https://github.com/jddamore/ccda-samples

FHIR Genomics Reporting:
- https://build.fhir.org/ig/HL7/genomics-reporting/
- https://build.fhir.org/ig/HL7/genomics-reporting/StructureDefinition-molecular-biomarker.html

---

## Future Directions

- Define clearer biomarker taxonomy
- Align with HL7 Genomics Reporting IG glossary
- Integrate automated validation (FHIR Validator)
- Provide rendered views of examples (via IG / viewer)
- Highlight consensus examples per use case

---

## How to Engage

- Share examples during HL7 Connectathons
- Discuss in Zulip (Genomics, OO, Implementers, Cancer streams)
- Contribute via GitHub

---

## Maintainers

- Patrick Werner
- (add others)

---

## License

This repository is licensed under the Apache License 2.0.

The license applies to all example content (e.g. FHIR JSON/XML files), documentation, and supporting materials.
