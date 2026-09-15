"""Minimal reading and summarising of FHIR resources (JSON and XML)."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

FHIR_NS = "http://hl7.org/fhir"
_PRIMITIVE_HOLDER = "value"


class ResourceError(Exception):
    """Raised when a file cannot be read as a FHIR resource."""


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def xml_to_dict(element: ET.Element) -> Any:
    """Convert FHIR XML to the JSON object model (good enough for summaries)."""
    node: dict[str, Any] = {}
    value = element.get(_PRIMITIVE_HOLDER)
    if value is not None:
        # A primitive element; may still carry id/extension children.
        if len(element) == 0:
            return value
        node[_PRIMITIVE_HOLDER] = value
    for child in element:
        name = _localname(child.tag)
        if name == "div":
            continue
        converted = xml_to_dict(child)
        if name in node:
            existing = node[name]
            if isinstance(existing, list):
                existing.append(converted)
            else:
                node[name] = [existing, converted]
        else:
            node[name] = converted
    if _PRIMITIVE_HOLDER in node and len(node) == 1:
        return node[_PRIMITIVE_HOLDER]
    return node


def _normalise_repeats(node: Any) -> Any:
    """XML has no arrays; single occurrences stay scalars. Callers use as_list()."""
    return node


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_resource(path: Path) -> dict[str, Any]:
    """Read one FHIR resource file. Raises ResourceError on any problem."""
    suffix = path.suffix.lower()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ResourceError(f"cannot read file: {exc}") from exc
    if suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ResourceError(f"invalid JSON: line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise ResourceError("top level JSON value is not an object")
        return data
    if suffix == ".xml":
        try:
            root = ET.fromstring(text)
        except ET.ParseError as exc:
            raise ResourceError(f"invalid XML: {exc}") from exc
        data = xml_to_dict(root)
        if not isinstance(data, dict):
            raise ResourceError("top level XML element has no content")
        data["resourceType"] = _localname(root.tag)
        return _normalise_repeats(data)
    raise ResourceError(f"unsupported file extension {suffix!r}")


def resource_type(resource: dict[str, Any]) -> str | None:
    value = resource.get("resourceType")
    return value if isinstance(value, str) else None


def iter_resources(resource: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield the root resource, Bundle entries and contained resources."""
    if not isinstance(resource, dict):
        return
    yield resource
    for contained in as_list(resource.get("contained")):
        if isinstance(contained, dict):
            yield from iter_resources(contained)
    for entry in as_list(resource.get("entry")):
        if isinstance(entry, dict) and isinstance(entry.get("resource"), dict):
            yield from iter_resources(entry["resource"])


def profiles(resource: dict[str, Any]) -> list[str]:
    meta = resource.get("meta")
    if not isinstance(meta, dict):
        return []
    return [p for p in as_list(meta.get("profile")) if isinstance(p, str)]


def codings(concept: Any) -> list[dict[str, str]]:
    if not isinstance(concept, dict):
        return []
    out: list[dict[str, str]] = []
    for coding in as_list(concept.get("coding")):
        if not isinstance(coding, dict):
            continue
        entry = {
            "system": str(coding.get("system")) if coding.get("system") is not None else "",
            "code": str(coding.get("code")) if coding.get("code") is not None else "",
            "display": str(coding.get("display")) if coding.get("display") is not None else "",
        }
        if entry["code"] or entry["system"]:
            out.append(entry)
    return out


def observation_codings(resource: dict[str, Any]) -> list[dict[str, str]]:
    return codings(resource.get("code"))


VALUE_PREFIX = "value"
_VALUE_SUFFIXES = (
    "Quantity",
    "CodeableConcept",
    "String",
    "Boolean",
    "Integer",
    "Range",
    "Ratio",
    "SampledData",
    "Time",
    "DateTime",
    "Period",
)


def value_type(resource: dict[str, Any]) -> str | None:
    for suffix in _VALUE_SUFFIXES:
        if f"{VALUE_PREFIX}{suffix}" in resource:
            return suffix
    return None


