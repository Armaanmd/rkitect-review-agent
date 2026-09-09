from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.agent.brief_parser import parse_brief
from app.agent.specialists import (
    check_adjacency,
    check_circulation,
    check_clearances,
    check_daylight,
    check_privacy,
)
from app.agent.synthesizer import synthesize_findings
from app.schemas import (
    DecisionRequest,
    ReviewRequest,
    ReviewResponse,
    SpecialistFinding,
)
from app.state import get_review, save_review

app = FastAPI(title="rkitect.ai Agentic Review API")


@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "service": "rkitect-agent"}


@app.post("/v1/reviews", response_model=ReviewResponse)
def create_review(request: ReviewRequest) -> ReviewResponse:
    run_id = uuid4().hex
    parsed = parse_brief(request.brief, request.constraints)

    specialists = [
        check_clearances,
        check_circulation,
        check_adjacency,
        check_daylight,
        check_privacy,
    ]

    brief_data = {
        "brief_text": request.brief,
        "spaces": parsed["structured_brief"]["spaces"],
        "requirements": parsed["structured_brief"]["requirements"],
        "preferences": parsed["structured_brief"]["preferences"],
        "missing_information": parsed["missing_information"],
        "contradictions": parsed["contradictions"],
    }
    constraints = request.constraints or {}

    findings: list[SpecialistFinding] = []
    for specialist in specialists:
        findings.extend(specialist(brief_data, constraints))

    review = ReviewResponse(
        run_id=run_id,
        status="completed",
        structured_brief=parsed["structured_brief"],
        missing_information=parsed["missing_information"],
        contradictions=parsed["contradictions"],
        specialist_findings=findings,
        recommendations=synthesize_findings(findings),
    )
    save_review(review)
    return review


@app.get("/v1/reviews/{run_id}", response_model=ReviewResponse)
def get_review_by_id(run_id: str) -> ReviewResponse:
    review = get_review(run_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@app.post("/v1/reviews/{run_id}/decisions")
def make_decision(run_id: str, request: DecisionRequest) -> dict:
    review = get_review(run_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    recommendation = next(
        (r for r in review.recommendations if r.id == request.recommendation_id),
        None,
    )
    if recommendation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Recommendation {request.recommendation_id} not found",
        )

    recommendation.decision_status = request.action
    save_review(review)
    return {
        "status": "success",
        "recommendation_id": request.recommendation_id,
        "new_status": request.action,
    }