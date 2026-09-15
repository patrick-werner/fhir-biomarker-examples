"""Strict YAML loading, JSON-Schema validation and defaulting of metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from . import fhir
from .config import Config, check_ig_pinned, ConfigError
from .discover import Submission


class MetadataError(Exception):
    """Raised when a metadata or contributor file cannot be read."""


class _StrictLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys."""


def _no_duplicates(loader: yaml.Loader, node: yaml.MappingNode, deep: bool = False) -> dict[str, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            mark = key_node.start_mark
            raise MetadataError(f"duplicate key {key!r} at line {mark.line + 1}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates)


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise MetadataError(f"cannot read file: {exc}") from exc
    try:
        data = yaml.load(text, Loader=_StrictLoader)
    except yaml.YAMLError as exc:
        raise MetadataError(f"not valid YAML: {exc}") from exc
    if data is None:
        raise MetadataError("file is empty")
    if not isinstance(data, dict):
        raise MetadataError("top level value must be a mapping of fields")
    return data


@lru_cache(maxsize=8)
def _schema(path_str: str) -> Draft202012Validator:
    schema = json.loads(Path(path_str).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def schema_errors(cfg: Config, data: dict[str, Any], schema_name: str) -> list[str]:
    """Return readable messages for every schema violation, sorted by path."""
    validator = _schema(str(cfg.schema_dir / schema_name))
    messages: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        location = ".".join(str(p) for p in error.absolute_path)
        prefix = f"{location}: " if location else ""
        messages.append(f"{prefix}{_readable(error)}")
    return messages


def _readable(error: Any) -> str:
    """A raw regex helps nobody; the schema's own description does."""
    description = error.schema.get("description") if isinstance(error.schema, dict) else None
    if error.validator == "pattern" and description:
        return f"{error.instance!r} is not valid here. {description}"
    return error.message


@dataclass
class ResolvedMetadata:
    title: str
    origin: str
    description: str | None
    fhirVersion: str
    igs: tuple[str, ...]
    category: str
    biomarkers: list[dict[str, str]]
    custodian: dict[str, str]
    source: dict[str, str]
    knownIssues: list[dict[str, str]]
    review: dict[str, Any]
    derivedBiomarkers: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "origin": self.origin,
            "description": self.description,
            "fhirVersion": self.fhirVersion,
            "igs": list(self.igs),
            "category": self.category,
            "biomarkers": self.biomarkers,
            "custodian": self.custodian,
            "source": self.source,
            "knownIssues": self.knownIssues,
            "review": self.review,
            "derivedBiomarkers": self.derivedBiomarkers,
        }


def effective_igs(sub: Submission, cfg: Config) -> tuple[str, ...]:
    """Default IGs of the submission's FHIR version plus its own, deduplicated."""
    version = str(sub.metadata.get("fhirVersion") or cfg.defaultFhirVersion)
    own = [str(ig) for ig in sub.metadata.get("igs") or []]
    for ig in own:
        check_ig_pinned(ig, f"{sub.id}: metadata.igs")
    return tuple(sorted(set(cfg.default_igs_for(version)) | set(own)))


def derive_biomarkers(sub: Submission) -> list[dict[str, str]]:
    """Biomarker names and codes taken from Observation.code of all resources."""
    seen: dict[tuple[str, str], dict[str, str]] = {}
    for path in sub.fhir_files:
        try:
            resource = fhir.load_resource(path)
        except fhir.ResourceError:
            continue
        for observation in fhir.iter_observations(resource):
            concept = observation.get("code")
            text = concept.get("text") if isinstance(concept, dict) else None
            for coding in fhir.observation_codings(observation):
                key = (coding.get("system", ""), coding.get("code", ""))
                if key in seen:
                    continue
                name = coding.get("display") or text or coding.get("code") or ""
                seen[key] = {
                    "name": str(name),
                    "system": coding.get("system", ""),
                    "code": coding.get("code", ""),
                }
    return [seen[key] for key in sorted(seen)]


def _normalise_biomarkers(raw: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for item in raw or []:
        if isinstance(item, str):
            out.append({"name": item, "system": "", "code": ""})
        elif isinstance(item, dict):
            out.append(
                {
                    "name": str(item.get("name", "")),
                    "system": str(item.get("system", "")),
                    "code": str(item.get("code", "")),
                }
            )
    return out


def resolve(sub: Submission, cfg: Config) -> ResolvedMetadata:
    """Apply every default so that the rest of the tooling sees complete data."""
    md = sub.metadata or {}
    contributor = sub.contributor or {}
    custodian_raw = md.get("custodian") or {}
    custodian = {
        "name": str(custodian_raw.get("name") or contributor.get("name") or sub.contributor_slug),
        "github": str(custodian_raw.get("github") or contributor.get("github") or ""),
        "contact": str(custodian_raw.get("contact") or contributor.get("contact") or ""),
    }
    declared = _normalise_biomarkers(md.get("biomarkers"))
    derived = False
    if not declared:
        declared = derive_biomarkers(sub)
        derived = True
    source_raw = md.get("source") or {}
    return ResolvedMetadata(
        title=str(md.get("title", sub.slug)),
        origin=str(md.get("origin", "synthetic")),
        description=(str(md["description"]) if md.get("description") else None),
        fhirVersion=str(md.get("fhirVersion") or cfg.defaultFhirVersion),
        igs=effective_igs(sub, cfg),
        category=str(md.get("category") or "other"),
        biomarkers=declared,
        custodian=custodian,
        source={k: str(v) for k, v in source_raw.items()},
        knownIssues=[dict(rule) for rule in md.get("knownIssues") or []],
        review=dict(md.get("review") or {}),
        derivedBiomarkers=derived,
    )


def load_submission_metadata(sub: Submission, cfg: Config) -> list[str]:
    """Populate sub.metadata / sub.contributor. Returns blocking error messages."""
    errors: list[str] = []
    try:
        sub.contributor = load_yaml(sub.contributor_path)
    except MetadataError as exc:
        errors.append(f"{sub.contributor_path.name}: {exc}")
        sub.contributor = {}
    try:
        sub.metadata = load_yaml(sub.metadata_path)
    except MetadataError as exc:
        errors.append(f"{sub.metadata_path.name}: {exc}")
        sub.metadata = {}
    return errors


def load_all(cfg: Config, submissions: list[Submission]) -> None:
    """Best-effort metadata loading used by validate/report after check passed."""
    for sub in submissions:
        try:
            sub.contributor = load_yaml(sub.contributor_path)
        except MetadataError:
            sub.contributor = {}
        try:
            sub.metadata = load_yaml(sub.metadata_path)
        except MetadataError:
            sub.metadata = {}


def all_effective_igs(cfg: Config, submissions: list[Submission]) -> list[str]:
    igs: set[str] = set()
    for sub in submissions:
        try:
            igs.update(effective_igs(sub, cfg))
        except ConfigError:
            continue
    return sorted(igs)
