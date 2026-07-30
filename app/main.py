"""FastAPI 서버 — POST /api/v1/fhir/transform 엔드포인트."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.converter import FHIRTransformationError, transform_to_fhir_bundle

app = FastAPI(
    title="Synthea to HL7 FHIR R4 Pipeline Engine",
    description="캐글 Synthea Raw 데이터를 HL7 FHIR R4 Bundle로 변환하는 API",
    version="1.0.0",
)


class TransformRequest(BaseModel):
    raw_patient: dict[str, Any] = Field(..., description="캐글 환자(patients.csv) Raw 레코드")
    raw_conditions: list[dict[str, Any]] = Field(
        default_factory=list, description="캐글 진단(conditions.csv) Raw 레코드 목록"
    )


@app.exception_handler(FHIRTransformationError)
async def fhir_transformation_error_handler(
    request: Request, exc: FHIRTransformationError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.post("/api/v1/fhir/transform")
async def transform_fhir(payload: TransformRequest) -> dict[str, Any]:
    return transform_to_fhir_bundle(payload.raw_patient, payload.raw_conditions)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