@dataclass
class ObsSummary:
    resource_id: str | None
    resource_type: str
    profiles: list[str] = field(default_factory=list)
    code: list[dict[str, str]] = field(default_factory=list)
    code_text: str | None = None
    value_type: str | None = None
    value_text: str | None = None
    unit: str | None = None
    component_codes: list[str] = field(default_factory=list)
    category_codes: list[str] = field(default_factory=list)
    has_interpretation: bool = False
    has_reference_range: bool = False
    method: str | None = None
    specimen: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "resourceId": self.resource_id,
            "resourceType": self.resource_type,
            "profiles": self.profiles,
            "code": self.code,
            "codeText": self.code_text,
            "valueType": self.value_type,
            "valueText": self.value_text,
            "unit": self.unit,
            "componentCodes": self.component_codes,
            "categoryCodes": self.category_codes,
            "hasInterpretation": self.has_interpretation,
            "hasReferenceRange": self.has_reference_range,
            "method": self.method,
            "specimen": self.specimen,
        }


def _coding_label(coding: dict[str, str]) -> str:
    system = coding.get("system") or ""
    code = coding.get("code") or ""
    short = system.rstrip("/").rsplit("/", 1)[-1] if system else ""
    return f"{short}|{code}" if short else code


def _value_text(resource: dict[str, Any]) -> tuple[str | None, str | None]:
    quantity = resource.get("valueQuantity")
    if isinstance(quantity, dict):
        value = quantity.get("value")
        unit = quantity.get("unit") or quantity.get("code")
        text = f"{value} {unit}".strip() if value is not None else (unit or None)
        return text, (str(unit) if unit is not None else None)
    concept = resource.get("valueCodeableConcept")
    if isinstance(concept, dict):
        if concept.get("text"):
            return str(concept["text"]), None
        found = codings(concept)
        if found:
            return found[0].get("display") or _coding_label(found[0]), None
    for suffix in ("String", "Boolean", "Integer", "Time", "DateTime"):
        key = f"{VALUE_PREFIX}{suffix}"
        if key in resource and not isinstance(resource[key], (dict, list)):
            return str(resource[key]), None
    return None, None


def summarize_observation(resource: dict[str, Any]) -> ObsSummary:
    rtype = resource_type(resource) or "Unknown"
    text, unit = _value_text(resource)
    code_concept = resource.get("code")
    component_codes: list[str] = []
    for component in as_list(resource.get("component")):
        if not isinstance(component, dict):
            continue
        for coding in codings(component.get("code")):
            component_codes.append(_coding_label(coding))
        concept = component.get("code")
        if isinstance(concept, dict) and not codings(concept) and concept.get("text"):
            component_codes.append(f"text:{concept['text']}")
    category_codes: list[str] = []
    for category in as_list(resource.get("category")):
        for coding in codings(category):
            category_codes.append(_coding_label(coding))
    method = resource.get("method")
    method_text = None
    if isinstance(method, dict):
        method_text = method.get("text") or (codings(method)[0].get("display") if codings(method) else None)
    specimen = resource.get("specimen")
    specimen_text = None
    if isinstance(specimen, dict):
        specimen_text = specimen.get("display") or specimen.get("reference")
    return ObsSummary(
        resource_id=str(resource["id"]) if isinstance(resource.get("id"), str) else None,
        resource_type=rtype,
        profiles=profiles(resource),
        code=observation_codings(resource),
        code_text=(code_concept.get("text") if isinstance(code_concept, dict) else None),
        value_type=value_type(resource),
        value_text=text,
        unit=unit,
        component_codes=component_codes,
        category_codes=category_codes,
        has_interpretation=bool(as_list(resource.get("interpretation"))),
        has_reference_range=bool(as_list(resource.get("referenceRange"))),
        method=str(method_text) if method_text else None,
        specimen=str(specimen_text) if specimen_text else None,
    )


OBSERVATION_LIKE = {"Observation", "DiagnosticReport"}


def iter_observations(resource: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for node in iter_resources(resource):
        if resource_type(node) == "Observation":
            yield node
