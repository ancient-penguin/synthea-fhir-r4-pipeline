# Synthea to HL7 FHIR R4 Pipeline

Kaggle Synthea raw CSV(환자/진단 데이터)를 [HL7 FHIR R4](https://www.hl7.org/fhir/) `Bundle` JSON으로 변환하는 소규모 FastAPI 서비스입니다. Patient/Condition 두 리소스를 지원합니다.

## Features

- Synthea `patients.csv` / `conditions.csv` 레코드 → FHIR R4 `Patient` / `Condition` 변환
- 필수 필드, 날짜 형식(`YYYY-MM-DD`), FHIR `id` 형식 검증
- Condition은 항목별로 검증되어, 유효한 것만 Bundle에 포함되고 실패한 항목은 `OperationOutcome` 리소스로 함께 보고됩니다(부분 성공 허용). Patient 검증 실패는 요청 전체를 `422`로 처리합니다.
- `GET /health` 헬스체크, `POST /api/v1/fhir/transform` 변환 엔드포인트
- 실제 CSV 데이터로 변환을 검증하는 CLI 스크립트(`scripts/run_pipeline.py`)

## Project Structure

```
fhir_project/
├── app/
│   ├── converter.py      # 변환 엔진 (검증 + FHIR 리소스 빌드)
│   └── main.py            # FastAPI 서버
├── tests/test_main.py     # pytest 테스트 스위트
├── scripts/run_pipeline.py  # CSV → FHIR CLI 검증 도구
└── data/raw/               # Synthea patients.csv / conditions.csv
```

Stack: Python 3.10+, FastAPI, Pydantic, Uvicorn, Pytest, HTTPX.

## Getting Started

```bash
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload  # http://localhost:8000, docs at /docs
curl http://localhost:8000/health
```

실제 Synthea 데이터로 변환 확인:

```bash
python scripts/run_pipeline.py --limit 5              # stdout으로 출력
python scripts/run_pipeline.py --limit 5 --out output/  # 파일로 저장
python scripts/run_pipeline.py --limit 5 --via-api     # 실행 중인 API 경유
```

## API

### `POST /api/v1/fhir/transform`

```json
// Request
{
  "raw_patient": {"Id": "PT-101", "FIRST": "Dahyun", "LAST": "Kim", "BIRTHDATE": "2002-05-14", "GENDER": "F"},
  "raw_conditions": [
    {"START": "2024-01-10", "PATIENT": "PT-101", "CODE": "160968000", "DESCRIPTION": "Risk activity involvement (finding)"}
  ]
}
```

성공 시 `200`과 FHIR `Bundle`(type: `collection`)을 반환합니다. Patient 검증 실패는 `422`, Condition 일부 실패는 `200` + `OperationOutcome` 엔트리로 보고됩니다.

## Testing

```bash
pytest tests/ -v
```

정상 변환, gender 매핑 fallback, 필수 필드/날짜/id 형식 검증, Condition 부분 실패, 헬스체크까지 8개 테스트가 있습니다.

## License

MIT — [ancient-penguin](https://github.com/ancient-penguin)
