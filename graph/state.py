from typing import Optional
from pydantic import BaseModel, Field
from tools.diff_parser import ParsedPR


# ── Individual agent output models ───────────────────────────────────────────

class SecurityFinding(BaseModel):
    severity: str           # critical / high / medium / low
    title: str
    description: str
    file: str
    line_hint: Optional[str] = None
    recommendation: str


class LogicFinding(BaseModel):
    severity: str           # high / medium / low
    title: str
    description: str
    file: str
    suggestion: str


class TestCoverageResult(BaseModel):
    coverage_score: int     # 0–100 estimate
    missing_test_cases: list[str]
    untested_files: list[str]
    suggestions: list[str]


class DocumentationResult(BaseModel):
    score: int              # 0–100 estimate
    missing_docstrings: list[str]
    missing_type_hints: list[str]
    suggestions: list[str]


class FinalReview(BaseModel):
    summary: str
    overall_score: int      # 0–100
    recommendation: str     # APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION
    security_highlights: list[str]
    logic_highlights: list[str]
    top_suggestions: list[str]
    estimated_review_time_minutes: int


# ── The shared graph state ────────────────────────────────────────────────────

class ReviewState(BaseModel):
    """
    The single shared object every agent reads from and writes to.
    LangGraph passes this between nodes automatically.
    """

    # Input — set once at the start, never modified
    pr_url: str = ""
    parsed_pr: Optional[ParsedPR] = None

    # Agent outputs — each agent fills in its own section
    security_findings: list[SecurityFinding] = Field(default_factory=list)
    logic_findings: list[LogicFinding] = Field(default_factory=list)
    test_coverage: Optional[TestCoverageResult] = None
    documentation: Optional[DocumentationResult] = None

    # Synthesis output — filled last by the orchestrator
    final_review: Optional[FinalReview] = None

    # Execution metadata — for observability and debugging
    errors: list[str] = Field(default_factory=list)
    completed_agents: list[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True  # needed for ParsedPR dataclass