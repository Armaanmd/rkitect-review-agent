from pydantic import BaseModel, Field
from typing import Optional


class ReviewRequest(BaseModel):
    brief: str
    constraints: Optional[dict] = None
    plan_data: Optional[dict | str] = None


class SpecialistFinding(BaseModel):
    category: str = Field(..., pattern="^(circulation|daylight|privacy|clearances|adjacency)$")
    severity: str = Field(..., pattern="^(high|medium|low)$")
    confidence: float
    finding: str
    evidence: str
    assumptions: list[str]


class Recommendation(BaseModel):
    id: str
    title: str
    description: str
    impact: str
    requires_human_approval: bool
    decision_status: str = "pending"


class ReviewResponse(BaseModel):
    run_id: str
    status: str
    structured_brief: dict
    missing_information: list[str]
    contradictions: list[str]
    specialist_findings: list[SpecialistFinding]
    recommendations: list[Recommendation]


class DecisionRequest(BaseModel):
    recommendation_id: str
    action: str = Field(..., pattern="^(accept|reject)$")
