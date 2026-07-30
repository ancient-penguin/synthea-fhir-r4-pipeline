"""Synthea raw data -> HL7 FHIR R4 Bundle 변환 엔진."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

SNOMED_CT_SYSTEM = "http://snomed.info/sct"
DATE_FORMAT = "%Y-%m-%d"
GENDER_MAP = {"M": "male", "F": "female"}


class FHIRTransformationError(ValueError):
    """Raw 데이터를 FHIR 리소스로 변환하는 데 실패했을 때 발생하는 예외."""


def _require_fields(raw: dict[str, Any], fields: list[str], resource_name: str) -> None:
    missing = [field for field in fields if not raw.get(field)]
    if missing:
        raise FHIRTransformationError(
            f"{resource_name} 필수 필드 누락: {', '.join(missing)}"
        )


def _validate_date(value: Any, field_name: str) -> str:
    try:
        datetime.strptime(value, DATE_FORMAT)
    except (ValueError, TypeError):
        raise FHIRTransformationError(
            f"{field_name} 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD 필요): {value!r}"
        )
    return value


def _map_gender(raw_gender: Any) -> str:
    return GENDER_MAP.get(str(raw_gender or "").strip().upper(), "unknown")


def _build_patient_resource(raw_patient: dict[str, Any]) -> dict[str, Any]:
    _require_fields(raw_patient, ["Id", "FIRST", "LAST", "BIRTHDATE"], "Patient")
    birth_date = _validate_date(raw_patient["BIRTHDATE"], "BIRTHDATE")

    return {
        "resourceType": "Patient",
        "id": raw_patient["Id"],
        "name": [
            {
                "use": "official",
                "family": raw_patient["LAST"],
                "given": [raw_patient["FIRST"]],
            }
        ],
        "gender": _map_gender(raw_patient.get("GENDER")),
        "birthDate": birth_date,
    }


def _build_condition_resource(raw_condition: dict[str, Any], patient_id: str) -> dict[str, Any]:
    _require_fields(raw_condition, ["CODE", "START"], "Condition")
    onset_date = _validate_date(raw_condition["START"], "START")

    return {
        "resourceType": "Condition",
        "id": str(uuid.uuid4()),
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                }
            ]
        },
        "code": {
            "coding": [
                {
                    "system": SNOMED_CT_SYSTEM,
                    "code": raw_condition["CODE"],
                    "display": raw_condition.get("DESCRIPTION"),
                }
            ],
            "text": raw_condition.get("DESCRIPTION"),
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "onsetDateTime": onset_date,
    }


def transform_to_fhir_bundle(
    raw_patient: dict[str, Any], raw_conditions: list[dict[str, Any]]
) -> dict[str, Any]:
    """캐글 Synthea raw 데이터를 FHIR R4 Bundle(collection) JSON으로 변환한다."""
    patient_resource = _build_patient_resource(raw_patient)
    patient_id = patient_resource["id"]

    entries = [{"resource": patient_resource}]
    for raw_condition in raw_conditions:
        entries.append({"resource": _build_condition_resource(raw_condition, patient_id)})

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": entries,
    }


if __name__ == "__main__":
    import json

    sample_patient = {
        "Id": "PT-101",
        "FIRST": "Dahyun",
        "LAST": "Kim",
        "BIRTHDATE": "2002-05-14",
        "GENDER": "M",
    }
    sample_conditions = [
        {
            "START": "2024-01-10",
            "PATIENT": "PT-101",
            "CODE": "160968000",
            "DESCRIPTION": "Risk activity involvement (finding)",
        }
    ]

    bundle = transform_to_fhir_bundle(sample_patient, sample_conditions)
    print(json.dumps(bundle, indent=2, ensure_ascii=False))
