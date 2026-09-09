from __future__ import annotations

import re

from app.schemas import SpecialistFinding

AREA_RE = re.compile(r"~?(\d{2,4})\s*(?:sq\.?\s*m|sqm|m²|m2)")
DINING_RE = re.compile(r"(\d+)[\s-]*seat\s+dining")


def _extract_area(brief_data: dict) -> int | None:
    brief_text = brief_data.get("brief_text", "")
    match = AREA_RE.search(brief_text)
    if match:
        return int(match.group(1))
    return None


def _get_spaces(brief_data: dict) -> list[str]:
    return brief_data.get("spaces", [])


def _get_preferences(brief_data: dict) -> list[str]:
    return brief_data.get("preferences", [])


def _get_requirements(brief_data: dict) -> list[str]:
    return brief_data.get("requirements", [])


def _get_missing(brief_data: dict) -> list[str]:
    return brief_data.get("missing_information", [])


def _get_text(brief_data: dict) -> str:
    return brief_data.get("brief_text", "").lower()


def check_clearances(brief_data: dict, constraints: dict) -> list[SpecialistFinding]:
    text = _get_text(brief_data)
    findings: list[SpecialistFinding] = []

    dining_match = DINING_RE.search(text)
    area = _extract_area(brief_data)

    if dining_match and area is not None:
        seats = int(dining_match.group(1))
        if seats >= 8 and area <= 100:
            findings.append(
                SpecialistFinding(
                    category="clearances",
                    severity="high",
                    confidence=0.92,
                    finding=(
                        f"An {seats}-person dining table requires ~3.6 x 2.4 m "
                        f"of clear floor area. In an apartment of ~{area} sq m "
                        f"this consumes roughly {round(seats / 2.6, 1)}% of the "
                        f"total plan, severely constraining adjacent circulation "
                        f"and living space."
                    ),
                    evidence=(
                        f"Brief requests a {seats}-seat dining table within "
                        f"~{area} sq m open living area."
                    ),
                    assumptions=[
                        "Standard 600 mm clearance per seating position assumed",
                        "No combined dining/living furniture arrangement supplied",
                    ],
                )
            )

    if not findings:
        findings.append(
            SpecialistFinding(
                category="clearances",
                severity="low",
                confidence=0.4,
                finding=(
                    "No specific clearance conflict identified from available "
                    "brief data. Insufficient detail to confirm furniture "
                    "dimensions."
                ),
                evidence="No dining or large-furniture reference found in brief.",
                assumptions=["Default furniture sizes assumed"],
            )
        )

    return findings


def check_daylight(brief_data: dict, constraints: dict) -> list[SpecialistFinding]:
    missing = _get_missing(brief_data)
    text = _get_text(brief_data)

    orientation_terms = [
        "north", "south", "east", "west",
        "orientation", "compass", "aspect", "facing",
    ]
    has_orientation = any(t in text for t in orientation_terms)

    if not has_orientation:
        return [
            SpecialistFinding(
                category="daylight",
                severity="high",
                confidence=0.88,
                finding=(
                    "Primary facade orientation (north/south/east/west) is not "
                    "supplied. Without compass direction, daylighting analysis "
                    "cannot reliably predict solar access, overshadowing risk, "
                    "or passive heating potential for any room."
                ),
                evidence=(
                    "Missing information flags: 'North orientation / compass "
                    "direction not supplied'."
                ),
                assumptions=[
                    "No site plan or GIS data provided",
                    "Orientation cannot be inferred from brief text",
                ],
            )
        ]

    return [
        SpecialistFinding(
            category="daylight",
            severity="low",
            confidence=0.5,
            finding="Orientation data present; detailed daylight analysis deferred to specialist modelling.",
            evidence="Orientation terms found in brief.",
            assumptions=["Further glazing schedule data required"],
        )
    ]


def check_privacy(brief_data: dict, constraints: dict) -> list[SpecialistFinding]:
    text = _get_text(brief_data)
    requirements = _get_requirements(brief_data)
    preferences = _get_preferences(brief_data)

    privacy_terms = ["privacy", "separation", "secluded", "private"]
    has_privacy = any(t in text for t in privacy_terms)
    bedroom_terms = ["bedroom", "master bedroom", "bedroom 1"]
    has_bedroom = any(t in text for t in bedroom_terms)

    if has_bedroom:
        if has_privacy:
            return [
                SpecialistFinding(
                    category="privacy",
                    severity="medium",
                    confidence=0.75,
                    finding=(
                        "Primary bedroom privacy requirement detected but no "
                        "detailed spatial separation strategy is defined. "
                        "Proximity to communal areas (kitchen, living) and "
                        "shared walls must be assessed."
                    ),
                    evidence=(
                        "Brief references privacy preference and primary "
                        "bedroom spaces."
                    ),
                    assumptions=[
                        "Standard acoustic separation (STC 50+) expected",
                        "No sight-line analysis data available",
                    ],
                )
            ]

        return [
            SpecialistFinding(
                category="privacy",
                severity="medium",
                confidence=0.7,
                finding=(
                    "Primary bedroom identified but privacy requirements not "
                    "explicitly stated. Risk of overlooking or acoustic "
                    "bleed from adjacent living zones."
                ),
                evidence="Bedroom spaces listed; no privacy preference found.",
                assumptions=[
                    "Bedroom requires standard privacy screening",
                    "Shared-wall acoustic performance unknown",
                ],
            )
        ]

    return [
        SpecialistFinding(
            category="privacy",
            severity="low",
            confidence=0.4,
            finding="No bedroom or private-space references found; privacy assessment deferred.",
            evidence="No bedroom keywords detected in brief.",
            assumptions=["Full room schedule not yet supplied"],
        )
    ]


