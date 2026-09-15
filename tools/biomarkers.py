"""Index of biomarker codes across all submissions.

This is what makes the collection comparable: one page per code, one row per
occurrence, so that different representations of the same biomarker sit next to
each other.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from .results import RunResult

SYSTEM_LABELS = {
    "http://loinc.org": "LOINC",
    "http://snomed.info/sct": "SNOMED CT",
    "http://www.genenames.org": "HGNC",
    "http://www.nlm.nih.gov/research/umls/rxnorm": "RxNorm",
    "http://unitsofmeasure.org": "UCUM",
}


def system_label(system: str) -> str:
    if system in SYSTEM_LABELS:
        return SYSTEM_LABELS[system]
    if not system:
        return "(no system)"
    return system.rstrip("/").rsplit("/", 1)[-1]


def slugify(value: str) -> str:
    """Turn a system URI or code into a safe single path segment."""
    cleaned = re.sub(r"^https?://", "", value or "none")
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", cleaned).strip("-")
    return (cleaned or "none").lower()[:80]


def key_of(system: str, code: str) -> str:
    return f"{system}|{code}"


def build_index(run: "RunResult") -> list[dict[str, Any]]:
    """Group every Observation.code occurrence by system and code."""
    index: dict[str, dict[str, Any]] = {}
    declared_names: dict[str, str] = {}
    for submission in run.submissions:
        for biomarker in submission.biomarkers:
            if biomarker.get("code"):
                declared_names.setdefault(
                    key_of(biomarker.get("system", ""), biomarker["code"]), biomarker.get("name", "")
                )
    for submission in run.submissions:
        for file_result in submission.files:
            for observation in file_result.observations:
                for coding in observation.get("code") or []:
                    system = coding.get("system", "")
                    code = coding.get("code", "")
                    if not code:
                        continue
                    key = key_of(system, code)
                    entry = index.setdefault(
                        key,
                        {
                            "key": key,
                            "system": system,
                            "systemLabel": system_label(system),
                            "code": code,
                            "name": coding.get("display")
                            or declared_names.get(key)
                            or observation.get("codeText")
                            or code,
                            "slug": f"{slugify(system)}/{slugify(code)}",
                            "occurrences": [],
                        },
                    )
                    entry["occurrences"].append(
                        {
                            "submission": submission.id,
                            "title": submission.title,
                            "contributor": submission.contributor,
                            "status": submission.status,
                            "file": file_result.name,
                            "filePath": file_result.path,
                            "resourceId": observation.get("resourceId"),
                            "resourceType": observation.get("resourceType"),
                            "profiles": observation.get("profiles") or [],
                            "valueType": observation.get("valueType"),
                            "valueText": observation.get("valueText"),
                            "unit": observation.get("unit"),
                            "componentCodes": observation.get("componentCodes") or [],
                            "categoryCodes": observation.get("categoryCodes") or [],
                            "hasInterpretation": observation.get("hasInterpretation", False),
                            "hasReferenceRange": observation.get("hasReferenceRange", False),
                            "method": observation.get("method"),
                            "specimen": observation.get("specimen"),
                        }
                    )
    for entry in index.values():
        entry["submissionCount"] = len({o["submission"] for o in entry["occurrences"]})
        entry["occurrenceCount"] = len(entry["occurrences"])
    return [index[key] for key in sorted(index, key=lambda k: (index[k]["systemLabel"], index[k]["code"]))]
