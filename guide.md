# Synthea to HL7 FHIR R4 Data Pipeline & API Engine
## 프로젝트 가이드라인 & 배경 지식 문서 (Project Blueprint)

---

## 1. 프로젝트 배경 및 목적 (Background & Rationale)

### 1.1 도메인 특화 백엔드 엔지니어링의 필요성

- **AI 시대의 차별화**: 단순 요구사항 기반의 CRUD 개발자는 AI 코딩 툴에 의해 대체될 위험이 크다. 반면, 규제가 엄격하고 구조가 복잡한 헬스케어 도메인 지식(Healthcare Domain Knowledge)과 고성능 백엔드 설계 역량을 융합한 엔지니어는 높은 희소성과 독점적 가치를 가진다.
- **임상 데이터 중심의 접근**: 순수 분자 생물학 연구나 단순 라이프로그(웰니스) 앱을 넘어, 실제 병원 및 의료 IT 기업에서 가장 거대한 자본과 문제가 집중된 EMR/임상 데이터(Clinical Data) 처리 영역을 정조준한다.

### 1.2 왜 HL7 FHIR R4인가? (의료 데이터 상호운용성)

- **상호운용성(Interoperability)**: 병원 및 기관마다 파편화된 전자의무기록(EMR) 데이터 구조를 표준화하여 상호 교환할 수 있게 만드는 기술.
- **HL7 FHIR (Fast Healthcare Interoperability Resources) R4**: 전 세계 디지털 헬스케어 생태계의 사실상 표준(De-facto Standard) 규격. 환자(Patient), 진단(Condition), 처방(MedicationRequest) 등의 의료 행위를 RESTful JSON 리소스 단위로 정의.

### 1.3 핵심 CS 및 백엔드 지식 체계

1. **데이터 정합성 및 동시성 제어 (Concurrency Control)**: 대량의 임상 데이터 유입/수정 시 데이터 꼬임을 방지하기 위한 DB 격리 수준(Isolation Level) 및 비관적 잠금(Pessimistic Locking) 메커니즘 이해.
2. **네트워크 & 성능 최적화**: 대용량 JSON 파싱 시 메모리 관리, FastAPI 비동기(Async) 처리, REST API 통신 및 웹소켓(WebSocket) 확장성 고려.
3. **표준 용어 체계 (Medical Terminologies)**: 질병 표준 코드(ICD-10/KCD), 임상 검사 코드(LOINC), 의약품 코드(RxNorm) 등의 매핑 구조 이해.

---

## 2. 시스템 아키텍처 및 스펙 (System Architecture)

**Data Flow**
```
Kaggle Raw Data ➔ Python FHIR Engine ➔ FastAPI REST API ➔ Pytest Validation
```

**Data Source**: 캐글(Kaggle) Synthea 기반 가상 환자/임상 레코드 (patients.csv, conditions.csv)

**Tech Stack**: Python 3.10+, FastAPI, Uvicorn, Pytest, Pydantic, HTTPX

**Core Deliverable**
- 캐글 Raw 데이터를 HL7 FHIR R4 Bundle(JSON) 규격으로 변환하는 모듈
- 변환 엔진을 탑재한 FastAPI REST API 서버
- 데이터 정합성 및 예외 처리 검증용 pytest 자동화 테스트 스위트
- 아키텍처 및 실행 방법이 정리된 README.md

---

## 3. 당일 완성을 위한 4단계 로드맵 (Execution Plan)

| 단계 | 이름 | 내용 |
|---|---|---|
| Step 1 | Core Engine | 캐글 Raw 데이터 수신 및 HL7 FHIR R4 Patient & Condition Bundle 변환 파이프라인 작성 |
| Step 2 | API Service | FastAPI 기반 `POST /api/v1/fhir/transform` 엔드포인트 구축 및 Pydantic 스키마 검증 |
| Step 3 | Reliability Test | pytest 기반 정상 케이스 매핑 및 에러(필수값 누락, 성별 포맷 오류 등) 예외 처리 검증 |
| Step 4 | Documentation | GitHub 제출용 README.md 작성 및 아키텍처 문서화 |

---

## 4. 새 채팅방 전용 실행 프롬프트 키트 (Prompt Kit)

