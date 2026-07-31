# Synthea to HL7 FHIR R4 Data Pipeline & API Engine

## Executive Summary

### The Problem: Healthcare Data Interoperability

Healthcare systems worldwide suffer from fragmented Electronic Medical Record (EMR) data structures. When patient records need to be shared between hospitals, clinics, and health IT platforms, incompatible data formats create operational friction and limit clinical data accessibility. This fragmentation undermines the goal of a unified, interoperable healthcare ecosystem.

### The Solution: HL7 FHIR R4

**HL7 FHIR (Fast Healthcare Interoperability Resources) R4** is the de-facto international standard for digital healthcare data exchange. FHIR defines clinical concepts—Patient, Condition, MedicationRequest, and others—as RESTful JSON resources, enabling seamless data transformation and sharing across healthcare organizations.

### This Project

This repository implements a **production-ready pipeline** that transforms raw Kaggle Synthea patient/clinical data into HL7 FHIR R4 compliant JSON Bundles. The pipeline:
- Converts raw patient demographics and clinical conditions to FHIR R4 Patient and Condition resources
- Exposes a FastAPI REST endpoint (`POST /api/v1/fhir/transform`) for real-time transformation
- Validates all inputs and handles errors gracefully with FHIR-compliant HTTP status codes
- Provides CLI tooling to verify transformation against real Synthea CSV data

---

## System Architecture

### Data Flow

```
┌─────────────────────┐
│ Kaggle Synthea CSV  │ (patients.csv, conditions.csv)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────┐
│  Python FHIR Transformation     │
│  • app/converter.py             │
│  • GENDER mapping (M→male, ...) │
│  • Date validation (YYYY-MM-DD) │
│  • Required field checking      │
│  • SNOMED CT code system        │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────┐
│ FHIR R4 Bundle JSON │
│ (collection type)   │
└──────────┬──────────┘
           │
     ┌─────┴──────┐
     ▼            ▼
┌──────────┐  ┌──────────────────┐
│FastAPI   │  │ CLI Verification │
│REST API  │  │ scripts/         │
└──────────┘  │ run_pipeline.py  │
     │        └──────────────────┘
     ▼
┌─────────────────────────────────┐
│  Pytest Validation Suite        │
│  • test_transform_success       │
│  • test_gender_mapping_fallback │
│  • test_missing_required_field  │
└─────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.10+ | Core application |
| **Web Framework** | FastAPI | REST API server with automatic OpenAPI docs |
| **Server** | Uvicorn | ASGI application server |
| **Data Validation** | Pydantic | Request/response schema validation |
| **Testing** | Pytest | Automated test suite |
| **HTTP Client** | HTTPX | CLI mode API verification |

### Project Structure

```
fhir_project/
├── app/
│   ├── __init__.py
│   ├── converter.py          # Core FHIR transformation engine
│   └── main.py               # FastAPI server & /api/v1/fhir/transform endpoint
├── tests/
│   ├── __init__.py
│   └── test_main.py          # Integration tests (3 test cases)
├── scripts/
│   └── run_pipeline.py       # CLI tool for CSV→FHIR verification
├── data/raw/
│   ├── patients.csv          # Synthea patient demographics
│   └── conditions.csv        # Synthea clinical conditions
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

---

## Key Features & Validation Strategy

### Data Transformation

