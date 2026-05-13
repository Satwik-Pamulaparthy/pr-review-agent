import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from graph.state import ReviewState, TestCoverageResult

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


TEST_COVERAGE_PROMPT = """You are a senior QA engineer reviewing test coverage for a pull request.

Analyze what tests exist, what tests are missing, and how well the changes are covered.

Focus on:
- Do the new/modified source files have corresponding test changes?
- Are edge cases tested (None inputs, empty collections, error paths)?
- Are the happy path AND failure paths tested?
- Are there tests for boundary conditions?
- Is the test quality good (meaningful assertions, not just smoke tests)?

PR Title: {title}
Source files changed: {source_files}
Test files changed: {test_files}

SOURCE FILE DIFFS:
{source_diff}

TEST FILE DIFFS:
{test_diff}

Respond with a JSON object in exactly this format:
{{
  "coverage_score": <integer 0-100>,
  "missing_test_cases": [
    "description of missing test case 1",
    "description of missing test case 2"
  ],
  "untested_files": [
    "filename that has no corresponding test changes"
  ],
  "suggestions": [
    "specific suggestion to improve test coverage"
  ]
}}

Return ONLY the JSON object, no other text.
"""


def run_test_coverage_agent(state: ReviewState) -> ReviewState:
    """
    Evaluates test coverage for the PR changes.
    Writes results to state.test_coverage.
    """
    pr = state.parsed_pr
    if pr is None:
        state.errors.append("test_coverage_agent: no parsed PR in state")
        return state

    source_files = pr.source_files
    test_files   = pr.test_files

    source_diff = "\n".join([
        f"=== {f.filename} ===\n{f.patch}"
        for f in source_files
    ])[:6000]

    test_diff = "\n".join([
        f"=== {f.filename} ===\n{f.patch}"
        for f in test_files
    ])[:6000] if test_files else "(no test files changed in this PR)"

    print(f"  [test_coverage_agent] 🧪 Analyzing {len(source_files)} source + {len(test_files)} test file(s)...")

    prompt = TEST_COVERAGE_PROMPT.format(
        title=pr.title,
        source_files=", ".join(f.filename for f in source_files) or "none",
        test_files=", ".join(f.filename for f in test_files) or "none",
        source_diff=source_diff,
        test_diff=test_diff,
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)

        state.test_coverage = TestCoverageResult(
            coverage_score=data.get("coverage_score", 0),
            missing_test_cases=data.get("missing_test_cases", []),
            untested_files=data.get("untested_files", []),
            suggestions=data.get("suggestions", []),
        )

        print(f"  [test_coverage_agent] ✅ Coverage score: {state.test_coverage.coverage_score}/100")

    except Exception as e:
        state.errors.append(f"test_coverage_agent failed: {str(e)}")
        print(f"  [test_coverage_agent] ❌ Error: {e}")

    state.completed_agents.append("test_coverage")
    return state