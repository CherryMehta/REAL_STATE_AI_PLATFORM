from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class QuizSession:
    document_id: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    questions: dict[str, dict] = field(default_factory=dict)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, QuizSession] = {}

    def set_session(self, document_id: str, session: QuizSession) -> None:
        self._sessions[document_id] = session

    def get_session(self, document_id: str) -> QuizSession | None:
        return self._sessions.get(document_id)

    def upsert_question(self, document_id: str, question_id: str, payload: dict) -> None:
        session = self._sessions.setdefault(document_id, QuizSession(document_id=document_id))
        session.questions[question_id] = payload

