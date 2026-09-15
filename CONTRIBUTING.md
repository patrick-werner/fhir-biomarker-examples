# Contributing an example

The bar is deliberately low. A submission needs **one FHIR file** and **two
lines of metadata**. Your example does not have to validate, and validation
errors never block a pull request.

## The quick version

```
examples/<your-slug>/
├── contributor.yaml            name: Your Name
└── <example-slug>/
    ├── metadata.yaml           title: …   origin: …
    ├── README.md               optional, but please write one
    └── Observation-*.json      one or more FHIR resources
```

1. Fork the repository and create a branch.
2. Copy `examples/_template/` to `examples/<your-slug>/`. Slugs are lower case,
   digits and hyphens (`^[a-z0-9][a-z0-9-]{1,62}$`).
3. Put your resource(s) into the submission folder. JSON and XML both work.
4. Fill in `metadata.yaml`:

   ```yaml
   title: PSA result from our laboratory system
   origin: real-world
   ```

   That is genuinely all that is required. `origin` is one of `real-world`,
   `derived-from-real` or `synthetic`.
5. Open a pull request and tick the boxes in the template.

## What happens then

| | |
|---|---|
| **Structural checks** run first | Parseable files, the layout above, the two metadata fields. **These block the merge.** |
| **FHIR validation** runs second | The HL7 Java validator, pinned to one version, with a fixed set of implementation guides. **This never blocks the merge.** |
| **A bot comment** appears | A table with the status of each submission, the findings, and what changed compared with `main`. It is updated in place on every push. |
| **After the merge** | The collection is re-validated and the [site](https://patrick-werner.github.io/fhir-biomarker-examples/) is rebuilt. |

## Rules that actually block

The gate is `python -m tools check`. It fails when:

- a file sits somewhere other than the layout above (no subfolders inside a
  submission, no loose files, only `.json` and `.xml` besides `metadata.yaml`
  and `README.md`),
- `metadata.yaml` is missing, unparseable, lacks `title` or `origin`, or
  contains a key that does not exist (typos fail loudly on purpose),
- `contributor.yaml` is missing or has no `name`,
- a FHIR file is not parseable or has no `resourceType`,
- an `igs` entry uses a floating version such as `#current`,
- a submission has no FHIR file at all.

Everything else — including a resource that fails validation completely — is
information, not a blocker.

## Running the checks locally (optional)

```bash
make install                                       # creates .venv
make check                                         # the blocking gate, seconds
make validate SUBMISSION=examples/you/your-example # needs Java 21, downloads ~190 MB once
make site && make serve                            # look at the result
```

The first validator run also downloads the implementation guide packages into
`~/.fhir/packages`; expect a few minutes. Later runs are fast.

## Choosing what to submit

Good submissions:

- come from a real system, even when they are messy,
- show a modelling decision worth discussing (components versus separate
  observations, which code system, how the unit is expressed),
- include a `README.md` that explains the context and what is unusual.

You may submit a single `Observation`, a panel, a `DiagnosticReport` with
results, or a full `Bundle`.

## Practical notes

**References between files are not resolved.** Each file is validated on its own,
so `Patient/123` in one file will not find `Patient` in the file next to it. If
you want references resolved, contribute a `Bundle` containing everything.

**XML works exactly like JSON.** Same layout, same checks.

**Extra implementation guides** go into `metadata.yaml`, always pinned:

```yaml
igs:
  - hl7.fhir.eu.laboratory#2.0.0
```

The defaults (IPS and Genomics Reporting for R4) are always loaded on top of
this. Submissions with the same FHIR version and the same IG set are validated
in one validator run.

**Findings you know about and accept** go into `knownIssues`. A justification is
mandatory, and a rule that stops matching is reported as stale so it does not
rot:

```yaml
knownIssues:
  - messageId: Terminology_TX_System_Relative
    file: Observation-example.json
    justification: The source system emits the code system name, and we want that visible.
```

A suppressed finding no longer counts towards the status, but it is still shown —
greyed out, with your justification next to it. See
[`docs/metadata-reference.md`](docs/metadata-reference.md) for every field and
[`docs/validation.md`](docs/validation.md) for how validation works.

## De-identification

This is the one thing we are strict about. Examples must contain no
patient-identifiable data. Replace names, identifiers, contact details and
addresses, and shift or truncate dates of birth. Tagging the resource with
`meta.security` `HTEST` is good practice:

```json
"meta": {
  "security": [
    {"system": "http://terminology.hl7.org/CodeSystem/v3-ActReason", "code": "HTEST"}
  ]
}
```

CI runs simple heuristics and points out anything that looks like a name, an
address, an e-mail address or a phone number. They are hints, not a guarantee —
you remain responsible for what you publish.

## No pull request? No problem

Open an [issue using the submission form](https://github.com/patrick-werner/fhir-biomarker-examples/issues/new?template=submit-example.yml),
send the example by e-mail, post it on Zulip, or bring it to a connectathon. A
maintainer will add it and credit you in `contributor.yaml`.

## Licence

Contributions are published under the Apache License 2.0, like the rest of the
repository.
