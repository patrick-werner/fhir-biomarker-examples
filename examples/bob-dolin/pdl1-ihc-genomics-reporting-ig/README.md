# Example Observation: PDL1Example

## Context
Example [PDL1Example](https://hl7.org/fhir/uv/genomics-reporting/STU3/Observation-PDL1Example.html) from FHIR Genomics Reporting Implementation Guide 3.0.0.

Worth noticing:

- LOINC `85147-7` (PD-L1 by clone 22C3 in Tissue by Immune stain Report), coded result `LA6576-8` Positive; gene studied CD274 (HGNC:17635).
- The tumor proportion score (5%) is carried only as free text in `Observation.note`.
- Biomarker categories: `cellReceptorLigand`, `immuneStain`.

## Origin

https://hl7.org/fhir/uv/genomics-reporting/STU3/Observation-PDL1Example.html

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
| `pdl1-ihc-genomics-reporting-ig.json` | PD-L1 by immune stain (clone 22C3). |
