from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class TriageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    channel: str = "email"
    source: str | None = None


class EntityItem(BaseModel):
    label: str
    value: str
    confidence: float = 0.0


class TriageAnalysis(BaseModel):
    urgency: Literal["low", "medium", "high", "critical"]
    intent: str
    route: str
    summary: str
    rationale: str
    entities: list[EntityItem] = Field(default_factory=list)


class TriageResponse(BaseModel):
    analysis: TriageAnalysis
    draft_response: str
    next_action: str
    confidence: float = 0.0


class ListingIngestRequest(BaseModel):
    document_id: str
    text: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QuizGenerateRequest(BaseModel):
    document_id: str
    num_questions: int = Field(default=3, ge=1, le=10)


class QuizQuestion(BaseModel):
    question_id: str
    question: str
    answer_type: Literal["short_answer", "multiple_choice"]
    options: list[str] = Field(default_factory=list)
    source_chunks: list[str] = Field(default_factory=list)


class QuizSet(BaseModel):
    document_id: str
    questions: list[QuizQuestion]


class QuizAnswerRequest(BaseModel):
    document_id: str
    question_id: str
    question: str
    answer: str


class QuizEvaluation(BaseModel):
    question_id: str
    score: float
    is_correct: bool
    verdict: str
    explanation: str
    ideal_answer: str
    source_support: str


class HealthResponse(BaseModel):
    status: str

