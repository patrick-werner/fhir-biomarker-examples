# HER2 immunohistochemistry status as Genomics Reporting molecular biomarker

## Context

HER2 (gene `ERBB2`, HGNC:3430) status decides whether a breast cancer patient is
eligible for anti-HER2 therapy. In practice it is determined by
immunohistochemistry first and only reflex-tested by ISH when the IHC score is
equivocal. The interesting modelling question is where such a result belongs:
a plain laboratory `Observation`, a pathology finding, or a genomics resource.

This example takes the Genomics Reporting route and claims the
`molecular-biomarker` profile of HL7 Genomics Reporting 3.0.0 (R4).

## Origin

Synthetic. Written for this collection, marked `HTEST`.

## Representation notes

- `molecular-biomarker` requires two `category` entries: the usual
  `observation-category#laboratory` and the IG's own
  `tbd-codes-cs#biomarker-category` slice. Both are present, which is the part
  implementers most often miss.
- The observation code is LOINC `18474-7` ("HER2 Ag [Presence] in Tissue by
  Immune stain"); the result is a `CodeableConcept` rather than a quantity,
  because IHC reports a category, not a measurement.
- `component:gene-studied` (LOINC `48018-6`) names the gene using the HGNC
  system `http://www.genenames.org` with the code `HGNC:3430`, as required by
  the IG's `hgnc-vs` value set.
- Two `component:biomarker-category` entries classify the assay with
  `immuneStain` and `protein` from `molecular-biomarker-ontology-cs`.
- The ASCO/CAP IHC score is carried as a free-text component, because there is
  no widely used code for it. This is a deliberate compromise and a good
  candidate for community discussion.
- `effectiveDateTime` is a date without a time, which is what pathology systems
  usually report.

## Validation status

The example validates without errors, but it does not come out clean: HGNC is
not a code system the public terminology server can resolve, so the gene code
cannot be checked and is reported as a warning. The free-text IHC score
component produces an informational notice because it matches none of the
slices the profile defines. Both are expected here and both are exactly the
kind of friction that makes this example worth keeping.

## Files

| File | Content |
|---|---|
| `Observation-her2-ihc.json` | HER2 IHC result, molecular-biomarker profile. |