#### 1. GENDER Mapping (Safe Fallback)
```python
"M" / "F"  →  "male" / "female"    # FHIR gender values
(any other value)  →  "unknown"     # Graceful fallback
```
- Location: [`app/converter.py:36-37`](app/converter.py#L36-L37)
- Ensures invalid gender codes don't crash the pipeline

#### 2. Date Format Validation
- Enforces ISO 8601 format: `YYYY-MM-DD`
- Parses and validates using Python's `datetime.strptime()`
- Returns explicit error if format is invalid
- Location: [`app/converter.py:26-33`](app/converter.py#L26-L33)

#### 3. Required Field Validation
- Enforces mandatory fields:
  - **Patient**: `Id`, `FIRST`, `LAST`, `BIRTHDATE`
  - **Condition**: `CODE`, `START`
- Returns detailed error message listing all missing fields
- Location: [`app/converter.py:18-23`](app/converter.py#L18-L23)

#### 4. SNOMED CT Code System Mapping
- Maps condition codes to SNOMED CT (Systematized Nomenclature of Medicine Clinical Terms)
- System URI: `http://snomed.info/sct`
- Includes condition display text for human readability
- Location: [`app/converter.py:59-86`](app/converter.py#L59-L86)

### Error Handling & HTTP Status Codes

| Error Scenario | HTTP Status | Response |
|---|---|---|
| All inputs valid | `200 OK` | FHIR Bundle JSON |
| Missing required field(s) | `422 Unprocessable Entity` | JSON error detail |
| Invalid date format | `422 Unprocessable Entity` | JSON error detail |
| Malformed JSON | `422 Unprocessable Entity` | Pydantic validation error |

---

## Getting Started

### Prerequisites
- Python 3.10+
- pip (Python package manager)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/ancient-penguin/fhir_project.git
cd fhir_project

# 2. Create a virtual environment (optional but recommended)
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Run the FastAPI Server

```bash
# Start the server on http://localhost:8000
uvicorn app.main:app --reload

# Open Swagger UI for interactive testing:
# Navigate to http://localhost:8000/docs in your browser
```

### Verify with Real Synthea Data

The `scripts/run_pipeline.py` CLI tool allows you to transform actual Synthea CSV data without running the API server:

```bash
# Transform and print first 5 patients to stdout
python scripts/run_pipeline.py --limit 5

# Transform and save to JSON files
python scripts/run_pipeline.py --limit 5 --out output/

# Transform a specific patient by ID
python scripts/run_pipeline.py --patient-id "6132a397-93f1-3f41-a63b-2c86042ae94c"

# Verify via the running FastAPI server (must be running)
python scripts/run_pipeline.py --limit 5 --via-api
```

---

## API Specification

### Endpoint: POST /api/v1/fhir/transform

Transform raw Synthea patient and condition data into a FHIR R4 Bundle.

#### Request

```json
{
  "raw_patient": {
    "Id": "PT-101",
    "FIRST": "Dahyun",
    "LAST": "Kim",
    "BIRTHDATE": "2002-05-14",
    "GENDER": "F"
  },
  "raw_conditions": [
    {
      "START": "2024-01-10",
      "PATIENT": "PT-101",
      "CODE": "160968000",
      "DESCRIPTION": "Risk activity involvement (finding)"
    }
  ]
}
```

#### Response (200 OK)

```json
{
  "resourceType": "Bundle",
  "type": "collection",
  "entry": [
    {
      "resource": {
        "resourceType": "Patient",
        "id": "PT-101",
        "name": [
          {
            "use": "official",
            "family": "Kim",
            "given": ["Dahyun"]
          }
        ],
        "gender": "female",
        "birthDate": "2002-05-14"
      }
    },
    {
      "resource": {
        "resourceType": "Condition",
        "id": "a1b2c3d4-e5f6-4a5b-8c9d-e0f1a2b3c4d5",
        "clinicalStatus": {
          "coding": [
            {
              "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
              "code": "active"
            }
          ]
        },
        "code": {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "160968000",
              "display": "Risk activity involvement (finding)"
            }
          ],
          "text": "Risk activity involvement (finding)"
        },
        "subject": {
          "reference": "Patient/PT-101"
        },
        "onsetDateTime": "2024-01-10"
      }
    }
  ]
}
```

#### Error Response (422 Unprocessable Entity)

```json
{
  "detail": "Patient 필수 필드 누락: Id, LAST"
}
```

---

## Test Coverage & Reliability

This project includes a comprehensive pytest suite to verify correctness and error handling.

### Test Cases

#### 1. test_transform_success
- **Purpose**: Verify successful transformation of valid data
- **Scenario**: Valid patient with multiple conditions
- **Assertions**: 
  - Response status is 200
  - Bundle contains Patient and Condition resources
  - All fields mapped correctly (gender, dates, names, codes)

#### 2. test_gender_mapping_fallback
- **Purpose**: Verify invalid gender codes safely fallback to "unknown"
- **Scenario**: Patient with `GENDER: "X"` (invalid code)
- **Assertion**: Transformed gender is "unknown" instead of crashing

#### 3. test_missing_required_field
- **Purpose**: Verify missing required fields return 422 error
- **Scenario**: Patient with missing `Id` and `LAST` fields
- **Assertions**:
  - Response status is 422
  - Error detail includes names of missing fields

### Running Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app

# Expected output:
# tests/test_main.py::test_transform_success PASSED
# tests/test_main.py::test_gender_mapping_fallback PASSED
# tests/test_main.py::test_missing_required_field PASSED
# ======================== 3 passed in 0.37s ========================
```

---

## Development & Contributing

### Project Goals
This project demonstrates healthcare domain-specific backend engineering combining:
- **FHIR R4 expertise**: Industry-standard data format for clinical interoperability
- **Input validation & error handling**: Production-ready pipeline resilience
- **FastAPI best practices**: Clean REST API design with automatic documentation

### Future Enhancements (Not Implemented)
The guide document references advanced topics like concurrency control and medical code mappings (ICD-10, LOINC) that are outside the current scope but represent natural extensions:
- Database transaction isolation levels for concurrent writes
- Medical terminology code system validators (ICD-10/KCD, LOINC, RxNorm)
- Batch transformation endpoints for bulk data processing

### License
MIT

---

## Author

**古代 ペンギン (ancient-penguin)**  
Healthcare Backend Engineer | FHIR R4 Specialist

---

*Last Updated: 2026-08-01*
