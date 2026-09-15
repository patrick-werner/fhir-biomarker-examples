"""The structural gate: what blocks a pull request and what only warns."""

from __future__ import annotations

from pathlib import Path

from tools.check import run_check


def errors(result) -> list[str]:
    return [f.message for f in result.errors]


def test_minimal_submission_passes(cfg, make_submission):
    make_submission()
    result = run_check(cfg)
    assert result.ok, errors(result)
    assert len(result.submissions) == 1


def test_missing_title_blocks(cfg, make_submission):
    make_submission(metadata="origin: synthetic\n")
    result = run_check(cfg)
    assert not result.ok
    assert any("'title' is a required property" in message for message in errors(result))


def test_unknown_key_blocks(cfg, make_submission):
    make_submission(metadata="title: An example\norigin: synthetic\nfoo: bar\n")
    result = run_check(cfg)
    assert not result.ok
    assert any("Additional properties are not allowed" in message for message in errors(result))


def test_floating_ig_version_blocks(cfg, make_submission):
    make_submission(
        metadata="title: An example\norigin: synthetic\nigs:\n  - hl7.fhir.eu.laboratory#current\n"
    )
    result = run_check(cfg)
    assert not result.ok
    assert any("hl7.fhir.eu.laboratory#current" in message for message in errors(result))


def test_pinned_ig_version_passes(cfg, make_submission):
    make_submission(
        metadata="title: An example\norigin: synthetic\nigs:\n  - hl7.fhir.eu.laboratory#2.0.0\n"
    )
    assert run_check(cfg).ok


def test_stray_file_blocks(cfg, make_submission):
    submission = make_submission()
    (submission / "notes.txt").write_text("hello", encoding="utf-8")
    result = run_check(cfg)
    assert not result.ok
    assert any("file type not allowed" in message for message in errors(result))


def test_subfolder_blocks(cfg, make_submission):
    submission = make_submission()
    (submission / "extra").mkdir()
    (submission / "extra" / "Observation-more.json").write_text("{}", encoding="utf-8")
    result = run_check(cfg)
    assert not result.ok
    assert any("Subfolders" in m or "subfolders" in m for m in errors(result))


def test_broken_json_blocks(cfg, make_submission):
    make_submission(resource='{"resourceType": "Observation",}')
    result = run_check(cfg)
    assert not result.ok
    assert any("invalid JSON" in message for message in errors(result))


def test_resource_without_resource_type_blocks(cfg, make_submission):
    make_submission(resource={"id": "x"})
    result = run_check(cfg)
    assert not result.ok
    assert any("resourceType" in message for message in errors(result))


def test_missing_fhir_file_blocks(cfg, repo: Path, make_submission):
    submission = make_submission()
    (submission / "Observation-example.json").unlink()
    result = run_check(cfg)
    assert not result.ok
    assert any("no FHIR file" in message for message in errors(result))


def test_missing_contributor_yaml_blocks(cfg, make_submission):
    submission = make_submission()
    (submission.parent / "contributor.yaml").unlink()
    result = run_check(cfg)
    assert not result.ok
    assert any("contributor.yaml is missing" in message for message in errors(result))


def test_contributor_without_name_blocks(cfg, make_submission):
    make_submission(contributor_yaml="github: someone\n")
    result = run_check(cfg)
    assert not result.ok
    assert any("'name' is a required property" in message for message in errors(result))


def test_duplicate_yaml_key_blocks(cfg, make_submission):
    make_submission(metadata="title: One\ntitle: Two\norigin: synthetic\n")
    result = run_check(cfg)
    assert not result.ok
    assert any("duplicate key" in message for message in errors(result))


def test_known_issue_file_must_exist(cfg, make_submission):
    make_submission(
        metadata=(
            "title: An example\norigin: synthetic\n"
            "knownIssues:\n"
            "  - file: Observation-missing.json\n"
            "    justification: This file does not exist at all.\n"
        )
    )
    result = run_check(cfg)
    assert not result.ok
    assert any("is not a file of this submission" in message for message in errors(result))


def test_known_issue_requires_justification(cfg, make_submission):
    make_submission(
        metadata=("title: An example\norigin: synthetic\nknownIssues:\n  - messageId: SOME_ID\n")
    )
    result = run_check(cfg)
    assert not result.ok
    assert any("justification" in message for message in errors(result))


def test_missing_readme_only_warns(cfg, make_submission):
    make_submission(readme=None)
    result = run_check(cfg)
    assert result.ok
    assert any("README.md is missing" in f.message for f in result.warnings)


def test_missing_profile_only_warns(cfg, make_submission):
    make_submission(
        resource={
            "resourceType": "Observation",
            "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": "2160-0"}]},
        }
    )
    result = run_check(cfg)
    assert result.ok
    assert any("meta.profile" in f.message for f in result.warnings)


def test_template_folder_is_ignored(cfg, repo: Path, make_submission):
    make_submission()
    template = repo / "examples" / "_template" / "broken"
    template.mkdir(parents=True)
    (template / "not-allowed.txt").write_text("x", encoding="utf-8")
    result = run_check(cfg)
    assert result.ok, errors(result)
    assert len(result.submissions) == 1


def test_bad_slug_blocks(cfg, make_submission):
    make_submission(slug="Not_A_Slug")
    result = run_check(cfg)
    assert not result.ok
    assert any("does not match" in message for message in errors(result))


def test_check_can_be_narrowed_to_changed_submissions(cfg, make_submission):
    make_submission(slug="good-one")
    make_submission(slug="bad-one", metadata="origin: synthetic\n")
    assert not run_check(cfg).ok
    assert run_check(cfg, only_ids=["someone/good-one"]).ok


def test_xml_resource_is_accepted(cfg, make_submission):
    make_submission(
        resource_name="Observation-example.xml",
        resource=(
            '<Observation xmlns="http://hl7.org/fhir">'
            '<id value="x"/><status value="final"/>'
            '<code><coding><system value="http://loinc.org"/><code value="2160-0"/></coding></code>'
            "</Observation>"
        ),
    )
    result = run_check(cfg)
    assert result.ok, errors(result)
