"""Parsing the validator output, attributing it and building the command line."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.discover import discover
from tools.metadata import load_all
from tools.validator import attribute, build_command, build_groups, parse_output, tail

EXT = "http://hl7.org/fhir/StructureDefinition"


def outcome(file_path: str, issues: list[dict]) -> dict:
    return {
        "resourceType": "OperationOutcome",
        "extension": [{"url": f"{EXT}/operationoutcome-file", "valueString": file_path}],
        "issue": issues,
    }


def issue(severity: str, message_id: str, expression: str, text: str, line: int = 7) -> dict:
    return {
        "severity": severity,
        "code": "processing",
        "details": {"text": text},
        "expression": [expression],
        "extension": [
            {"url": f"{EXT}/operationoutcome-message-id", "valueString": message_id},
            {"url": f"{EXT}/operationoutcome-issue-line", "valueInteger": line},
            {"url": f"{EXT}/operationoutcome-issue-col", "valueInteger": 3},
            {"url": f"{EXT}/operationoutcome-issue-source", "valueString": "InstanceValidator"},
        ],
    }


def test_parse_bundle_of_outcomes(tmp_path: Path):
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {"resource": outcome("/abs/a.json", [issue("error", "ID_ONE", "Observation.status", "boom")])},
            {"resource": outcome("/abs/b.json", [])},
        ],
    }
    path = tmp_path / "group-1.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    parsed = parse_output(path)
    assert [source for source, _ in parsed] == ["/abs/a.json", "/abs/b.json"]
    first = parsed[0][1][0]
    assert first.severity == "error"
    assert first.messageId == "ID_ONE"
    assert first.line == 7 and first.col == 3
    assert first.location == "Observation.status"
    assert first.source == "InstanceValidator"


def test_parse_single_outcome(tmp_path: Path):
    path = tmp_path / "single.json"
    path.write_text(
        json.dumps(outcome("/abs/a.json", [issue("warning", "W", "Observation", "hm")])),
        encoding="utf-8",
    )
    parsed = parse_output(path)
    assert len(parsed) == 1
    assert parsed[0][1][0].severity == "warning"


def test_parse_rejects_other_resources(tmp_path: Path):
    path = tmp_path / "nope.json"
    path.write_text(json.dumps({"resourceType": "Patient"}), encoding="utf-8")
    with pytest.raises(ValueError):
        parse_output(path)


def test_attribution_by_absolute_path(tmp_path: Path):
    first = tmp_path / "Observation-a.json"
    second = tmp_path / "Observation-b.json"
    first.write_text("{}", encoding="utf-8")
    second.write_text("{}", encoding="utf-8")
    parsed = [
        (str(second.resolve()), [issue("error", "E", "Observation", "second")]),
        (str(first.resolve()), [issue("warning", "W", "Observation", "first")]),
    ]
    parsed = [(source, parse_issue_list(issues)) for source, issues in parsed]
    attributed, leftovers = attribute(parsed, [first, second])
    assert not leftovers
    assert attributed[first][0].severity == "warning"
    assert attributed[second][0].severity == "error"


def parse_issue_list(issues: list[dict]):
    from tools.validator import _issue_from

    return [_issue_from(i) for i in issues]


def test_attribution_falls_back_to_a_suffix_match(tmp_path: Path):
    target = tmp_path / "Observation-a.json"
    target.write_text("{}", encoding="utf-8")
    parsed = [("Observation-a.json", parse_issue_list([issue("error", "E", "Observation", "x")]))]
    attributed, leftovers = attribute(parsed, [target])
    assert not leftovers
    assert target in attributed


def test_unattributable_outcomes_are_kept(tmp_path: Path):
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    for path in (first, second):
        path.write_text("{}", encoding="utf-8")
    parsed = [
        ("/somewhere/else.json", parse_issue_list([issue("error", "E", "Observation", "x")])),
        (str(first.resolve()), []),
    ]
    attributed, leftovers = attribute(parsed, [first, second])
    assert len(leftovers) == 1
    assert second not in attributed


def test_grouping_and_command(cfg, make_submission):
    make_submission(slug="one")
    make_submission(slug="two", metadata="title: Two\norigin: synthetic\nigs:\n  - hl7.fhir.eu.laboratory#2.0.0\n")
    submissions = discover(cfg)
    load_all(cfg, submissions)
    groups = build_groups(cfg, submissions)
    assert len(groups) == 2

    plain = [g for g in groups if "hl7.fhir.eu.laboratory#2.0.0" not in g.igs][0]
    command = build_command(cfg, plain, Path("/out.json"), Path("/out.html"))
    assert command[0] == "java"
    assert "-Xmx4g" in command
    assert command[command.index("-version") + 1] == "4.0.1"
    assert "hl7.fhir.uv.ips#2.0.1" in command
    assert command[command.index("-tx") + 1] == "https://tx.fhir.org"
    assert "-show-message-ids" in command
    assert command[-1].startswith("/")  # absolute source paths


def test_offline_command_has_no_terminology_server(cfg, make_submission):
    make_submission()
    submissions = discover(cfg)
    load_all(cfg, submissions)
    group = build_groups(cfg, submissions)[0]
    command = build_command(cfg, group, Path("/out.json"), Path("/out.html"), offline=True)
    assert command[command.index("-tx") + 1] == "n/a"
    assert "-txCache" not in command


def test_tail_returns_the_last_lines(tmp_path: Path):
    log = tmp_path / "log.txt"
    log.write_text("\n".join(str(n) for n in range(100)), encoding="utf-8")
    assert tail(log, 5) == ["95", "96", "97", "98", "99"]
    assert tail(tmp_path / "missing.txt", 5) == []
