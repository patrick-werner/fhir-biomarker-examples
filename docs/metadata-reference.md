# Metadata reference

Two files describe a submission. The authoritative definitions are
[`schema/contributor.schema.json`](../schema/contributor.schema.json) and
[`schema/metadata.schema.json`](../schema/metadata.schema.json); both use
`additionalProperties: false`, so a misspelled key fails the structural check
instead of being ignored.

## `examples/<contributor>/contributor.yaml`

| Field | Required | Rule |
|---|---|---|
| `name` | **yes** | 2–100 characters. A person or an organisation. |
| `organization` | no | 2–200 characters. |
| `github` | no | GitHub login without `@`, `^[A-Za-z0-9-]{1,39}$`. |
| `contact` | no | E-mail address, Zulip handle, whatever you prefer. |
| `url` | no | `http://` or `https://`. |

Minimal:

```yaml
name: Patrick Werner
```

One file per contributor folder. Who contributed what is answered by the folder
path plus the git history, not by a field repeated in every submission.

## `examples/<contributor>/<submission>/metadata.yaml`

Required: `title` and `origin`. Nothing else.

```yaml
title: HbA1c result as IPS laboratory observation
origin: synthetic
```

| Field | Required | Default / rule |
|---|---|---|
| `title` | **yes** | 3–120 characters. |
| `origin` | **yes** | `real-world`, `derived-from-real` or `synthetic`. |
| `description` | no | One or two sentences. Longer prose belongs in `README.md`. |
| `fhirVersion` | no | `4.0.1`, `4.3.0` or `5.0.0`. Default: `defaultFhirVersion` from the config (`4.0.1`). |
| `igs` | no | Extra implementation guides as `package#version`. Floating versions are rejected. |
| `category` | no | `lab`, `genomic`, `imaging` or `other`. Default: `other`. |
| `biomarkers` | no | Names, or `{name, system, code}` objects. Derived from `Observation.code` when omitted. |
| `custodian` | no | `{name, github, contact}`. Defaults to `contributor.yaml`. |
| `source` | no | `{vendor, system, project, url}` — where the example was produced. |
| `knownIssues` | no | Accepted findings, see below. |
| `review` | no | Maintainers only, see below. |

Deliberately absent: a schema version (the schema is versioned with the
repository), a submission date (derived from the first commit that touched the
folder), and the de-identification and licence declarations (they live in the
pull request template, where a human ticks them).

### `origin`

Be honest here; it is the basis of rating level 1.

- `real-world` — came out of a running system, possibly de-identified.
- `derived-from-real` — built from a real example, substantially rewritten.
- `synthetic` — invented.

### `igs`

```yaml
igs:
  - hl7.fhir.eu.laboratory#2.0.0
```

Always pinned: `#current`, `#dev` and `#latest` are rejected, because a result
that changes without a commit cannot be reasoned about. The defaults for the
FHIR version are always added on top.

### `biomarkers`

Omit this and the codes are taken from `Observation.code.coding`, which is right
most of the time. Set it when the code does not say what the biomarker is, or
when you want a different name on the site:

```yaml
biomarkers:
  - name: HER2
    system: http://www.genenames.org
    code: "HGNC:3430"
```

A plain list of strings also works: `biomarkers: [HbA1c]`.

### `knownIssues`

```yaml
knownIssues:
  - messageId: Validation_VAL_Profile_Minimum
    location: "Observation"
    justification: The source system never populates Observation.status.
```

| Matcher | Matching |
|---|---|
| `messageId` | Exact, case-insensitive. The id shown in the report. |
| `file` | Exact file name inside this submission. |
| `location` | FHIRPath expression, or `Line n, Column m`. `*` wildcards allowed. |
| `details` | The message text. `*` wildcards allowed. |
| `justification` | **Required**, at least 10 characters. |

At least one matcher must be present, and all matchers given must match. A
suppressed finding no longer counts towards the status, but it is still counted
and shown with its justification. A rule that matches nothing is reported as
stale.

### `review`

Set by maintainers, not by contributors.

| Field | Effect |
|---|---|
| `smeReviewed` | Rating level 2. |
| `consensus` | Rating level 4. |
| `reviewer`, `date`, `notes` | Documentation of the review. |
| `normalizedVersion` | Path of an improved variant of this submission. |

## Rating

The level shown is the **highest one reached**, not a sum:

| Level | Granted by |
|---|---|
| ★ | `origin` is `real-world` or `derived-from-real`. |
| ★★ | `review.smeReviewed`. |
| ★★★ | CI: every observation declares `meta.profile`, the status is not `not-validated`, and there are no unsuppressed errors. |
| ★★★★ | `review.consensus`. |

Suppressed errors do not prevent level 3, but they are visible on the submission
page, with the justification — so the level is never a way of hiding something.
