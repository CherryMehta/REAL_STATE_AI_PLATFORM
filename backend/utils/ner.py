from __future__ import annotations

import re
from functools import lru_cache

from app.models.schemas import EntityItem

try:
    import spacy
except ImportError:  # pragma: no cover - optional dependency in some environments
    spacy = None


NOISE_VALUES = {
    "and",
    "availability",
    "date",
    "bhk",
    "id",
    "id and",
    "move-in date",
    "move in date",
    "listing id",
    "listing id and",
    "id and availability",
    "id an",
}

SPACY_LABEL_MAP = {
    "DATE": "date",
    "TIME": "date",
    "MONEY": "budget",
    "GPE": "location",
    "LOC": "location",
}


def _append_unique(entities: list[EntityItem], entity: EntityItem) -> None:
    key = (entity.label, entity.value.lower())
    for existing in entities:
        if (existing.label, existing.value.lower()) == key:
            return
    entities.append(entity)


def _normalize(value: str) -> str:
    value = value.replace("\u2013", "-").replace("\u2014", "-")
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\n\r,.;:()[]{}\"'")


def _clean_value(value: str) -> str:
    value = _normalize(value)
    value = re.sub(r"^(?:in|at|near|around)\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+(?:and|or|with)$", "", value, flags=re.IGNORECASE)
    return _normalize(value)


def _is_noise_value(value: str) -> bool:
    lowered = value.lower().strip()
    if lowered in NOISE_VALUES:
        return True
    if lowered.startswith("and "):
        return True
    if lowered.endswith(" and"):
        return True
    return False


def _is_meaningful_value(value: str, label: str) -> bool:
    if not value or _is_noise_value(value):
        return False

    lowered = value.lower()
    if label not in {"email", "phone"} and any(token in lowered.split() for token in {"and", "or"}):
        return False
    if label not in {"identifier", "email", "phone", "date", "budget"} and len(lowered) < 3:
        return False
    if label == "identifier" and not re.search(r"\d", value):
        return False
    if label == "location" and lowered in {"tx", "ca", "ny", "fl", "uk", "us"}:
        return False
    return True


@lru_cache(maxsize=1)
def _get_spacy_nlp():
    if spacy is None:
        return None

    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        nlp = spacy.blank("en")
        if "entity_ruler" not in nlp.pipe_names:
            ruler = nlp.add_pipe("entity_ruler")
            ruler.add_patterns(
                [
                    {
                        "label": "GPE",
                        "pattern": [
                            {
                                "LOWER": {
                                    "IN": [
                                        "indore",
                                        "bhopal",
                                        "mumbai",
                                        "pune",
                                        "delhi",
                                        "bengaluru",
                                        "hyderabad",
                                        "chennai",
                                        "kolkata",
                                    ]
                                }
                            }
                        ],
                    },
                    {"label": "GPE", "pattern": [{"LOWER": "vijay"}, {"LOWER": "nagar"}]},
                    {"label": "MONEY", "pattern": [{"TEXT": {"REGEX": r"^\$\d[\d,]*(?:\.\d+)?$"}}]},
                    {"label": "DATE", "pattern": [{"TEXT": {"REGEX": r"^\d{4}-\d{2}-\d{2}$"}}]},
                ]
            )
        return nlp


def sanitize_entities(entities: list[EntityItem]) -> list[EntityItem]:
    filtered: list[EntityItem] = []
    for entity in entities:
        value = _clean_value(entity.value)
        if not _is_meaningful_value(value, entity.label):
            continue

        if entity.label in {"date", "move_in_timeline"} and value.lower() in {"availability", "date", "id and"}:
            continue

        filtered.append(EntityItem(label=entity.label, value=value, confidence=entity.confidence))

    return filtered


def _extract_spacy_entities(text: str) -> list[EntityItem]:
    nlp = _get_spacy_nlp()
    if nlp is None:
        return []

    entities: list[EntityItem] = []
    try:
        doc = nlp(text)
    except Exception:
        return []

    for ent in doc.ents:
        label = SPACY_LABEL_MAP.get(ent.label_)
        if label is None:
            continue

        value = _clean_value(ent.text)
        if not _is_meaningful_value(value, label):
            continue

        confidence = 0.9 if ent.label_ in {"GPE", "LOC", "DATE"} else 0.88
        if ent.label_ == "MONEY":
            confidence = 0.94
        _append_unique(entities, EntityItem(label=label, value=value, confidence=confidence))

    return entities


