from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings

try:
    from crewai import Agent, LLM
except ImportError:  # pragma: no cover - fallback when CrewAI internals differ
    Agent = None
    LLM = None


@dataclass(slots=True)
class TriageAgentBundle:
    classifier: object
    extractor: object
    responder: object
    llm: object | None


def build_llm() -> object | None:
    settings = get_settings()
    if LLM is None or not settings.groq_api_key:
        return None
    try:
        return LLM(model=f"groq/{settings.resolved_groq_model}", api_key=settings.groq_api_key)
    except Exception:
        return None


def build_agents() -> TriageAgentBundle:
    llm = build_llm()

    if Agent is None or llm is None:
        return TriageAgentBundle(classifier=None, extractor=None, responder=None, llm=llm)

    try:
        classifier = Agent(
            role="Real Estate Triage Classifier",
            goal="Classify incoming real estate messages by intent and urgency.",
            backstory="You are a senior operations assistant for a real estate team.",
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )
        extractor = Agent(
            role="Real Estate Entity Extractor",
            goal="Extract critical identifiers, dates, locations, and contact details from the message.",
            backstory="You produce reliable structured extraction output for downstream automation.",
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )
        responder = Agent(
            role="Real Estate Response Writer",
            goal="Draft a concise, helpful first-response message grounded in the extracted context.",
            backstory="You write production-ready drafts that are accurate, polite, and action-oriented.",
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )
    except Exception:
        return TriageAgentBundle(classifier=None, extractor=None, responder=None, llm=llm)
    return TriageAgentBundle(classifier=classifier, extractor=extractor, responder=responder, llm=llm)