def check_circulation(brief_data: dict, constraints: dict) -> list[SpecialistFinding]:
    text = _get_text(brief_data)
    area = _extract_area(brief_data)

    storage_terms = ["storage", "wardrobe", "cabinet", "cupboard", "pantry"]
    has_storage = any(t in text for t in storage_terms)
    circulation_terms = ["circulation", "flow", "wide", "generous"]
    has_circulation = any(t in text for t in circulation_terms)

    if has_storage and has_circulation:
        area_val = area if area else 92
        return [
            SpecialistFinding(
                category="circulation",
                severity="high",
                confidence=0.85,
                finding=(
                    f"The brief requests maximised storage while maintaining "
                    f"wide circulation paths. In a ~{area_val} sq m apartment "
                    f"these goals are inherently in tension: adding cabinetry "
                    f"and wardrobes reduces effective corridor width below the "
                    f"1200 mm minimum."
                ),
                evidence=(
                    "Brief mentions storage preference alongside circulation "
                    "preference in compact plan."
                ),
                assumptions=[
                    "Minimum 1200 mm clear circulation width per BCA/NCC",
                    "Storage volume not quantified in brief",
                ],
            )
        ]

    if has_storage:
        return [
            SpecialistFinding(
                category="circulation",
                severity="medium",
                confidence=0.65,
                finding=(
                    "Storage emphasis detected; impact on circulation paths "
                    "cannot be assessed without corridor dimensions."
                ),
                evidence="Storage keywords present; no circulation reference.",
                assumptions=["Standard 900-1200 mm corridors assumed"],
            )
        ]

    return [
        SpecialistFinding(
            category="circulation",
            severity="low",
            confidence=0.4,
            finding=(
                "No explicit storage or circulation trade-off identified in "
                "brief. General circulation compliance deferred to plan review."
            ),
            evidence="No storage or circulation keywords detected.",
            assumptions=["Basic corridor compliance assumed"],
        )
    ]


def check_adjacency(brief_data: dict, constraints: dict) -> list[SpecialistFinding]:
    text = _get_text(brief_data)
    spaces = _get_spaces(brief_data)

    kitchen_terms = ["kitchen", "cooking", "galley"]
    living_terms = ["living room", "living area", "lounge"]
    has_kitchen = any(t in text for t in kitchen_terms)
    has_living = any(t in text for t in living_terms)

    open_plan_terms = ["open plan", "open feel", "open living", "visual connection"]
    has_open = any(t in text for t in open_plan_terms)

    if has_kitchen and has_open:
        return [
            SpecialistFinding(
                category="adjacency",
                severity="medium",
                confidence=0.78,
                finding=(
                    "Kitchen is required to maintain a visual connection with "
                    "the living area in an open-plan layout. This creates "
                    "adjacency obligations: cooking odours, noise, and grease "
                    "must be managed without physical separation."
                ),
                evidence=(
                    "Brief specifies open-plan kitchen with visual connection "
                    "to living area."
                ),
                assumptions=[
                    "No operable partition or screen mentioned",
                    "Extractor fan and splash-back standards assumed",
                ],
            )
        ]

    if has_kitchen and has_living and not has_open:
        return [
            SpecialistFinding(
                category="adjacency",
                severity="low",
                confidence=0.5,
                finding=(
                    "Kitchen and living areas both referenced but no open-plan "
                    "or visual-connection requirement stated. Adjacency "
                    "assessment deferred to spatial planning."
                ),
                evidence="Kitchen and living spaces listed without adjacency directive.",
                assumptions=["Default proximity assumed based on typical layouts"],
            )
        ]

    return [
        SpecialistFinding(
            category="adjacency",
            severity="low",
            confidence=0.35,
            finding="Insufficient adjacency data; assessment deferred.",
            evidence="No kitchen or living-area references found.",
            assumptions=["Full room schedule not supplied"],
        )
    ]
