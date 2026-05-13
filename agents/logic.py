import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from graph.state import ReviewState, LogicFinding

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


LOGIC_PROMPT = """You are a senior software engineer performing a logic and correctness review on a code diff.

Analyze the following pull request for bugs, logic errors, and code quality issues.

Focus on:
- Logical errors or incorrect conditions (off-by-one, wrong comparisons, inverted logic)
- Edge cases that are not handled (None/null, empty lists, negative numbers, concurrency)
- Error handling gaps (missing try/except, silent failures, swallowed exceptions)
- Performance issues (N+1 queries, unnecessary loops, memory leaks)
- Breaking changes to public APIs or interfaces
- Incorrect use of language features or standard library
- Code that is overly complex and could be simplified

PR Title: {title}
Description: {description}
Files changed: {files}

DIFF:
{diff}

Respond with a JSON object in exactly this format:
{{
  "findings": [
    {{
      "severity": "high|medium|low",
      "title": "short title",
      "description": "detailed description of the issue",
      "file": "filename where issue exists",
      "suggestion": "specific improvement suggestion with example if possible"
    }}
  ]
}}

If there are no logic issues, return {{"findings": []}}.
Return ONLY the JSON object, no other text.
"""


def run_logic_agent(state: ReviewState) -> ReviewState:
    """
    Analyzes the PR diff for logic errors and code quality issues.
    Writes findings to state.logic_findings.
    """
    pr = state.parsed_pr
    if pr is None:
        state.errors.append("logic_agent: no parsed PR in state")
        return state

    # Logic agent looks at all non-config files
    relevant_files = [f for f in pr.files if not f.is_config_file]
    if not relevant_files:
        relevant_files = pr.files

    diff_text = "\n".join([
        f"=== {f.filename} ===\n{f.patch}"
        for f in relevant_files
    ])[:12000]

    prompt = LOGIC_PROMPT.format(
        title=pr.title,
        description=pr.description[:500],
        files=", ".join(f.filename for f in relevant_files),
        diff=diff_text,
    )

    print(f"  [logic_agent] 🧠 Analyzing {len(relevant_files)} file(s) for logic issues...")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)

        state.logic_findings = [
            LogicFinding(**f) for f in data.get("findings", [])
        ]

        severity_counts = {}
        for f in state.logic_findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

        print(f"  [logic_agent] ✅ Found {len(state.logic_findings)} issue(s): {severity_counts or 'none'}")

    except Exception as e:
        state.errors.append(f"logic_agent failed: {str(e)}")
        print(f"  [logic_agent] ❌ Error: {e}")

    state.completed_agents.append("logic")
    return state