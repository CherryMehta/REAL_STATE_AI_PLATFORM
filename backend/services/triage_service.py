from __future__ import annotations

from app.agents.orchestration import TriageOrchestrator
from app.models.schemas import TriageRequest, TriageResponse
from app.utils.ner import extract_entities, sanitize_entities


class TriageService:
    def __init__(self) -> None:
        self.orchestrator = TriageOrchestrator()

    def analyze(self, request: TriageRequest) -> TriageResponse:
        response = self.orchestrator.analyze(request.message)
        base_entities = extract_entities(request.message)
        extra_entities = sanitize_entities(response.analysis.entities or [])

        merged_entities = list(base_entities)
        seen = {(entity.label, entity.value.lower()) for entity in merged_entities}
        for entity in extra_entities:
            key = (entity.label, entity.value.lower())
            if key in seen:
                continue
            merged_entities.append(entity)
            seen.add(key)

        response.analysis.entities = merged_entities
        return response
