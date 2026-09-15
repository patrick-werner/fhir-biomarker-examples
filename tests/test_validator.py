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
    assert "hl7.fhir.uv.genomics-reporting#3.0.0" in command
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


# ------------------------------------------------------------ terminology retries


def test_terminology_failure_detection(tmp_path: Path):
    from tools.validator import terminology_failure

    log = tmp_path / "group-1.log"
    assert terminology_failure(log) is False  # no log at all
    log.write_text("Loading\n  Loading FHIR v4.0.1\n", encoding="utf-8")
    assert terminology_failure(log) is False
    log.write_text(
        "org.hl7.fhir.exceptions.FHIRException: Unable to connect to terminology server "
        "at https://tx.fhir.org. Use parameter '-tx n/a' ...\n",
        encoding="utf-8",
    )
    assert terminology_failure(log) is True


def _fake_run_group(calls: list[bool], log_text_when_online: str, crash_online: bool):
    from tools.results import GroupResult

    def fake(cfg_, group_, out_dir_, offline=False):
        calls.append(offline)
        raw = out_dir_ / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        log = raw / f"group-{group_.index}.log"
        result = GroupResult(
            index=group_.index,
            fhirVersion=group_.fhirVersion,
            igs=list(group_.igs),
            files=[str(p) for p in group_.files],
        )
        if offline or not crash_online:
            log.write_text("done\n", encoding="utf-8")
            result.exitCode = 0
        else:
            log.write_text(log_text_when_online, encoding="utf-8")
            result.crashed = True
            result.exitCode = 1
            result.reason = "the validator exited with code 1 and produced no output file"
        return result

    return fake


def test_terminology_crash_is_retried_then_validated_offline(
    cfg, make_submission, monkeypatch, tmp_path: Path
):
    from tools import validator

    make_submission()
    submissions = discover(cfg)
    load_all(cfg, submissions)
    group = build_groups(cfg, submissions)[0]
    calls: list[bool] = []
    monkeypatch.setattr(
        validator,
        "run_group",
        _fake_run_group(calls, "Unable to connect to terminology server at x\n", True),
    )
    monkeypatch.setattr(validator, "_sleep", lambda seconds: None)

    result = validator.run_group_with_retries(cfg, group, tmp_path / "results")

    # first attempt + retries from the config + one offline run
    assert calls == [False] * (1 + cfg.terminology.retries) + [True]
    assert result.crashed is False
    assert result.terminologyFallback is True
    assert result.attempts == len(calls)
    kept = sorted(p.name for p in (tmp_path / "results" / "raw").glob("group-1.attempt-*.log"))
    assert kept == [f"group-1.attempt-{n}.log" for n in range(1, len(calls))]


def test_other_crashes_are_not_retried(cfg, make_submission, monkeypatch, tmp_path: Path):
    from tools import validator

    make_submission()
    submissions = discover(cfg)
    load_all(cfg, submissions)
    group = build_groups(cfg, submissions)[0]
    calls: list[bool] = []
    monkeypatch.setattr(
        validator, "run_group", _fake_run_group(calls, "java.lang.OutOfMemoryError\n", True)
    )
    monkeypatch.setattr(validator, "_sleep", lambda seconds: None)

    result = validator.run_group_with_retries(cfg, group, tmp_path / "results")

    assert calls == [False]
    assert result.crashed is True
    assert result.terminologyFallback is False
    assert result.attempts == 1


def test_no_offline_fallback_when_disabled(cfg, make_submission, monkeypatch, tmp_path: Path):
    import dataclasses

    from tools import validator

    cfg = dataclasses.replace(
        cfg, terminology=dataclasses.replace(cfg.terminology, fallbackToOffline=False)
    )
    make_submission()
    submissions = discover(cfg)
    load_all(cfg, submissions)
    group = build_groups(cfg, submissions)[0]
    calls: list[bool] = []
    monkeypatch.setattr(
        validator,
        "run_group",
        _fake_run_group(calls, "Error fetching the server's capability statement: timeout\n", True),
    )
    monkeypatch.setattr(validator, "_sleep", lambda seconds: None)

    result = validator.run_group_with_retries(cfg, group, tmp_path / "results")

    assert calls == [False] * (1 + cfg.terminology.retries)
    assert result.crashed is True
    assert result.terminologyFallback is False


# ------------------------------------------------------------- output streaming


def _group_for(cfg, make_submission):
    make_submission()
    submissions = discover(cfg)
    load_all(cfg, submissions)
    return build_groups(cfg, submissions)[0]


def _fake_validator(monkeypatch, script: str) -> None:
    import sys

    from tools import validator

    monkeypatch.setattr(
        validator,
        "build_command",
        lambda cfg_, group_, out_json, out_html, offline=False: [sys.executable, "-c", script],
    )


def test_run_group_streams_output_to_stdout_and_log(
    cfg, make_submission, monkeypatch, tmp_path: Path, capsys
):
    from tools import validator

    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    group = _group_for(cfg, make_submission)
    _fake_validator(
        monkeypatch,
        "import sys; print('Loading'); print('  Loading FHIR v4.0.1'); "
        "sys.stderr.write('stderr line\\n')",
    )

    result = validator.run_group(cfg, group, tmp_path / "results")

    out = capsys.readouterr().out
    assert "Loading FHIR v4.0.1" in out
    assert "stderr line" in out
    assert "::group::" not in out
    log = (tmp_path / "results" / "raw" / "group-1.log").read_text(encoding="utf-8")
    assert "Loading FHIR v4.0.1" in log
    assert "stderr line" in log
    assert result.exitCode == 0
    assert result.crashed is True  # the fake wrote no output file
    assert "produced no output file" in result.reason


def test_run_group_wraps_output_in_a_group_on_github_actions(
    cfg, make_submission, monkeypatch, tmp_path: Path, capsys
):
    from tools import validator

    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    group = _group_for(cfg, make_submission)
    _fake_validator(monkeypatch, "print('validator says hello')")

    validator.run_group(cfg, group, tmp_path / "results")

    lines = capsys.readouterr().out.splitlines()
    assert "::group::validator output, group 1" in lines
    assert lines.index("::group::validator output, group 1") < lines.index("validator says hello")
    assert lines.index("validator says hello") < lines.index("::endgroup::")


def test_run_group_kills_a_hanging_validator(cfg, make_submission, monkeypatch, tmp_path: Path):
    import dataclasses

    from tools import validator

    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    cfg = dataclasses.replace(
        cfg, validator=dataclasses.replace(cfg.validator, timeoutMinutes=0.02)
    )  # 1.2 seconds
    group = _group_for(cfg, make_submission)
    _fake_validator(monkeypatch, "import time; print('started', flush=True); time.sleep(60)")

    result = validator.run_group(cfg, group, tmp_path / "results")

    assert result.crashed is True
    assert "did not finish within" in result.reason
    assert result.durationSeconds < 15
    assert "started" in (tmp_path / "results" / "raw" / "group-1.log").read_text(encoding="utf-8")
