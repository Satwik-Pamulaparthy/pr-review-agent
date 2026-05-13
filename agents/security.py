import os
from openai import OpenAI
from dotenv import load_dotenv
from graph.state import ReviewState, SecurityFinding

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


SECURITY_PROMPT = """You are a senior security engineer performing a security audit on a code diff.

Analyze the following pull request and identify security vulnerabilities.

Focus on:
- Injection vulnerabilities (SQL, command, path traversal)
- Authentication and authorization flaws
- Hardcoded secrets, tokens, or credentials
- Insecure data handling or exposure of sensitive data
- Dangerous function calls (eval, exec, shell=True, etc.)
- Missing input validation or sanitization
- Insecure dependencies or imports
- Race conditions or concurrency issues

PR Title: {title}
Author: {author}
Files changed: {files}

DIFF:
{diff}

Respond with a JSON object in exactly this format:
{{
  "findings": [
    {{
      "severity": "critical|high|medium|low",
      "title": "short title",
      "description": "detailed description of the issue",
      "file": "filename where issue exists",
      "line_hint": "approximate line or function name (optional)",
      "recommendation": "specific fix recommendation"
    }}
  ]
}}

If there are no security issues, return {{"findings": []}}.
Return ONLY the JSON object, no other text.
"""


def run_security_agent(state: ReviewState) -> ReviewState:
    """
    Analyzes the PR diff for security vulnerabilities.
    Writes findings to state.security_findings.
    """
    pr = state.parsed_pr
    if pr is None:
        state.errors.append("security_agent: no parsed PR in state")
        return state

    # Truncate diff to avoid token limits — security agent focuses on source files
    source_files = pr.source_files
    if not source_files:
        source_files = pr.files  # fallback to all files

    diff_text = "\n".join([
        f"=== {f.filename} ===\n{f.patch}"
        for f in source_files
    ])[:12000]  # ~3k tokens — leaves room for prompt + response

    prompt = SECURITY_PROMPT.format(
        title=pr.title,
        author=pr.author,
        files=", ".join(f.filename for f in source_files),
        diff=diff_text,
    )

    print(f"  [security_agent] 🔍 Analyzing {len(source_files)} source file(s)...")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,    # low temp = more consistent, less creative
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        import json
        data = json.loads(raw)

        state.security_findings = [
            SecurityFinding(**f) for f in data.get("findings", [])
        ]

        severity_counts = {}
        for f in state.security_findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

        print(f"  [security_agent] ✅ Found {len(state.security_findings)} issue(s): {severity_counts or 'none'}")

    except Exception as e:
        state.errors.append(f"security_agent failed: {str(e)}")
        print(f"  [security_agent] ❌ Error: {e}")

    state.completed_agents.append("security")
    return state