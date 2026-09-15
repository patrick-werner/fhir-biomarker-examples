"""Defaulting of metadata and reading of FHIR resources."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import fhir
from tools.config import ConfigError
from tools.discover import discover, find_submission
from tools.metadata import MetadataError, effective_igs, load_all, load_yaml, resolve

XML_OBSERVATION = """<?xml version="1.0" encoding="UTF-8"?>
<Observation xmlns="http://hl7.org/fhir">
  <id value="xml-1"/>
  <meta><profile value="http://example.org/StructureDefinition/x"/></meta>
  <status value="final"/>
  <category><coding><system value="http://terminology.hl7.org/CodeSystem/observation-category"/><code value="laboratory"/></coding></category>
  <code><coding><system value="http://loinc.org"/><code value="2160-0"/><display value="Creatinine"/></coding></code>
  <valueQuantity><value value="1.1"/><unit value="mg/dL"/><code value="mg/dL"/></valueQuantity>
  <referenceRange><low><value value="0.6"/></low></referenceRange>
</Observation>
"""


def test_defaults_are_applied(cfg, make_submission):
    make_submission()
    submissions = discover(cfg)
    load_all(cfg, submissions)
    resolved = resolve(submissions[0], cfg)
    assert resolved.fhirVersion == "4.0.1"
    assert resolved.category == "other"
    assert resolved.custodian["name"] == "Some One"
    assert resolved.igs == ("hl7.fhir.uv.genomics-reporting#3.0.0",)


def test_biomarkers_are_derived_from_the_resource(cfg, make_submission):
    make_submission()
    submissions = discover(cfg)
    load_all(cfg, submissions)
    resolved = resolve(submissions[0], cfg)
    assert resolved.derivedBiomarkers
    assert resolved.biomarkers == [
        {"name": "Hemoglobin A1c", "system": "http://loinc.org", "code": "4548-4"}
    ]


def test_declared_biomarkers_win(cfg, make_submission):
    make_submission(
        metadata="title: T\norigin: synthetic\nbiomarkers:\n  - name: HbA1c\n    system: http://loinc.org\n    code: 4548-4\n"
    )
    submissions = discover(cfg)
    load_all(cfg, submissions)
    resolved = resolve(submissions[0], cfg)
    assert not resolved.derivedBiomarkers
    assert resolved.biomarkers[0]["name"] == "HbA1c"


def test_custodian_overrides_the_contributor(cfg, make_submission):
    make_submission(
        metadata="title: T\norigin: synthetic\ncustodian:\n  name: Someone Else\n  github: else\n"
    )
    submissions = discover(cfg)
    load_all(cfg, submissions)
    assert resolve(submissions[0], cfg).custodian["name"] == "Someone Else"


def test_effective_igs_merge_and_deduplicate(cfg, make_submission):
    make_submission(
        metadata=(
            "title: T\norigin: synthetic\nigs:\n"
            "  - hl7.fhir.uv.ips#2.0.1\n"
            "  - hl7.fhir.uv.genomics-reporting#3.0.0\n"  # already a default
            "  - hl7.fhir.eu.laboratory#2.0.0\n"
        )
    )
    submissions = discover(cfg)
    load_all(cfg, submissions)
    assert effective_igs(submissions[0], cfg) == (
        "hl7.fhir.eu.laboratory#2.0.0",
        "hl7.fhir.uv.genomics-reporting#3.0.0",
        "hl7.fhir.uv.ips#2.0.1",
    )


def test_floating_ig_is_rejected(cfg, make_submission):
    make_submission(metadata="title: T\norigin: synthetic\nigs:\n  - some.package#current\n")
    submissions = discover(cfg)
    load_all(cfg, submissions)
    with pytest.raises(ConfigError):
        effective_igs(submissions[0], cfg)


def test_find_submission_by_id_and_by_path(cfg, make_submission):
    directory = make_submission(contributor="alice", slug="one")
    assert find_submission(cfg, "alice/one").id == "alice/one"
    assert find_submission(cfg, str(directory)).id == "alice/one"
    assert find_submission(cfg, str(directory / "Observation-example.json")).id == "alice/one"
    assert find_submission(cfg, "nobody/nothing") is None


def test_duplicate_keys_are_rejected(tmp_path: Path):
    path = tmp_path / "metadata.yaml"
    path.write_text("title: One\ntitle: Two\n", encoding="utf-8")
    with pytest.raises(MetadataError, match="duplicate key"):
        load_yaml(path)


def test_empty_file_is_rejected(tmp_path: Path):
    path = tmp_path / "metadata.yaml"
    path.write_text("\n", encoding="utf-8")
    with pytest.raises(MetadataError, match="empty"):
        load_yaml(path)


def test_xml_resource_is_read_like_json(tmp_path: Path):
    path = tmp_path / "Observation-xml.xml"
    path.write_text(XML_OBSERVATION, encoding="utf-8")
    resource = fhir.load_resource(path)
    assert resource["resourceType"] == "Observation"
    assert resource["status"] == "final"
    assert fhir.profiles(resource) == ["http://example.org/StructureDefinition/x"]
    summary = fhir.summarize_observation(resource)
    assert summary.code[0]["code"] == "2160-0"
    assert summary.value_type == "Quantity"
    assert summary.unit == "mg/dL"
    assert summary.has_reference_range is True
    assert summary.has_interpretation is False


def test_bundle_entries_and_contained_are_walked(tmp_path: Path):
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "outer",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "1"}]},
                    "contained": [
                        {
                            "resourceType": "Observation",
                            "id": "inner",
                            "code": {"coding": [{"system": "http://loinc.org", "code": "2"}]},
                        }
                    ],
                }
            }
        ],
    }
    path = tmp_path / "Bundle-x.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    resource = fhir.load_resource(path)
    codes = [
        coding["code"]
        for observation in fhir.iter_observations(resource)
        for coding in fhir.observation_codings(observation)
    ]
    assert sorted(codes) == ["1", "2"]


def test_component_and_category_summary():
    resource = {
        "resourceType": "Observation",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory"}]}],
        "code": {"coding": [{"system": "http://loinc.org", "code": "18474-7"}]},
        "valueCodeableConcept": {"text": "HER2 positive"},
        "method": {"text": "IHC"},
        "specimen": {"display": "Biopsy"},
        "component": [
            {"code": {"coding": [{"system": "http://loinc.org", "code": "48018-6"}]}},
            {"code": {"text": "IHC score"}, "valueString": "3+"},
        ],
    }
    summary = fhir.summarize_observation(resource)
    assert summary.value_type == "CodeableConcept"
    assert summary.value_text == "HER2 positive"
    assert summary.component_codes == ["loinc.org|48018-6", "text:IHC score"]
    assert summary.category_codes == ["observation-category|laboratory"]
    assert summary.method == "IHC"
    assert summary.specimen == "Biopsy"


def test_broken_files_raise(tmp_path: Path):
    bad_json = tmp_path / "a.json"
    bad_json.write_text("{", encoding="utf-8")
    with pytest.raises(fhir.ResourceError, match="invalid JSON"):
        fhir.load_resource(bad_json)
    bad_xml = tmp_path / "a.xml"
    bad_xml.write_text("<Observation>", encoding="utf-8")
    with pytest.raises(fhir.ResourceError, match="invalid XML"):
        fhir.load_resource(bad_xml)
