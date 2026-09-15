# Creatinine result with typical real-world mistakes (deliberately invalid)

## Context

This submission exists so that the collection contains at least one example that
fails validation on purpose. It is the reference case for the pipeline: it shows
what the report looks like when things go wrong, and it demonstrates the
`knownIssues` suppression mechanism.

Serum creatinine (LOINC `2160-0`) was chosen because it is one of the most
frequently exchanged laboratory results, and because the four defects below are
exactly the ones that show up in production data.

## Origin

Synthetic, marked `HTEST`. Nothing here was taken from a real system, but every
defect was observed in the wild at some point.

## The deliberate defects

| # | Defect | Why it happens in practice |
|---|---|---|
| 1 | `status` is missing | The source system tracks result state in its own columns and never maps it. `Observation.status` is 1..1, so this is a cardinality error. |
| 2 | `code.coding.system` is `"LOINC"` | The system field is filled with the name of the code system instead of its canonical URI `http://loinc.org`. FHIR requires an absolute URI. |
| 3 | `effectiveDateTime` is `2025-01-20T07:40:00` | A local timestamp without an offset. FHIR requires a timezone as soon as a time is present, and a lot of exports drop it. |
| 4 | `valueQuantity.code` is `mg/deciliter` | The human-readable unit string is copied into `code`, which has to be a UCUM expression (`mg/dL`). The `referenceRange` in the same resource gets it right, so the two do not even agree with each other. |

The resource also carries no `meta.profile`, so rating level 3 (validated
against a profile) is out of reach by construction.

## What the validator does and does not catch

Defects 1 to 3 are reported: a cardinality error, a relative `Coding.system`
and a timestamp without an offset. The relative system produces a second,
softer finding as well, because a code system called `LOINC` cannot be looked
up, so the code itself cannot be validated either.

Defect 4 depends on the terminology server. `Quantity.code` with the UCUM
system is checked against UCUM, but that check runs on the terminology server:
when it is reachable, `mg/deciliter` is reported as an invalid unit; in a run
that had to fall back to `-tx n/a`, the validator only warns that the code
could not be checked. The site and the pull request comment say which of the
two happened.

A note on case: `mg/dl` would **not** be a defect. UCUM accepts both `l` and
`L` for litre, so the validator lets it pass, and rightly so.

This is worth knowing when reading the rest of the collection: a green result
means "nothing contradicted the profiles that were declared", not "the data is
correct".

## Suppression demo

`metadata.yaml` declares one `knownIssues` rule for the missing `status`. The
rule needs a `justification`, the suppressed finding is excluded from the
status calculation, and it is still counted and displayed — greyed out, with the
justification next to it. If the underlying issue ever disappears, the rule is
reported as stale.

That is the whole mechanism: accept a finding explicitly and in writing, rather
than silencing the validator.

## Files

| File | Content |
|---|---|
| `Observation-creatinine.json` | Creatinine result with four deliberate defects. |
