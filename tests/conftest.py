"""Shared fixtures: a throwaway repository with the real config and schemas."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

MINIMAL_OBSERVATION = {
    "resourceType": "Observation",
    "id": "example-1",
    "meta": {
        "profile": ["http://hl7.org/fhir/StructureDefinition/Observation"],
        "security": [
            {"system": "http://terminology.hl7.org/CodeSystem/v3-ActReason", "code": "HTEST"}
        ],
    },
    "status": "final",
    "code": {
        "coding": [
            {"system": "http://loinc.org", "code": "4548-4", "display": "Hemoglobin A1c"}
        ]
    },
    "subject": {"reference": "Patient/example-patient"},
    "effectiveDateTime": "2026-01-15T09:00:00+01:00",
    "valueQuantity": {
        "value": 5.4,
        "unit": "%",
        "system": "http://unitsofmeasure.org",
        "code": "%",
    },
}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """An empty collection with the production config and schemas."""
    shutil.copy(REPO_ROOT / "validation.config.yaml", tmp_path / "validation.config.yaml")
    shutil.copytree(REPO_ROOT / "schema", tmp_path / "schema")
    (tmp_path / "examples").mkdir()
    return tmp_path


@pytest.fixture
def make_submission(repo: Path):
    """Create examples/<contributor>/<slug> with metadata, README and a resource."""

    def _make(
        contributor: str = "someone",
        slug: str = "example-submission",
        metadata: str = "title: An example submission\norigin: synthetic\n",
        contributor_yaml: str = "name: Some One\n",
        resource: dict | str | None = None,
        resource_name: str = "Observation-example.json",
        readme: str | None = "# An example submission\n",
    ) -> Path:
        contributor_dir = repo / "examples" / contributor
        contributor_dir.mkdir(parents=True, exist_ok=True)
        (contributor_dir / "contributor.yaml").write_text(contributor_yaml, encoding="utf-8")
        submission_dir = contributor_dir / slug
        submission_dir.mkdir(parents=True, exist_ok=True)
        (submission_dir / "metadata.yaml").write_text(metadata, encoding="utf-8")
        if readme is not None:
            (submission_dir / "README.md").write_text(readme, encoding="utf-8")
        if resource is None:
            resource = MINIMAL_OBSERVATION
        body = resource if isinstance(resource, str) else json.dumps(resource, indent=2)
        (submission_dir / resource_name).write_text(body, encoding="utf-8")
        return submission_dir

    return _make


@pytest.fixture
def cfg(repo: Path):
    from tools.config import load_config

    return load_config(repo)
