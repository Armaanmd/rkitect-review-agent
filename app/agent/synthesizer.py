from uuid import uuid4

from app.schemas import Recommendation, SpecialistFinding


def synthesize_findings(findings: list[SpecialistFinding]) -> list[Recommendation]:
    recommendations: list[Recommendation] = []
    for finding in findings:
        category = finding.category
        title = f"{category} Review Action"
        description = (
            f"{finding.finding} Evidence: {finding.evidence} "
            f"(assumptions: {', '.join(finding.assumptions) or 'none'})"
        )
        impact = (
            f"High impact - {finding.finding}"
            if finding.severity == "high"
            else f"Moderate impact - {finding.finding}"
            if finding.severity == "medium"
            else f"Low impact - {finding.finding}"
        )
        recommendation = Recommendation(
            id=uuid4().hex,
            title=title,
            description=description,
            impact=impact,
            requires_human_approval=(finding.severity == "high"),
            decision_status="pending",
        )
        recommendations.append(recommendation)
    return recommendations