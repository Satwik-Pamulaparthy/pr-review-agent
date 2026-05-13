import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from graph.state import ReviewState, FinalReview

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


SYNTHESIS_PROMPT = """You are a principal engineer synthesizing a full code review from specialist agent reports.

You have received findings from four specialist agents. Your job is to:
1. Weigh all findings together
2. Produce an overall quality score (0-100)
3. Make a clear recommendation
4. Summarize the most important points for the PR author

PR INFORMATION:
- Title: {title}
- Author: {author}
- Repository: {repo}
- Files changed: {files_changed}
- Total additions: +{additions} / deletions: -{deletions}
- Languages: {languages}
- Commits: {commits}

SECURITY AGENT FINDINGS ({security_count} issues):
{security_findings}

LOGIC AGENT FINDINGS ({logic_count} issues):
{logic_findings}

TEST COVERAGE REPORT:
- Score: {test_score}/100
- Missing test cases: {missing_tests}
- Untested files: {untested_files}

DOCUMENTATION REPORT:
- Score: {doc_score}/100
- Missing docstrings: {missing_docstrings}
- Missing type hints: {missing_type_hints}

Based on ALL of the above, respond with a JSON object in exactly this format:
{{
  "summary": "2-3 sentence plain English summary of the PR quality and main concerns",
  "overall_score": <integer 0-100>,
  "recommendation": "APPROVE|REQUEST_CHANGES|NEEDS_DISCUSSION",
  "security_highlights": [
    "most important security point (or 'No security issues found')"
  ],
  "logic_highlights": [
    "most important logic point 1",
    "most important logic point 2"
  ],
  "top_suggestions": [
    "highest priority action item 1",
    "highest priority action item 2",
    "highest priority action item 3"
  ],
  "estimated_review_time_minutes": <integer>
}}

Scoring guide:
- 90-100: Excellent, minor nits only
- 75-89:  Good, small improvements needed
- 60-74:  Acceptable, several issues to address
- 40-59:  Needs significant work
- 0-39:   Major problems, do not merge

Recommendation guide:
- APPROVE: score >= 80 and no critical/high security issues
- REQUEST_CHANGES: any critical/high security issue, or score < 70
- NEEDS_DISCUSSION: score 70-79 or complex tradeoffs that need team input

Return ONLY the JSON object, no other text.
"""


def _format_security_findings(findings) -> str:
    if not findings:
        return "  None found."
    lines = []
    for f in findings:
        lines.append(f"  [{f.severity.upper()}] {f.title} — {f.file}")
        lines.append(f"    {f.description[:200]}")
    return "\n".join(lines)


def _format_logic_findings(findings) -> str:
    if not findings:
        return "  None found."
    lines = []
    for f in findings:
        lines.append(f"  [{f.severity.upper()}] {f.title} — {f.file}")
        lines.append(f"    {f.description[:200]}")
    return "\n".join(lines)


def run_synthesis_agent(state: ReviewState) -> ReviewState:
    """
    Reads all specialist findings and produces the final review report.
    Writes result to state.final_review.
    """
    pr = state.parsed_pr
    if pr is None:
        state.errors.append("synthesis_agent: no parsed PR in state")
        return state

    print(f"  [synthesis_agent] 📋 Synthesizing findings from {len(state.completed_agents)} agents...")

    # Build test coverage summary safely
    tc = state.test_coverage
    test_score     = tc.coverage_score if tc else "N/A"
    missing_tests  = ", ".join(tc.missing_test_cases[:3]) if tc else "unknown"
    untested_files = ", ".join(tc.untested_files) if tc else "unknown"

    # Build documentation summary safely
    docs = state.documentation
    doc_score         = docs.score if docs else "N/A"
    missing_docstrings = ", ".join(docs.missing_docstrings[:3]) if docs else "unknown"
    missing_type_hints = ", ".join(docs.missing_type_hints[:3]) if docs else "unknown"

    prompt = SYNTHESIS_PROMPT.format(
        title=pr.title,
        author=pr.author,
        repo=pr.repo_name,
        files_changed=pr.total_files_changed,
        additions=pr.total_additions,
        deletions=pr.total_deletions,
        languages=", ".join(pr.changed_languages),
        commits=len(pr.commit_messages),
        security_count=len(state.security_findings),
        security_findings=_format_security_findings(state.security_findings),
        logic_count=len(state.logic_findings),
        logic_findings=_format_logic_findings(state.logic_findings),
        test_score=test_score,
        missing_tests=missing_tests,
        untested_files=untested_files,
        doc_score=doc_score,
        missing_docstrings=missing_docstrings,
        missing_type_hints=missing_type_hints,
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",             # use full 4o for synthesis — quality matters here
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)

        state.final_review = FinalReview(
            summary=data["summary"],
            overall_score=data["overall_score"],
            recommendation=data["recommendation"],
            security_highlights=data.get("security_highlights", []),
            logic_highlights=data.get("logic_highlights", []),
            top_suggestions=data.get("top_suggestions", []),
            estimated_review_time_minutes=data.get("estimated_review_time_minutes", 5),
        )

        print(f"  [synthesis_agent] ✅ Score: {state.final_review.overall_score}/100 — {state.final_review.recommendation}")

    except Exception as e:
        state.errors.append(f"synthesis_agent failed: {str(e)}")
        print(f"  [synthesis_agent] ❌ Error: {e}")

    state.completed_agents.append("synthesis")
    return state