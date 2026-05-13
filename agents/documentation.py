import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from graph.state import ReviewState, DocumentationResult

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


DOCUMENTATION_PROMPT = """You are a senior engineer reviewing documentation quality for a pull request.

Analyze the code changes for documentation completeness and quality.

Focus on:
- Missing or outdated docstrings on new/modified functions and classes
- Missing type hints on function parameters and return values
- Inline comments for complex logic that needs explanation
- Whether the PR description adequately explains what changed and why
- README or changelog updates if this is a user-facing change
- Are error messages clear and helpful?

PR Title: {title}
PR Description: {description}
Files changed: {files}

DIFF:
{diff}

Respond with a JSON object in exactly this format:
{{
  "score": <integer 0-100>,
  "missing_docstrings": [
    "ClassName.method_name is missing a docstring",
    "function_name lacks parameter documentation"
  ],
  "missing_type_hints": [
    "function_name: parameter 'x' has no type hint",
    "function_name: return type not annotated"
  ],
  "suggestions": [
    "specific documentation improvement suggestion"
  ]
}}

Return ONLY the JSON object, no other text.
"""


def run_documentation_agent(state: ReviewState) -> ReviewState:
    """
    Evaluates documentation quality for the PR changes.
    Writes results to state.documentation.
    """
    pr = state.parsed_pr
    if pr is None:
        state.errors.append("documentation_agent: no parsed PR in state")
        return state

    # Focus on source files only — test files have looser doc requirements
    relevant_files = pr.source_files or pr.files

    diff_text = "\n".join([
        f"=== {f.filename} ===\n{f.patch}"
        for f in relevant_files
    ])[:10000]

    print(f"  [documentation_agent] 📝 Analyzing documentation in {len(relevant_files)} file(s)...")

    prompt = DOCUMENTATION_PROMPT.format(
        title=pr.title,
        description=pr.description[:500],
        files=", ".join(f.filename for f in relevant_files),
        diff=diff_text,
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

        state.documentation = DocumentationResult(
            score=data.get("score", 0),
            missing_docstrings=data.get("missing_docstrings", []),
            missing_type_hints=data.get("missing_type_hints", []),
            suggestions=data.get("suggestions", []),
        )

        print(f"  [documentation_agent] ✅ Documentation score: {state.documentation.score}/100")

    except Exception as e:
        state.errors.append(f"documentation_agent failed: {str(e)}")
        print(f"  [documentation_agent] ❌ Error: {e}")

    state.completed_agents.append("documentation")
    return state