def extract_entities(text: str) -> list[EntityItem]:
    entities: list[EntityItem] = []

    for entity in _extract_spacy_entities(text):
        _append_unique(entities, entity)

    # Strong, domain-specific rules first.
    for match in re.finditer(r"\b(?:RE|LISTING|PROP)-?\d+[A-Z0-9-]*\b", text, flags=re.IGNORECASE):
        value = _clean_value(match.group(0))
        if _is_meaningful_value(value, "identifier"):
            _append_unique(entities, EntityItem(label="identifier", value=value, confidence=0.98))

    for match in re.finditer(r"\b\d+\s?or\s?\d+\s?BHK\b", text, flags=re.IGNORECASE):
        value = _clean_value(match.group(0)).upper()
        if _is_meaningful_value(value, "property_type_range"):
            _append_unique(entities, EntityItem(label="property_type_range", value=value, confidence=0.97))

    for match in re.finditer(r"\b\d+\s?BHK\b", text, flags=re.IGNORECASE):
        value = _clean_value(match.group(0)).upper()
        if _is_meaningful_value(value, "property_type"):
            _append_unique(entities, EntityItem(label="property_type", value=value, confidence=0.97))

    for match in re.finditer(
        r"(?:\b(?:[$]|\u20b9|rs\.?|inr\s*)\d[\d,]*(?:\.\d+)?(?:\s?(?:-|to)\s?\d[\d,]*(?:\.\d+)?)?\b|\b\d[\d,]*(?:\.\d+)?\s?(?:lakhs?|lakh|crores?|crore|cr|k|m|million|billion)\b)",
        text,
        flags=re.IGNORECASE,
    ):
        value = _clean_value(match.group(0)).replace(" to ", "-")
        if re.search(r"\d", value) and _is_meaningful_value(value, "budget"):
            _append_unique(entities, EntityItem(label="budget", value=value, confidence=0.96))

    for match in re.finditer(
        r"\b(?:within\s+the\s+next\s+\d+\s+(?:days?|weeks?|months?)|this\s+week|next\s+week|this\s+month|next\s+month)\b",
        text,
        flags=re.IGNORECASE,
    ):
        value = _clean_value(match.group(0))
        if _is_meaningful_value(value, "move_in_timeline"):
            _append_unique(entities, EntityItem(label="move_in_timeline", value=value, confidence=0.95))

    for match in re.finditer(r"\b(?:Indore|Vijay Nagar|Bhopal|Mumbai|Pune|Delhi|Bengaluru|Hyderabad|Chennai|Kolkata)\b", text, flags=re.IGNORECASE):
        value = _clean_value(match.group(0))
        if _is_meaningful_value(value, "location"):
            _append_unique(entities, EntityItem(label="location", value=value, confidence=0.95))

    for match in re.finditer(r"\b(?:nearby areas?|surrounding areas?|adjacent areas?)\b", text, flags=re.IGNORECASE):
        value = _clean_value(match.group(0))
        if _is_meaningful_value(value, "location_scope"):
            _append_unique(entities, EntityItem(label="location_scope", value=value, confidence=0.8))

    # Supportive contact and reference details.
    for match in re.finditer(r"\b\d{4}-\d{2}-\d{2}\b", text):
        value = _clean_value(match.group(0))
        if _is_meaningful_value(value, "date"):
            _append_unique(entities, EntityItem(label="date", value=value, confidence=0.92))

    for match in re.finditer(r"\b\d{2}/\d{2}/\d{4}\b", text):
        value = _clean_value(match.group(0))
        if _is_meaningful_value(value, "date"):
            _append_unique(entities, EntityItem(label="date", value=value, confidence=0.92))

    for match in re.finditer(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}\b", text, flags=re.IGNORECASE):
        value = _clean_value(match.group(0))
        if _is_meaningful_value(value, "date"):
            _append_unique(entities, EntityItem(label="date", value=value, confidence=0.92))

    for match in re.finditer(r"\b[\w.\-+]+@[\w.-]+\.\w+\b", text):
        value = _clean_value(match.group(0))
        if _is_meaningful_value(value, "email"):
            _append_unique(entities, EntityItem(label="email", value=value, confidence=0.98))

    for match in re.finditer(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", text):
        value = _clean_value(match.group(0))
        if _is_meaningful_value(value, "phone"):
            _append_unique(entities, EntityItem(label="phone", value=value, confidence=0.93))

    return sanitize_entities(entities)
