# Example Observation: TumorMutationBurdenExample01

## Context
Example [TumorMutationBurdenExample01](https://hl7.org/fhir/uv/genomics-reporting/STU3/Observation-TumorMutationBurdenExample01.html) from FHIR Genomics Reporting Implementation Guide 3.0.0.

Worth noticing:

- LOINC `94076-7` with `valueQuantity` 250.
- The quantity has no unit; the unit is implied by the LOINC code.
- Biomarker category: `molgen`.
- Compare with `tmb-example-genomics-reporting-ig`, the IG's other TMB example.

## Origin

https://hl7.org/fhir/uv/genomics-reporting/STU3/Observation-TumorMutationBurdenExample01.html

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
| `tmb-example01-genomics-reporting-ig.json` | Tumor mutation burden, 250. |
