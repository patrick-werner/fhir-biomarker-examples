# Example Observation: MSIExample

## Context
Example [MSIExample](https://hl7.org/fhir/uv/genomics-reporting/STU3/Observation-MSIExample.html) from FHIR Genomics Reporting Implementation Guide 3.0.0.

Worth noticing:

- LOINC `81695-9` (Microsatellite instability [Interpretation] in Cancer specimen Qualitative), coded result `LA26203-2` MSI-H.
- No gene-studied component: MSI is a genome-wide signature, not a single gene.
- Biomarker category: `molgen`.
- Compare with `msi-example01-genomics-reporting-ig`, the IG's second MSI example.

## Origin

https://hl7.org/fhir/uv/genomics-reporting/STU3/Observation-MSIExample.html

The narrative names the IG's fictional test patient; no real patient data.

## The deliberate defects

No deliberate defects. The idea with this example is to populate the repository with the IG's molecular-biomarker examples so that we can explore the repo's ability to help identify similar examples and reconcile them, as needed or desired, into a new FHIR Genomics profile.


## What the validator does and does not catch

Validation results are computed by CI and published on this submission's page on the [collection site](https://patrick-werner.github.io/fhir-biomarker-examples/).


## Suppression demo

none

## Files

| File | Content |
|---|---|
| `msi-example-genomics-reporting-ig.json` | Microsatellite instability, MSI-H. |
