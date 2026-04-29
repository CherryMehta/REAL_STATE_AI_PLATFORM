from __future__ import annotations

try:
    from crewai import Task
except ImportError:  # pragma: no cover
    Task = None


def build_tasks(bundle, message: str):
    if Task is None or bundle.classifier is None:
        return []

    classifier_task = Task(
        description=(
            "Analyze the following incoming real estate communication and return ONLY valid JSON.\n"
            "Message:\n"
            f"{message}\n\n"
            "JSON schema:\n"
            "{"
            '"urgency":"low|medium|high|critical",'
            '"intent":"short intent label",'
            '"route":"team or workflow route",'
            '"summary":"1-2 sentence summary",'
            '"rationale":"why the urgency/intent were selected"'
            "}"
        ),
        expected_output="A JSON object with urgency, intent, route, summary, and rationale.",
        agent=bundle.classifier,
    )

    extractor_task = Task(
        description=(
            "Extract identifiers, dates, addresses, dollar amounts, emails, phone numbers, and property references. "
            "Return ONLY valid JSON in this exact shape: {\"entities\":[{\"label\":\"...\",\"value\":\"...\",\"confidence\":0.0}]}\n"
            f"Message:\n{message}"
        ),
        expected_output='A JSON object shaped like {"entities":[...]}',
        agent=bundle.extractor,
    )

    responder_task = Task(
        description=(
            "Synthesize the full triage result using the prior task outputs. "
            "Return ONLY valid JSON with urgency, intent, route, summary, rationale, entities, draft_response, next_action, and confidence. "
            "The response should be concise, professional, and based on the classification and entities."
        ),
        expected_output=(
            'A JSON object with keys urgency, intent, route, summary, rationale, entities, '
            "draft_response, next_action, and confidence."
        ),
        agent=bundle.responder,
        context=[classifier_task, extractor_task],
    )
    return [classifier_task, extractor_task, responder_task]
