wird# How validation works

Everything CI does is a `python -m tools …` call, so every step can be
reproduced locally with the same command. The workflows contain no logic beyond
calling the tooling.

## The two layers

| Layer | Command | Blocks a merge? | What it answers |
|---|---|---|---|
| Structural checks | `python -m tools check` | **yes** | Is this a well-formed submission? |
| FHIR validation | `python -m tools validate` | no | What does the HL7 validator say about it? |

The separation is the whole point of the setup. A collection of real-world
examples contains invalid examples by definition — that is what makes it
interesting. `main` therefore stays green while the collection is full of
errors; it only turns red when the infrastructure itself breaks.

## Structural checks

`tools/check.py` walks `examples/`, enforces the layout, validates
`metadata.yaml` and `contributor.yaml` against the JSON schemas in `schema/`,
and parses every FHIR file. Folders starting with `_` (such as `_template`) are
ignored.

Two findings are warnings rather than errors: a missing `README.md`, and a
submission whose observations declare no `meta.profile` (which puts rating
level 3 out of reach).

## The validator

The validator is the official
[HL7 Java validator](https://github.com/hapifhir/org.hl7.fhir.core), pinned in
`validation.config.yaml`:

```yaml
validator:
  version: "6.10.4"
```

The jar is downloaded once into `.cache/validator/` and checked for size and zip
magic; set `validator.sha256` to verify the download as well. Bumps arrive as a
pull request from the `validator-update` workflow, together with the validation
results the new version produces — never as a silent `latest`.

## Grouping

Starting a JVM and loading implementation guides takes far longer than
validating a file. Submissions are therefore grouped by
`(fhirVersion, effective IGs)` and each group is validated in a single
invocation:

```
java -Xmx4g -Dfile.encoding=UTF-8 -jar .cache/validator/validator_cli-6.10.4.jar \
  -version 4.0.1 \
  -ig hl7.fhir.uv.genomics-reporting#3.0.0 \
  -tx https://tx.fhir.org -txCache .cache/txcache \
  -output results/raw/group-1.json -html-output results/raw/group-1.html \
  -show-message-ids -allow-example-urls true -extension any \
  -display-issues-are-warnings -best-practice warning \
  /abs/path/Observation-a.json /abs/path/Observation-b.json
```

The exact command of every run is written to `results/raw/group-<n>.cmd.txt`, so
a result can always be reproduced by hand.

Effective IGs are the defaults for the FHIR version (`defaultIgs` in the config)
plus whatever the submission declares in `metadata.igs`. Adding an IG to one
submission creates a second group; it does not slow the others down.

Two flags deserve a note. `-extension any` and `-display-issues-are-warnings`
are both about tolerance for real-world data: unknown extensions and mismatched
display strings are reported, but they do not make an example "wrong". Both are
configurable in `validation.config.yaml`.

## Attribution

The validator writes one `OperationOutcome` per input file into a single Bundle.
Each outcome carries an `operationoutcome-file` extension with the absolute path
of the source, which is matched back to the input by real path (with a suffix
match as a fallback). Outcomes that cannot be attributed become an
infrastructure warning rather than being dropped silently, and input files
without an outcome are reported as `not-validated` with a reason.

The predecessor project matched outcomes by file base name, which quietly
attributed findings to the wrong example as soon as two submissions used the
same file name.

## Status and counts

Per file, then aggregated per submission, worst wins:

| Status | Meaning |
|---|---|
| `not-validated` | No result — the validator crashed, timed out or skipped the file. |
| `errors` | At least one unsuppressed `error` or `fatal`. |
| `warnings` | At least one unsuppressed `warning`. |
| `valid` | Nothing but informational messages. |

Informational messages never affect the status. Suppressed findings are excluded
from the status but are counted and displayed.

## Known-issue suppression

`metadata.knownIssues` accepts rules with four optional matchers — `messageId`
(case-insensitive), `file` (exact file name), `location` and `details` (both
support `*` wildcards) — and a mandatory `justification`. All matchers given in
a rule must match. `location` is matched against the FHIRPath expression, or
against `Line n, Column m` when the validator reports no expression.

A rule that matches nothing is reported as **stale**, both in the pull request
comment and on the site. This is deliberate: suppressions that nobody prunes are
how a validation setup rots.

## Crashes

A crash is anything other than "the validator ran and produced parseable
output": a missing or broken output file, a timeout, a JVM failure. Then

- every file of that group becomes `not-validated` with the reason and the last
  40 log lines attached,
- the remaining groups still run,
- `validate` exits with code 2,
- the CI job fails — and on `main` the site is not deployed, so the last good
  version stays up.

Validation *errors*, by contrast, exit 0 and never fail a job.

## Terminology

`https://tx.fhir.org` is used by default, with a cache in `.cache/txcache` that
CI keeps across runs. `--offline` passes `-tx n/a`; the run then completes but
codes cannot be checked and the results are not comparable with an online run.

The server times out now and then. When a validator run fails only because the
server did not answer (the log says *Unable to connect to terminology server*),
the group is retried `terminology.retries` times and, if that does not help and
`terminology.fallbackToOffline` is set, validated once more with `-tx n/a`. Such
a run is marked everywhere: `terminologyFallback` in `results.json`, a warning in
the pull request comment and the job summary, and a banner on the site. It
reports fewer findings than usual because no LOINC, SNOMED CT or UCUM code was
checked. The logs of the failed attempts stay next to the final one as
`results/raw/group-<n>.attempt-<k>.log`. Every other kind of crash is reported
as a crash and is not retried.

Because terminology servers change independently of this repository, `main` is
revalidated weekly. A finding that appears without a commit is terminology
drift, and `results.json` records the validator version, jar SHA, IG versions,
terminology server and timestamp of every run so that such a change can be
pinned down.

## Limits worth knowing

**References are not resolved across files.** Each file is a separate source.
`subject: Patient/123` will not be found in a neighbouring file — use a `Bundle`
if you need resolution.

**Unbound codes are not checked.** If a profile does not bind an element to a
value set, the validator has nothing to check against. `examples/patrick-werner/creatinine-invalid-demo`
demonstrates this with a wrong UCUM unit that goes unreported. A `valid` status
means "nothing contradicted the declared profiles", not "the data is correct".

## Output

```
results/
├── results.json                     the full run: submissions, files, issues, groups
├── <contributor>/<slug>/<file>.oo.json   one OperationOutcome per input file
└── raw/
    ├── group-1.json                 the validator output as it came
    ├── group-1.html                 the validator's own HTML report
    ├── group-1.log                  stdout and stderr
    └── group-1.cmd.txt              the exact command line
```

`python -m tools report` turns this into the pull request comment, the job
summary and the static site. `site/results.json` is also the baseline the next
pull request compares against, which is where "+2 new / 1 fixed" comes from.
