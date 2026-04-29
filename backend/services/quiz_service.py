from __future__ import annotations

import re
import uuid

from app.models.schemas import QuizAnswerRequest, QuizEvaluation, QuizGenerateRequest, QuizQuestion, QuizSet
from app.services.groq_client import GroqClient
from app.services.rag_service import RagService
from app.services.session_store import QuizSession, SessionStore


class QuizService:
    def __init__(self) -> None:
        self.groq = GroqClient()
        self._rag: RagService | None = None
        self.sessions = SessionStore()

    @property
    def rag(self) -> RagService:
        if self._rag is None:
            self._rag = RagService()
        return self._rag

    def ingest(self, document_id: str, text: str, metadata: dict | None = None) -> dict:
        try:
            chunk_count = self.rag.ingest(document_id=document_id, text=text, metadata=metadata)
        except Exception:
            chunk_count = 0
        session = self.sessions.get_session(document_id) or QuizSession(document_id=document_id)
        self.sessions.set_session(document_id, session)
        return {"document_id": document_id, "chunks_indexed": chunk_count}

    def generate(self, request: QuizGenerateRequest, source_text: str | None = None) -> QuizSet:
        query = f"Create assessment questions from the following real estate listing content for document {request.document_id}."
        effective_text = source_text or "No listing content has been provided yet."
        if source_text:
            try:
                self.rag.ingest(request.document_id, source_text, {"source": "inline"})
            except Exception:
                pass
        try:
            chunks = self.rag.retrieve(request.document_id, query, k=min(4, request.num_questions + 1))
        except Exception:
            chunks = []
        joined = "\n\n".join(chunk.text for chunk in chunks) or effective_text

        prompt = f"""
Generate {request.num_questions} multiple-choice quiz questions from this real estate listing content.
Return ONLY valid JSON with this schema:
{{
  "questions": [
    {{
      "question_id": "string",
      "question": "string",
      "answer_type": "multiple_choice",
      "options": ["exactly four answer choices"],
      "source_chunks": ["supporting text snippet 1", "supporting text snippet 2"]
    }}
  ]
}}

Content:
{joined}
"""
        payload = self.groq.complete_json(
            system="You build targeted real estate learning quizzes from source content.",
            user=prompt,
        )

        questions: list[QuizQuestion] = []
        raw_questions = payload.get("questions", [])
        if not isinstance(raw_questions, list):
            raw_questions = []

        for raw in raw_questions:
            if not isinstance(raw, dict):
                continue
            question_id = raw.get("question_id") or uuid.uuid4().hex[:8]
            question = QuizQuestion(
                question_id=question_id,
                question=raw.get("question", "What is the key fact from the listing?"),
                answer_type="multiple_choice",
                options=self._normalize_options(raw.get("options", []), joined),
                source_chunks=list(raw.get("source_chunks", [])),
            )
            questions.append(question)
            self.sessions.upsert_question(request.document_id, question.question_id, question.model_dump())

        if not questions:
            questions = self._fallback_questions(request.document_id, joined, request.num_questions)
        if not questions:
            questions = [
                QuizQuestion(
                    question_id=f"{request.document_id}-1",
                    question="What is the key pricing or availability detail from the listing?",
                    answer_type="multiple_choice",
                    options=[
                        "The asking price and availability date",
                        "The contact email only",
                        "The HOA fee only",
                        "The number of parking spaces only",
                    ],
                    source_chunks=[joined],
                )
            ]

        session = QuizSession(document_id=request.document_id)
        session.questions = {q.question_id: q.model_dump() for q in questions}
        self.sessions.set_session(request.document_id, session)
        return QuizSet(document_id=request.document_id, questions=questions)

    def evaluate(self, request: QuizAnswerRequest) -> QuizEvaluation:
        session = self.sessions.get_session(request.document_id)
        source_context = ""
        options = []
        if session:
            question_meta = session.questions.get(request.question_id, {})
            source_context = "\n".join(question_meta.get("source_chunks", []))
            options = list(question_meta.get("options", []))

        prompt = f"""
Evaluate the following learner answer against the real estate source context.
Return ONLY valid JSON with:
{{
  "score": 0-100,
  "is_correct": true|false,
  "verdict": "one sentence verdict",
  "explanation": "clear explanation, especially for incorrect answers",
  "ideal_answer": "what the correct answer should contain",
  "source_support": "cite the relevant listing detail"
}}

Question: {request.question}
Options: {options}
Selected answer: {request.answer}
Source context:
{source_context}
"""
        payload = self.groq.complete_json(
            system="You are a precise real estate tutor who explains mistakes clearly.",
            user=prompt,
        )

        if "score" not in payload:
            return self._fallback_evaluation(request, source_context)

        try:
            score = float(payload.get("score", 0))
        except (TypeError, ValueError):
            score = 0.0

        return QuizEvaluation(
            question_id=request.question_id,
            score=score,
            is_correct=bool(payload.get("is_correct", False)),
            verdict=payload.get("verdict", "Review the listing again."),
            explanation=payload.get("explanation", "Compare your answer against the listing details."),
            ideal_answer=payload.get("ideal_answer", ""),
            source_support=payload.get("source_support", source_context[:300]),
        )

    def _fallback_questions(self, document_id: str, text: str, num_questions: int) -> list[QuizQuestion]:
        snippets = [snippet.strip() for snippet in re.split(r"[.!?]\s+", text) if snippet.strip()]
        questions: list[QuizQuestion] = []
        for index, snippet in enumerate(snippets[:num_questions]):
            question_id = f"{document_id}-{index+1}"
            questions.append(
                QuizQuestion(
                    question_id=question_id,
                    question=f"What key detail is stated in this listing snippet: '{snippet[:120]}'?",
                    answer_type="multiple_choice",
                    options=[
                        snippet[:120].strip() or "The main listing detail",
                        "A contact detail only",
                        "An unrelated financing detail",
                        "A random property amenity",
                    ],
                    source_chunks=[snippet],
                )
            )
        return questions

    def _normalize_options(self, options: list[str], context: str) -> list[str]:
        cleaned = [opt.strip() for opt in options if isinstance(opt, str) and opt.strip()]
        if len(cleaned) >= 4:
            return cleaned[:4]

        if not cleaned:
            cleaned = []

        fallback_pool = [
            "The asking price and availability",
            "The contact email or phone number",
            "The property address or location",
            "The HOA fee or taxes",
            "The number of bedrooms or parking spaces",
            "The wrong listing reference",
        ]
        for candidate in fallback_pool:
            if len(cleaned) >= 4:
                break
            if candidate not in cleaned:
                cleaned.append(candidate)

        while len(cleaned) < 4:
            cleaned.append(f"Option {len(cleaned) + 1}")

        return cleaned[:4]

    def _fallback_evaluation(self, request: QuizAnswerRequest, source_context: str) -> QuizEvaluation:
        answer = request.answer.lower()
        support = source_context.lower()
        overlap = sum(1 for token in answer.split() if token in support)
        score = min(100.0, max(25.0, overlap * 12.5))
        is_correct = score >= 70
        return QuizEvaluation(
            question_id=request.question_id,
            score=score,
            is_correct=is_correct,
            verdict="Correct" if is_correct else "Incorrect",
            explanation=(
                "Your selected option matches the listing details."
                if is_correct
                else "Your selected option does not match the listing details. Recheck the source chunk for the exact fact."
            ),
            ideal_answer="Use the exact facts from the listing chunks.",
            source_support=source_context[:300],
        )
