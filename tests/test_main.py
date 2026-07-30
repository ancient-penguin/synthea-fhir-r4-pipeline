"""pytest + httpx 기반 FHIR 변환/API 테스트 스위트."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

TRANSFORM_URL = "/api/v1/fhir/transform"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_transform_success(client: TestClient) -> None:
    payload = {
        "raw_patient": {
            "Id": "PT-101",
            "FIRST": "Dahyun",
            "LAST": "Kim",
            "BIRTHDATE": "2002-05-14",
            "GENDER": "M",
        },
        "raw_conditions": [
            {
                "START": "2024-01-10",
                "PATIENT": "PT-101",
                "CODE": "160968000",
                "DESCRIPTION": "Risk activity involvement (finding)",
            }
        ],
    }

    response = client.post(TRANSFORM_URL, json=payload)

    assert response.status_code == 200
    body = response.json()

    assert body["resourceType"] == "Bundle"
    assert body["type"] == "collection"
    assert len(body["entry"]) == 2

    patient_resource = body["entry"][0]["resource"]
    assert patient_resource["resourceType"] == "Patient"
    assert patient_resource["id"] == "PT-101"
    assert patient_resource["gender"] == "male"
    assert patient_resource["birthDate"] == "2002-05-14"
    assert patient_resource["name"][0]["family"] == "Kim"
    assert patient_resource["name"][0]["given"] == ["Dahyun"]

    condition_resource = body["entry"][1]["resource"]
    assert condition_resource["resourceType"] == "Condition"
    assert condition_resource["subject"]["reference"] == "Patient/PT-101"
    assert condition_resource["code"]["coding"][0]["code"] == "160968000"
    assert condition_resource["onsetDateTime"] == "2024-01-10"


def test_gender_mapping_fallback(client: TestClient) -> None:
    payload = {
        "raw_patient": {
            "Id": "PT-102",
            "FIRST": "Jihyo",
            "LAST": "Park",
            "BIRTHDATE": "1997-02-01",
            "GENDER": "X",
        },
        "raw_conditions": [],
    }

    response = client.post(TRANSFORM_URL, json=payload)

    assert response.status_code == 200
    body = response.json()

    patient_resource = body["entry"][0]["resource"]
    assert patient_resource["gender"] == "unknown"


def test_missing_required_field(client: TestClient) -> None:
    payload = {
        "raw_patient": {
            "FIRST": "Nayeon",
            "BIRTHDATE": "1995-09-22",
            "GENDER": "F",
        },
        "raw_conditions": [],
    }

    response = client.post(TRANSFORM_URL, json=payload)

    assert response.status_code == 422
    body = response.json()
    assert "Id" in body["detail"]
    assert "LAST" in body["detail"]
