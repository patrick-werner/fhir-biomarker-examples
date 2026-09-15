"""The pull request comment, the baseline delta, the biomarker index and the site."""

from __future__ import annotations

from pathlib import Path

from tools.baseline import describe, diff, fingerprint
from tools.biomarkers import build_index, slugify
from tools.report_md import MARKER_END, MARKER_START, ig_label, render_job_summary, render_pr_comment
from tools.results import FileResult, Issue, RunResult, SubmissionResult
from tools.site import badge, build_site, render_markdown


def make_run(*submissions: SubmissionResult, **kwargs) -> RunResult:
    run = RunResult(
        generatedAt="2026-02-01T10:00:00Z",
        validator={"version": "6.10.4"},
        terminology="https://tx.fhir.org",
        **kwargs,
    )
    run.submissions = list(submissions)
    return run


def make_submission(
    identifier: str = "c/s",
    issues: list[Issue] | None = None,
    title: str = "An example",
    **kwargs,
) -> SubmissionResult:
    contributor, slug = identifier.split("/")
    entry = SubmissionResult(
        id=identifier,
        contributor=contributor,
        slug=slug,
        title=title,
        origin="synthetic",
        category="lab",
        igs=["hl7.fhir.uv.ips#2.0.1"],
        custodian={"name": "Some One", "github": "", "contact": ""},
        biomarkers=[{"name": "HbA1c", "system": "http://loinc.org", "code": "4548-4"}],
        **kwargs,
    )
    entry.files = [
        FileResult(
            name="Observation-a.json",
            path=f"examples/{contributor}/{slug}/Observation-a.json",
            resourceType="Observation",
            profiles=["http://hl7.org/fhir/uv/ips/StructureDefinition/x"],
            status="valid",
            issues=issues or [],
            observations=[
                {
                    "resourceId": "a",
                    "resourceType": "Observation",
                    "profiles": [],
                    "code": [{"system": "http://loinc.org", "code": "4548-4", "display": "HbA1c"}],
                    "codeText": "HbA1c",
                    "valueType": "Quantity",
                    "valueText": "6.4 %",
                    "unit": "%",
                    "componentCodes": [],
                    "categoryCodes": ["observation-category|laboratory"],
                    "hasInterpretation": True,
                    "hasReferenceRange": True,
                    "method": None,
                    "specimen": None,
                }
            ],
        )
    ]
    entry.recompute()
    return entry


def test_comment_contains_the_markers_and_the_table(cfg):
    run = make_run(make_submission(issues=[Issue(severity="error", messageId="E1", details="boom")]))
    body = render_pr_comment(cfg, run, {}, check_summary="<!-- check-status: passed -->\n### Structural checks: ✅ passed\n")
    assert body.startswith(MARKER_START)
    assert body.rstrip().endswith(MARKER_END)
    assert "| Submission | FHIR | Status |" in body
    assert "`c/s`" in body
    assert "<details>" in body
    assert "E1" in body


def test_failed_checks_omit_the_rest(cfg):
    run = make_run(make_submission())
    body = render_pr_comment(
        cfg, run, {}, check_summary="<!-- check-status: failed -->\n### Structural checks: ❌ failed\n"
    )
    assert "| Submission | FHIR | Status |" not in body
    assert "structural checks must pass" in body


def test_comment_without_results(cfg):
    body = render_pr_comment(cfg, RunResult(validator={"version": "6.10.4"}), {})
    assert "No FHIR validation results in this comment" in body


def test_comment_respects_the_budget(cfg):
    issues = [Issue(severity="error", messageId=f"E{n}", details="x" * 200) for n in range(50)]
    submissions = [make_submission(f"c/s{n}", issues=list(issues)) for n in range(40)]
    run = make_run(*submissions)
    body = render_pr_comment(cfg, run, {})
    assert len(body) <= cfg.report.prCommentBudgetChars
    assert "not shown here" in body


