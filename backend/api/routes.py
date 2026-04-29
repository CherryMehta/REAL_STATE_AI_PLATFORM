from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import (
    HealthResponse,
    ListingIngestRequest,
    QuizAnswerRequest,
    QuizEvaluation,
    QuizGenerateRequest,
    QuizSet,
    TriageRequest,
    TriageResponse,
)
from app.services.quiz_service import QuizService
from app.services.triage_service import TriageService

router = APIRouter()

triage_service = TriageService()
quiz_service = QuizService()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/api/triage/analyze", response_model=TriageResponse)
def analyze_triage(payload: TriageRequest) -> TriageResponse:
    return triage_service.analyze(payload)


@router.post("/api/quiz/ingest")
def ingest_listing(payload: ListingIngestRequest) -> dict:
    return quiz_service.ingest(payload.document_id, payload.text, payload.metadata)


@router.post("/api/quiz/generate", response_model=QuizSet)
def generate_quiz(payload: QuizGenerateRequest) -> QuizSet:
    return quiz_service.generate(payload)


@router.post("/api/quiz/evaluate", response_model=QuizEvaluation)
def evaluate_quiz(payload: QuizAnswerRequest) -> QuizEvaluation:
    return quiz_service.evaluate(payload)

