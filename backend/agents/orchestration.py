from __future__ import annotations

import json

from app.agents.triage_agents import build_agents
from app.agents.triage_tasks import build_tasks
from app.models.schemas import EntityItem, TriageAnalysis, TriageResponse
from app.services.groq_client import GroqClient
from app.utils.ner import extract_entities

try:
    from crewai import Crew, Process
except ImportError:  # pragma: no cover
    Crew = None
    Process = None


def _safe_json(value: str | dict | None) -> dict:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    cleaned = value.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {}


class TriageOrchestrator:
    def __init__(self) -> None:
        self.groq = GroqClient()

    def _fallback(self, message: str) -> TriageResponse:
        entities = extract_entities(message)
        lowered = message.lower()
        urgency = "critical" if any(word in lowered for word in ["evict", "fraud", "legal", "urgent", "immediately"]) else "high" if any(word in lowered for word in ["today", "asap", "same day"]) else "medium" if any(word in lowered for word in ["soon", "follow up"]) else "low"
        intent = "lead_follow_up" if any(word in lowered for word in ["showing", "tour", "visit"]) else "lease_support" if "lease" in lowered else "general_inquiry"
        route = "sales" if intent == "lead_follow_up" else "operations"
        analysis = TriageAnalysis(
            urgency=urgency,  # type: ignore[arg-type]
            intent=intent,
            route=route,
            summary="The message has been reviewed using the basic rule-based checker.",
            rationale="The checker looked for urgent words, listing references, dates, locations, and follow-up clues.",
            entities=entities,
        )
        draft = "Thanks for reaching out. We received your message and are reviewing the details now. We'll follow up shortly with the next best step."
        try:
            generated = self.groq.complete(
                system="You draft concise, professional real estate first responses.",
                user=(
                    "Create a helpful first reply for this real estate message. "
                    "Use any listing ID, date, location, or timeline details from the message. "
                    "Return plain text only.\n\n"
                    f"Message:\n{message}"
                ),
            )
            if generated and "api key is missing" not in generated.lower():
                draft = generated
        except Exception:
            pass
        return TriageResponse(analysis=analysis, draft_response=draft, next_action="Route to the assigned real estate queue.", confidence=0.62)

    def analyze(self, message: str) -> TriageResponse:
        bundle = build_agents()
        tasks = build_tasks(bundle, message)

        if Crew is None or Process is None or not tasks or bundle.llm is None:
            return self._fallback(message)

        try:
            crew = Crew(
                agents=[bundle.classifier, bundle.extractor, bundle.responder],
                tasks=tasks,
                process=Process.sequential,
                verbose=False,
            )
            result = crew.kickoff()
            raw = getattr(result, "raw", str(result))
        except Exception:
            return self._fallback(message)

        if "{" not in raw:
            return self._fallback(message)

        parsed = _safe_json(raw)
        entities = extract_entities(message)

        urgency = str(parsed.get("urgency", "medium")).lower()
        if urgency not in {"low", "medium", "high", "critical"}:
            urgency = "medium"

        analysis = TriageAnalysis(
            urgency=urgency,
            intent=parsed.get("intent", "general_inquiry"),
            route=parsed.get("route", "operations"),
            summary=parsed.get("summary", ""),
            rationale=parsed.get("rationale", ""),
            entities=entities,
        )

        draft_response = parsed.get("draft_response") or "Thanks for the update. We are reviewing this and will respond shortly."
        if "draft_response" not in parsed:
            draft_response = self.groq.complete(
                system="You draft concise, professional real estate first responses.",
                user=f"Create a helpful response for this message:\n{message}\nReturn plain text only.",
            )

        return TriageResponse(
            analysis=analysis,
            draft_response=draft_response,
            next_action=parsed.get("next_action", "Assign to the appropriate follow-up queue."),
            confidence=float(parsed.get("confidence", 0.78)),
        )
