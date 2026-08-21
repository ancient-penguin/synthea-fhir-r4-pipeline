"""Synthea raw data -> HL7 FHIR R4 Bundle 변환 엔진."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

SNOMED_CT_SYSTEM = "http://snomed.info/sct"
DATE_FORMAT = "%Y-%m-%d"
GENDER_MAP = {"M": "male", "F": "female"}
FHIR_ID_PATTERN = re.compile(r"^[A-Za-z0-9\-\.]{1,64}$")


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


def _validate_fhir_id(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not FHIR_ID_PATTERN.match(value):
        raise FHIRTransformationError(
            f"{field_name} 값이 FHIR id 형식에 맞지 않습니다 "
            f"(영숫자, '-', '.'만 허용, 64자 이하): {value!r}"
        )
    return value


def _build_patient_resource(raw_patient: dict[str, Any]) -> dict[str, Any]:
    _require_fields(raw_patient, ["Id", "FIRST", "LAST", "BIRTHDATE"], "Patient")
    patient_id = _validate_fhir_id(raw_patient["Id"], "Id")
    birth_date = _validate_date(raw_patient["BIRTHDATE"], "BIRTHDATE")

    return {
        "resourceType": "Patient",
        "id": patient_id,
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


def _build_operation_outcome(issues: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "resourceType": "OperationOutcome",
        "issue": issues,
    }


def transform_to_fhir_bundle(
    raw_patient: dict[str, Any], raw_conditions: list[dict[str, Any]]
) -> dict[str, Any]:
    """캐글 Synthea raw 데이터를 FHIR R4 Bundle(collection) JSON으로 변환한다.

    Patient 검증 실패는 전체 요청을 실패시킨다. Condition은 항목별로 검증하여
    유효한 항목만 Bundle에 포함하고, 실패한 항목은 OperationOutcome 리소스로
    Bundle에 함께 담아 보고한다(부분 성공 허용).
    """
    patient_resource = _build_patient_resource(raw_patient)
    patient_id = patient_resource["id"]

    entries = [{"resource": patient_resource}]
    issues: list[dict[str, Any]] = []
    for index, raw_condition in enumerate(raw_conditions):
        try:
            entries.append({"resource": _build_condition_resource(raw_condition, patient_id)})
        except FHIRTransformationError as exc:
            logger.warning("patient=%s raw_conditions[%d] 스킵: %s", patient_id, index, exc)
            issues.append(
                {
                    "severity": "warning",
                    "code": "invalid",
                    "diagnostics": str(exc),
                    "expression": [f"raw_conditions[{index}]"],
                }
            )

    if issues:
        entries.append({"resource": _build_operation_outcome(issues)})

    logger.info(
        "patient=%s conditions=%d/%d succeeded",
        patient_id,
        len(raw_conditions) - len(issues),
        len(raw_conditions),
    )

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
