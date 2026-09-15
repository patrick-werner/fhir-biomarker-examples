## What does this pull request add?

<!-- One or two sentences. For a new example: which biomarker, which context. -->

## Checklist

- [ ] The example contains **no** patient-identifiable data. It is synthetic,
      de-identified or derived from real data in a way that cannot be traced
      back to a person.
- [ ] I am allowed to publish this example, and I contribute it under the
      repository licence (Apache 2.0).
- [ ] `metadata.yaml` has a `title` and an honest `origin`
      (`real-world`, `derived-from-real` or `synthetic`).
- [ ] Optional: I ran `make check` locally.

## Notes for reviewers

<!-- Anything unusual: known validation errors, modelling decisions you want
     discussed, a question for the community. -->

---

Validation errors do **not** block this pull request. Only the structural checks
do — they make sure the files are parseable and sit in the right place.
Everything else is information: the bot comment shows what the FHIR validator
found so that readers of the collection know what they are looking at.