def test_baseline_delta(cfg):
    old_issue = Issue(severity="error", messageId="E1", details="boom", expression=["Observation"], line=3)
    same_issue = Issue(severity="error", messageId="E1", details="boom", expression=["Observation"], line=99)
    new_issue = Issue(severity="error", messageId="E2", details="other", expression=["Observation"])

    baseline = make_run(make_submission(issues=[old_issue]))
    current = make_run(make_submission(issues=[same_issue, new_issue]))
    delta = diff(current, baseline)
    assert delta["c/s"]["new"] == 1
    assert delta["c/s"]["fixed"] == 0
    assert delta["c/s"]["unchanged"] == 1  # the line number moved, the finding did not
    assert describe(delta["c/s"]) == "+1 new"

    fixed = diff(make_run(make_submission(issues=[])), baseline)
    assert describe(fixed["c/s"]) == "1 fixed"
    assert describe(diff(make_run(make_submission("c/new")), baseline)["c/new"]) == "new submission"
    assert describe(None) == "–"


def test_fingerprint_ignores_line_and_column():
    a = Issue(severity="error", messageId="E", details="d", expression=["x"], line=1, col=2)
    b = Issue(severity="error", messageId="E", details="d", expression=["x"], line=9, col=9)
    assert fingerprint("f", a) == fingerprint("f", b)


def test_biomarker_index_groups_occurrences():
    run = make_run(make_submission("a/one"), make_submission("b/two"))
    index = build_index(run)
    assert len(index) == 1
    entry = index[0]
    assert entry["code"] == "4548-4"
    assert entry["systemLabel"] == "LOINC"
    assert entry["submissionCount"] == 2
    assert entry["slug"] == "loinc.org/4548-4"


def test_slugify_is_path_safe():
    assert slugify("http://loinc.org") == "loinc.org"
    assert slugify("HGNC:3430") == "hgnc-3430"
    assert slugify("") == "none"


def test_badge_is_a_shields_endpoint():
    run = make_run(make_submission("a/one"), make_submission("b/two", issues=[Issue(severity="error")]))
    payload = badge(run)
    assert payload["schemaVersion"] == 1
    assert payload["label"] == "examples"
    assert payload["color"] == "blue"
    assert "1 valid" in payload["message"] and "1 errors" in payload["message"]


def test_markdown_is_sanitised():
    rendered = render_markdown("# Title\n\n<script>alert(1)</script>\n\n[ok](https://example.org)\n")
    assert "<h1>Title</h1>" in rendered
    assert "<script>" not in rendered
    assert "alert(1)" in rendered  # dropped tag, text kept
    assert '<a href="https://example.org">ok</a>' in rendered


def test_markdown_drops_dangerous_urls():
    rendered = render_markdown("[click](javascript:alert(1))")
    assert "javascript:" not in rendered


def test_ig_label_is_short():
    assert ig_label("hl7.fhir.uv.ips#2.0.1") == "ips 2.0.1"


def test_site_builds_every_page(cfg, tmp_path: Path):
    run = make_run(make_submission("a/one"), make_submission("b/two", issues=[Issue(severity="error", messageId="E")]))
    run.biomarkers = build_index(run)
    target = tmp_path / "site"
    build_site(cfg, run, target)
    assert (target / "index.html").is_file()
    assert (target / ".nojekyll").is_file()
    assert (target / "badge.json").is_file()
    assert (target / "results.json").is_file()
    assert (target / "biomarkers.json").is_file()
    assert (target / "contributors" / "index.html").is_file()
    assert (target / "biomarkers" / "loinc.org" / "4548-4.html").is_file()
    assert (target / "submissions" / "a" / "one" / "index.html").is_file()
    assert (target / "submissions" / "a" / "one" / "Observation-a.json.html").is_file()
    index = (target / "index.html").read_text(encoding="utf-8")
    assert "submissions/a/one/index.html" in index
    assert "assets/style.css" in index


def test_job_summary_reports_a_crash(cfg):
    run = make_run(make_submission())
    from tools.results import GroupResult

    run.groups = [
        GroupResult(
            index=1, fhirVersion="4.0.1", igs=[], files=[], crashed=True, reason="out of memory",
            logTail=["Error occurred during initialization of VM"],
        )
    ]
    summary = render_job_summary(cfg, run, {})
    assert "crashed" in summary
    assert "out of memory" in summary
    assert "initialization of VM" in summary
