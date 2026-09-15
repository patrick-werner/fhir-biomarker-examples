# HbA1c result as IPS laboratory observation

## Context

Glycated haemoglobin (HbA1c, LOINC `4548-4`) is the standard long-term marker of
glycaemic control. This example shows the representation most laboratory systems
produce when they export a single numeric result for an international patient
summary: one `Observation`, a quantity with a UCUM unit, an interpretation flag
and a reference range.

## Origin

Synthetic. The resource was written for this collection; the values are
plausible but do not come from a real patient. `meta.security` carries `HTEST`,
so the resource is recognisable as test data wherever it travels.

## Representation notes

- Claims the IPS profile
  `Observation-results-laboratory-pathology-uv-ips`, which requires `subject`,
  `effective[x]`, at least one `performer` and the `laboratory` category slice.
  All four are present, so the example reaches rating level 3.
- IPS is not one of the collection's default implementation guides, so
  `metadata.yaml` lists `hl7.fhir.uv.ips#2.0.1` under `igs`. That is all it
  takes for the validator to resolve the profile.
- The value is a `Quantity` with `system` `http://unitsofmeasure.org` and the
  UCUM code `%`. Note that `%` for HbA1c is the DCCT/NGSP convention; the IFCC
  convention would use `mmol/mol`. Both are found in the wild, which is exactly
  the kind of difference this collection is meant to make visible.
- `interpretation` uses `v3-ObservationInterpretation#H` rather than a free text
  flag, and `referenceRange.type` is coded as `normal`.
- A generated `text` narrative is included. FHIR's `dom-6` constraint asks for
  one, and without it the validator reports a warning — which is why plenty of
  otherwise clean real-world resources end up in the "warnings" bucket.
- References point at resources that are not part of the submission. The
  validator does not resolve references across files, so these are reported as
  informational at most. Contribute a `Bundle` if you want references resolved.

## Files

| File | Content |
|---|---|
| `Observation-hba1c.json` | HbA1c result, IPS laboratory/pathology profile. |
