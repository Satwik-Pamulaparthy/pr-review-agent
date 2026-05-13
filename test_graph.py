import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.workflow import review_graph
from graph.state import ReviewState

RECOMMENDATION_EMOJI = {
    "APPROVE": "✅",
    "REQUEST_CHANGES": "🔴",
    "NEEDS_DISCUSSION": "🟡",
}

print("=" * 65)
print("  PR Review Agent — Full Pipeline Test")
print("=" * 65)

initial_state = ReviewState(
    pr_url="https://github.com/fastapi/fastapi/pull/15508"
)

print(f"\nAnalyzing: {initial_state.pr_url}\n")
final_state = review_graph.invoke(initial_state)

pr     = final_state.get("parsed_pr")
review = final_state.get("final_review")

print(f"\n{'=' * 65}")
print(f"  FINAL REVIEW REPORT")
print(f"{'=' * 65}")
print(f"  PR:     {pr.title}")
print(f"  Repo:   {pr.repo_name}  |  Author: {pr.author}")
print(f"  Lines:  +{pr.total_additions} / -{pr.total_deletions}  |  Files: {pr.total_files_changed}")

if review:
    emoji = RECOMMENDATION_EMOJI.get(review.recommendation, "⚪")
    print(f"\n  {emoji}  RECOMMENDATION: {review.recommendation}")
    print(f"  📊  OVERALL SCORE:  {review.overall_score}/100")
    print(f"  ⏱️   EST. REVIEW TIME: {review.estimated_review_time_minutes} min")
    print(f"\n  SUMMARY")
    print(f"  {review.summary}")

    if review.security_highlights:
        print(f"\n  🔒 SECURITY HIGHLIGHTS")
        for h in review.security_highlights:
            print(f"    • {h}")

    if review.logic_highlights:
        print(f"\n  🧠 LOGIC HIGHLIGHTS")
        for h in review.logic_highlights:
            print(f"    • {h}")

    if review.top_suggestions:
        print(f"\n  💡 TOP SUGGESTIONS (priority order)")
        for i, s in enumerate(review.top_suggestions, 1):
            print(f"    {i}. {s}")

print(f"\n  Errors: {final_state.get('errors') or 'none'}")
print(f"{'=' * 65}")