> 사용 방법: 새 채팅방에 본 문서를 복사해 넣은 후, 아래 프롬프트를 1번부터 순서대로 입력한다.

### [Prompt 1] FHIR R4 Core 변환 엔진 작성

```
나는 헬스케어 백엔드 개발자야. 업로드한 가이드라인 문서에 따라 캐글 Synthea 가상 환자
원시 데이터를 HL7 FHIR R4 규격으로 변환하는 파이썬 파이프라인 엔진(converter.py)을
작성하려고 해.

아래는 내가 가진 캐글 환자 데이터 및 진단 데이터의 필드 예시야:

환자 데이터: {"Id": "PT-101", "FIRST": "Dahyun", "LAST": "Kim", "BIRTHDATE": "2002-05-14", "GENDER": "M"}
진단 데이터: {"START": "2024-01-10", "PATIENT": "PT-101", "CODE": "I10", "DESCRIPTION": "Essential hypertension"}

위 원시 데이터를 입력받아 FHIR R4 규격의 Patient와 Condition 리소스를 포함하는
'FHIR Bundle (collection)' JSON 구조를 반환하는 파이썬 함수
transform_to_fhir_bundle(raw_patient, raw_conditions)를 만들어줘.

[조건]
- GENDER ('M'/'F')는 FHIR 규격인 'male'/'female'로 안전하게 매핑할 것.
- 날짜 형식(YYYY-MM-DD) 유효성 검증 포함.
- 진단 코드(CODE)는 FHIR Condition.code.coding 구조에 맞게 매핑할 것.
- 하단에 if __name__ == '__main__': 실행 예제를 포함해 바로 터미널 출력을 검증할 수 있게 할 것.
```

### [Prompt 2] FastAPI 웹 서버 구축

```
방금 작성한 transform_to_fhir_bundle 함수를 기반으로 FastAPI 웹 서버(main.py)를 구현해줘.

[요구사항]
- POST /api/v1/fhir/transform 엔드포인트를 구현할 것.
- 요청 바디(JSON)로 캐글 Raw 데이터를 전달받아 FHIR Bundle JSON 응답 반환.
- Raw 데이터의 필수 필드가 누락되었거나 날짜 포맷 오류 시 422 Unprocessable Entity 및
  명확한 에러 메시지 반환.
- uvicorn으로 즉시 실행 가능한 하단 블록 포함.
```

### [Prompt 3] Pytest 자동화 테스트 스위트 작성

```
구현된 FastAPI 서버 및 FHIR 변환 로직에 대해 pytest 및 httpx 기반의 테스트 코드
(test_main.py)를 작성해줘.

[테스트 케이스]
- test_transform_success: 정상 데이터 유입 시 resourceType이 'Bundle'이고 내부
  Patient/Condition이 올바르게 매핑되는지 검증.
- test_gender_mapping_fallback: GENDER 값이 이상할 경우 FHIR 규격상 'unknown'으로
  안전하게 처리되는지 검증.
- test_missing_required_field: 필수 ID/이름 누락 시 422 에러 반환 검증.
```

### [Prompt 4] GitHub README.md 생성

```
오늘 완성한 'Synthea to HL7 FHIR R4 Pipeline Engine' 프로젝트의 포트폴리오용
GitHub README.md 내용을 마크다운으로 작성해줘.

[포함 내용]
- Executive Summary (헬스케어 상호운용성 및 FHIR R4의 중요성)
- System Architecture (Data Flow 시각화)
- Key Features & Concurrency/Validation Strategy
- Getting Started & API Specification
- Test Coverage & Reliability (pytest 결과 요약)
```

---

## 5. 실행 체크리스트 (Action Checklist)

- [ ] 캐글(Kaggle)에서 Synthea 데이터셋 다운로드 완료
- [ ] converter.py 구현 및 터미널 FHIR JSON 출력 성공
- [ ] main.py (FastAPI) 실행 및 /docs (Swagger UI) 테스트 성공
- [ ] pytest test_main.py 실행 후 ALL PASSED 초록불 확인
- [ ] GitHub 저장소 생성 및 README.md와 함께 최종 커밋 완료
