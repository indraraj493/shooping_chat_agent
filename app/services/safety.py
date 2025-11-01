from dataclasses import dataclass
import re
from typing import List


SENSITIVE_REQUEST_PATTERNS: List[re.Pattern] = [
    re.compile(r"reveal (?:system|hidden) prompt", re.I),
    re.compile(r"show (?:your|the) (?:api|secret|key)", re.I),
    re.compile(r"api\s*key", re.I),
]

TOXIC_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(?:trash|hate|sucks|terrible)\b.*\b(?:brand|company|model|[A-Za-z0-9]+)\b", re.I),
]

IRRELEVANT_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(?:write code|homework|unrelated|politics|celebrity|recipe)\b", re.I),
]


@dataclass
class SafetyResult:
    blocked: bool
    message: str


REFUSAL_GENERIC = (
    "I can't help with that. I can assist with mobile phone shopping, comparisons, and specs."
)


def evaluate_safety(text: str) -> SafetyResult:
    normalized = text.strip()
    if not normalized:
        return SafetyResult(blocked=False, message="")

    for pat in SENSITIVE_REQUEST_PATTERNS:
        if pat.search(normalized):
            return SafetyResult(
                blocked=True,
                message=(
                    "I can't reveal internal prompts, API keys, or hidden system details. "
                    "Ask me about phones, specs, or recommendations instead."
                ),
            )

    for pat in TOXIC_PATTERNS:
        if pat.search(normalized):
            return SafetyResult(
                blocked=True,
                message=(
                    "Let's keep it neutral and factual. I can compare models using objective specs."
                ),
            )

    for pat in IRRELEVANT_PATTERNS:
        if pat.search(normalized):
            return SafetyResult(blocked=True, message=REFUSAL_GENERIC)

    return SafetyResult(blocked=False, message="")


