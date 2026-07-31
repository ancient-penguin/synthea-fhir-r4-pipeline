"""CSV → FHIR 변환 파이프라인 스크립트. 실제 Synthea 데이터에 대해 변환 검증."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.converter import FHIRTransformationError, transform_to_fhir_bundle


def load_conditions() -> dict[str, list[dict]]:
    """조건(conditions.csv)을 환자 ID 기준으로 그룹핑."""
    conditions_by_patient: dict[str, list[dict]] = defaultdict(list)
    csv_path = Path(__file__).parent.parent / "data" / "raw" / "conditions.csv"

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            patient_id = row["PATIENT"]
            conditions_by_patient[patient_id].append(row)

    return conditions_by_patient


def run_direct(
    patient_id: str | None,
    limit: int,
    out_dir: Path | None,
) -> None:
    """변환 함수를 직접 호출해 결과를 출력/저장."""
    csv_path = Path(__file__).parent.parent / "data" / "raw" / "patients.csv"
    conditions_by_patient = load_conditions()

    processed = 0
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if patient_id and row["Id"] != patient_id:
                continue

            try:
                conditions = conditions_by_patient.get(row["Id"], [])
                bundle = transform_to_fhir_bundle(row, conditions)

                if out_dir:
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_file = out_dir / f"{row['Id']}.json"
                    out_file.write_text(
                        json.dumps(bundle, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )
                    print(f"✓ {row['Id']} → {out_file}")
                else:
                    print(f"\n{'='*60}\nPatient: {row['Id']}\n{'='*60}")
                    print(json.dumps(bundle, indent=2, ensure_ascii=False))

                processed += 1
                if processed >= limit:
                    break

            except FHIRTransformationError as e:
                print(f"✗ {row['Id']}: {e}", file=sys.stderr)


def run_via_api(
    patient_id: str | None,
    limit: int,
    out_dir: Path | None,
) -> None:
    """API 경유로 변환 결과를 요청하고 출력/저장."""
    try:
        import httpx
    except ImportError:
        print("Error: httpx가 설치되지 않았습니다. pip install httpx 실행 후 다시 시도하세요.", file=sys.stderr)
        sys.exit(1)

    csv_path = Path(__file__).parent.parent / "data" / "raw" / "patients.csv"
    conditions_by_patient = load_conditions()
    api_url = "http://localhost:8000/api/v1/fhir/transform"

    processed = 0
    try:
        with httpx.Client() as client:
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if patient_id and row["Id"] != patient_id:
                        continue

                    try:
                        conditions = conditions_by_patient.get(row["Id"], [])
                        payload = {"raw_patient": row, "raw_conditions": conditions}

                        response = client.post(api_url, json=payload)
                        if response.status_code != 200:
                            print(
                                f"✗ {row['Id']}: API 에러 {response.status_code}: {response.text}",
                                file=sys.stderr,
                            )
                            continue

                        bundle = response.json()

                        if out_dir:
                            out_dir.mkdir(parents=True, exist_ok=True)
                            out_file = out_dir / f"{row['Id']}.json"
                            out_file.write_text(
                                json.dumps(bundle, indent=2, ensure_ascii=False) + "\n",
                                encoding="utf-8",
                            )
                            print(f"✓ {row['Id']} → {out_file} (via API)")
                        else:
                            print(f"\n{'='*60}\nPatient: {row['Id']} (via API)\n{'='*60}")
                            print(json.dumps(bundle, indent=2, ensure_ascii=False))

                        processed += 1
                        if processed >= limit:
                            break

                    except FHIRTransformationError as e:
                        print(f"✗ {row['Id']}: {e}", file=sys.stderr)

    except httpx.ConnectError:
        print(
            "Error: FastAPI 서버에 연결할 수 없습니다. "
            "uvicorn app.main:app --reload을 먼저 실행하세요.",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synthea CSV 데이터를 HL7 FHIR R4 Bundle로 변환"
    )
    parser.add_argument(
        "--patient-id",
        type=str,
        default=None,
        help="특정 환자 ID만 변환 (미지정 시 전체)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="처리할 환자 수 제한 (기본값: 5)",
    )
    parser.add_argument(
        "--via-api",
        action="store_true",
        help="FastAPI 서버 경유로 변환 (서버 기동 필요)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="출력 디렉토리 (미지정 시 stdout에 출력)",
    )

    args = parser.parse_args()

    if args.via_api:
        run_via_api(args.patient_id, args.limit, args.out)
    else:
        run_direct(args.patient_id, args.limit, args.out)


if __name__ == "__main__":
    main()
