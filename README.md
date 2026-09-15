# FHIR Biomarker Examples Repository

[![Validation status](https://img.shields.io/endpoint?url=https%3A%2F%2Fpatrick-werner.github.io%2Ffhir-biomarker-examples%2Fbadge.json)](https://patrick-werner.github.io/fhir-biomarker-examples/)

**Browse the collection: <https://patrick-werner.github.io/fhir-biomarker-examples/>**

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

Examples never move. Every submission stays where its contributor put it, and
its status is computed by CI and published on the site.

```
examples/
  <contributor-slug>/
    contributor.yaml              name: …          (the only required field)
    <submission-slug>/
      metadata.yaml               title: …  origin: …   (the only required fields)
      README.md                   context, origin, modelling notes
      Observation-*.json|xml      one or more FHIR resources
```

Supporting parts of the repository:

| Path | What it is |
|---|---|
| `validation.config.yaml` | The single source of truth: validator version, implementation guides, limits. |
| `schema/` | JSON Schemas for `metadata.yaml` and `contributor.yaml`. |
| `tools/` | The Python tooling behind every CI step; runs locally the same way. |
| `docs/` | [How validation works](docs/validation.md), [metadata reference](docs/metadata-reference.md). |
| `examples/_template/` | Copy this to start a submission. |

---

## Validation

Every pull request gets an automated report, and the whole collection is
revalidated on `main` and once a week.

- **Structural checks block a merge**: files must be parseable and sit in the
  layout above, and `metadata.yaml` needs `title` and `origin`.
- **FHIR validation never blocks a merge.** The HL7 Java validator runs against
  a pinned version and a fixed set of implementation guides, and its findings
  are published as information about the example.

That distinction is deliberate: a collection of real-world data contains invalid
data, so `main` is never red because an example has errors — only when the
infrastructure breaks.

Details: [`docs/validation.md`](docs/validation.md).

---

## Submission Guidelines

We intentionally keep submission simple. Step by step:
[**CONTRIBUTING.md**](CONTRIBUTING.md).

You can contribute by:
- Opening a Pull Request
- Opening an [issue with the submission form](https://github.com/patrick-werner/fhir-biomarker-examples/issues/new?template=submit-example.yml)
- Sharing examples via Zulip or email (maintainers will add them)
- Contributing during HL7 Connectathons

### Minimal Requirements

Each submission needs:
- Example file(s) (JSON or XML)
- `metadata.yaml` with exactly two fields: `title` and `origin`

Strongly encouraged, but not enforced — a short `README.md` describing:
- Context / use case
- Origin (vendor, project, synthetic, etc.)
- The modelling decisions worth discussing

The custodian defaults to your `contributor.yaml`, the biomarker codes are read
out of `Observation.code`, and the submission date comes from the git history.

### Important Notes

- Examples do **not need to validate**
- Errors are acceptable
- Do not include sensitive or identifiable patient data

---

## Evaluation & Quality Indicators

A **lightweight rating system** helps users understand example quality:

- ⭐ Real-world example — `origin` is `real-world` or `derived-from-real`
- ⭐⭐ Reviewed by SME — set by a maintainer after review
- ⭐⭐⭐ Validated against profile — computed by CI: every observation declares
  `meta.profile` and validation produced no unsuppressed errors
- ⭐⭐⭐⭐ Consensus example — the community agreed this is how it should be done

A submission shows the **highest level it has reached**; the levels are not
cumulative requirements. Level 3 is the only one awarded automatically.

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
- Provide rendered views of examples (via IG / viewer)
- Highlight consensus examples per use case

Already in place: automated validation with the HL7 FHIR validator, per-code
[comparison pages](https://patrick-werner.github.io/fhir-biomarker-examples/biomarkers/index.html)
that put different representations of the same biomarker side by side, and a
machine-readable
[`results.json`](https://patrick-werner.github.io/fhir-biomarker-examples/results.json).

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
