"""How the evidence reads: tool names, citations, a specialist's numbers and its outcome. Plain functions."""

import re

from api.models import Finding, Source

# The orchestrator's tools, by the name the farmer should see.
STEPS = {
    "list_fields": "Looked up your registered fields",
    "save_requirements": "Saved what you need to memory",
    "ask_weather_agent": "Weather agent",
    "ask_farm_context_agent": "Farm context agent",
    "ask_knowledge_agent": "Knowledge agent",
    "ask_advisory_agent": "Advisory agent",
}
# Which finding each specialist leaves behind. Advisory leaves none: its work is the answer.
FINDING_OF = {"ask_weather_agent": "weather", "ask_farm_context_agent": "farm_context", "ask_knowledge_agent": "knowledge"}
FINDING_TITLES = {"weather": "Weather", "farm_context": "Farm context", "knowledge": "Knowledge"}

# A citation the knowledge agent leaves in its text: [cg-06-fertiliser-…-5] or [cg-06-…-5, cg-07-…-2].
CITATION = re.compile(r"\s*\[([a-z]+-\d+[\w-]*(?:,\s*[a-z]+-\d+[\w-]*)*)\]")

# Data keys that are shown elsewhere (the sources) or say nothing to a farmer.
HIDDEN_KEYS = {"field_id", "citations", "found"}


def guide(identifier: str) -> str:
    """The guide a passage or file belongs to: 'cg-06-fertiliser-…-5' and 'CG-06_fertiliser….pdf' → 'cg-06'."""
    return "-".join(re.split(r"[-_]", identifier.lower())[:2])


def cite(text: str, sources: list[Source]) -> str:
    """Replaces citation ids with short markers: [1] for a source in the list, else the guide, [CG-06]."""
    numbers: dict[str, int] = {}
    for number, source in enumerate(sources, 1):
        numbers.setdefault(source.id, number)
        numbers.setdefault(guide(source.source), number)

    def markers(match: re.Match) -> str:
        labels = []
        for citation in re.split(r",\s*", match.group(1)):
            label = str(numbers.get(citation) or numbers.get(guide(citation)) or guide(citation).upper())
            if label not in labels:
                labels.append(label)
        return " " + "".join(f"[{label}]" for label in labels)

    return CITATION.sub(markers, text)


def metric(key: str, value) -> tuple[str, str]:
    """A data key and value, readable: rainfall_last_7_days_mm, 112.0 → 'Rainfall last 7 days', '112 mm'."""
    unit = ""
    if key.endswith("_mm"):
        key, unit = key[:-3], " mm"
    elif key.endswith("_percentage"):
        key, unit = key[: -len("_percentage")], "%"
    label = re.sub(r"\bndvi\b", "NDVI", key.replace("_", " ").capitalize(), flags=re.IGNORECASE)
    if isinstance(value, bool):
        text = "Yes" if value else "No"
    elif isinstance(value, float):
        text = f"{value:g}{unit}"
    else:
        text = f"{value}{unit}".replace("_", " ")
    return label, text


def status(finding: Finding) -> str:
    """A specialist's outcome: it found something, it had no data, or the guides do not cover it."""
    if not finding.ok:
        return "No data"
    if not finding.covered:
        return "Not in the guides"
    return "Done"


def evidence(finding: Finding, sources: list[Source]) -> str:
    """A specialist's summary, then its numbers on one line."""
    numbers = [
        "{} **{}**".format(*metric(key, value))
        for key, value in finding.data.items()
        if key not in HIDDEN_KEYS and not isinstance(value, dict | list)
    ]
    text = cite(finding.summary, sources)
    return f"{text}\n\n{' · '.join(numbers)}" if numbers else text
