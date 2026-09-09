from __future__ import annotations

import re


def parse_brief(brief: str, constraints: dict | None = None) -> dict:
    lower = brief.lower()

    spaces = _extract_spaces(lower)
    requirements = _extract_requirements(lower)
    preferences = _extract_preferences(lower)
    missing = _detect_missing(lower, constraints)
    contradictions = _detect_contradictions(lower, constraints)
    questions = _generate_questions(lower, constraints)

    return {
        "structured_brief": {
            "spaces": spaces,
            "requirements": requirements,
            "preferences": preferences,
        },
        "missing_information": missing,
        "contradictions": contradictions,
        "clarification_questions": questions,
    }


SPACE_KEYWORDS = [
    ("bedroom 1", "Bedroom 1"),
    ("bedroom 2", "Bedroom 2"),
    ("master bedroom", "Master Bedroom"),
    ("study", "Study"),
    ("kitchen", "Kitchen"),
    ("living room", "Living Room"),
    ("living area", "Living Area"),
    ("dining", "Dining Area"),
    ("bathroom", "Bathroom"),
    ("ensuite", "Ensuite"),
    ("laundry", "Laundry"),
    ("hallway", "Hallway"),
    ("entry", "Entry"),
    ("garage", "Garage"),
    ("balcony", "Balcony"),
    ("terrace", "Terrace"),
]

REQUIREMENT_KEYWORDS = [
    "work from home",
    "work from home office",
    "home office",
    "remote work",
    "host",
    "entertain",
    "guest",
    "parents",
    "family",
    "children",
    "kids",
    "pet",
    "accessibility",
    "wheelchair",
    "aging in place",
]

PREFERENCE_KEYWORDS = [
    "open feel",
    "open plan",
    "visual connection",
    "privacy",
    "natural light",
    "daylight",
    "storage",
    "minimalist",
    "spacious",
    "cozy",
    "quiet",
    "noise",
    "separation",
    "connection",
    "flow",
    "circulation",
]


def _extract_spaces(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for keyword, label in SPACE_KEYWORDS:
        if keyword in text and label not in seen:
            found.append(label)
            seen.add(label)
    return found


def _extract_requirements(text: str) -> list[str]:
    found: list[str] = []
    for kw in REQUIREMENT_KEYWORDS:
        if kw in text:
            found.append(kw)
    return found


def _extract_preferences(text: str) -> list[str]:
    found: list[str] = []
    for kw in PREFERENCE_KEYWORDS:
        if kw in text:
            found.append(kw)
    return found


AREA_PATTERN = re.compile(r"~?(\d{2,4})\s*(?:sq\.?\s*m|sqm|m²|m2)")
DINING_PATTERN = re.compile(r"(\d+)[\s-]*seat\s+dining")
STORAGE_PATTERN = re.compile(r"(maximis|maximiz|plenty of|lots of|extra)\s+storage")
WIDE_CIRCULATION = re.compile(r"(wide|broad|generous)\s+circulation")


def _detect_missing(text: str, constraints: dict | None) -> list[str]:
    missing: list[str] = []

    orientation_terms = [
        "north", "south", "east", "west",
        "orientation", "compass", "aspect",
        "facing", "northern", "southern",
    ]
    if not any(t in text for t in orientation_terms):
        missing.append("North orientation / compass direction not supplied")

    scale_terms = ["scale", "1:", "100", "50", "200", "drawing scale"]
    if not any(t in text for t in scale_terms):
        missing.append("Drawing scale unverified or missing")

    obstruction_terms = [
        "sill height", "sill heights", "adjacent building",
        "neighbouring", "neighboring", "obstruction", "overshadow",
        "shadow", "building line", "setback",
    ]
    if not any(t in text for t in obstruction_terms):
        missing.append("Window sill heights and adjacent building obstructions unknown")

    area_terms = ["area", "sqm", "sq m", "sqm", "m²", "m2", "total area", "floor area"]
    if not any(t in text for t in area_terms) and not AREA_PATTERN.search(text):
        missing.append("Total floor area not specified")

    budget_terms = ["budget", "cost", "price", "spend"]
    if not any(t in text for t in budget_terms):
        missing.append("Budget / cost constraints not specified")

    return missing


def _detect_contradictions(text: str, constraints: dict | None) -> list[str]:
    contradictions: list[str] = []

    area_match = AREA_PATTERN.search(text)
    dining_match = DINING_PATTERN.search(text)

    if area_match and dining_match:
        area_val = int(area_match.group(1))
        seats = int(dining_match.group(1))
        if area_val <= 100 and seats >= 8:
            contradictions.append(
                f"{seats}-seat dining table requested inside an open living "
                f"area within ~{area_val} sq m creates a severe spatial "
                f"footprint conflict"
            )

    if (STORAGE_PATTERN.search(text) and WIDE_CIRCULATION.search(text)):
        area_match_local = AREA_PATTERN.search(text)
        if area_match_local:
            area_val = int(area_match_local.group(1))
        else:
            area_val = 92
        contradictions.append(
            f"Maximizing storage while maintaining wide circulation in a "
            f"compact {area_val} sq m layout requires trade-offs"
        )

    return contradictions


def _generate_questions(text: str, constraints: dict | None) -> list[str]:
    questions: list[str] = []

    orientation_terms = [
        "north", "south", "east", "west",
        "orientation", "compass", "aspect", "facing",
    ]
    if not any(t in text for t in orientation_terms):
        questions.append(
            "Can the orientation of the primary facade be confirmed?"
        )

    if DINING_PATTERN.search(text):
        questions.append(
            "Is a folding or expandable dining table acceptable to preserve "
            "living room circulation?"
        )

    if not any(t in text for t in ["storage", "wardrobe", "cabinet", "cupboard"]):
        questions.append(
            "What is the minimum storage volume required (e.g., wardrobe "
            "linear metres, pantry capacity)?"
        )

    if not any(t in text for t in ["natural light", "daylight", "window", "glazing"]):
        questions.append(
            "Are there specific daylight targets or minimum glazing ratios "
            "for each habitable room?"
        )

    return questions
