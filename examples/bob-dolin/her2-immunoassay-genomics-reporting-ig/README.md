# Example Observation: HER2byImmunoassayExample

## Context
Example [HER2byImmunoassayExample](https://hl7.org/fhir/uv/genomics-reporting/STU3/Observation-HER2byImmunoassayExample.html) from FHIR Genomics Reporting Implementation Guide 3.0.0.

Worth noticing:

- Same biomarker as `her2-ihc-genomics-reporting-ig`, different method: LOINC `72382-5` (HER2 [Units/volume] in Tissue by Immunoassay) with a `valueQuantity` instead of a coded presence/absence.
- The quantity is `20` with `unit` `IU/mL` but no UCUM `system` or `code`.
- Biomarker categories: `immunoassay`, `cellReceptor`, `protein`.

## Origin

https://hl7.org/fhir/uv/genomics-reporting/STU3/Observation-HER2byImmunoassayExample.html

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
| `her2-immunoassay-genomics-reporting-ig.json` | HER2 by immunoassay. |
