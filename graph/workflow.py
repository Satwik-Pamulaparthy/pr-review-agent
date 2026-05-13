from langgraph.graph import StateGraph, END
from graph.state import ReviewState
from agents.security import run_security_agent
from agents.logic import run_logic_agent
from agents.test_coverage import run_test_coverage_agent
from agents.documentation import run_documentation_agent
from agents.synthesis import run_synthesis_agent


def fetch_pr_node(state: ReviewState) -> ReviewState:
    from tools.github_client import fetch_pr
    try:
        state.parsed_pr = fetch_pr(state.pr_url)
        print(f"  [fetch_pr] ✅ Fetched PR #{state.parsed_pr.pr_number}: {state.parsed_pr.title}")
    except Exception as e:
        state.errors.append(f"fetch_pr failed: {str(e)}")
        print(f"  [fetch_pr] ❌ {e}")
    return state


def should_continue(state: ReviewState) -> str:
    if state.parsed_pr is None:
        return "abort"
    return "continue"


def build_graph() -> StateGraph:
    graph = StateGraph(ReviewState)

    graph.add_node("fetch_pr",            fetch_pr_node)
    graph.add_node("security_agent",      run_security_agent)
    graph.add_node("logic_agent",         run_logic_agent)
    graph.add_node("test_coverage_agent", run_test_coverage_agent)
    graph.add_node("documentation_agent", run_documentation_agent)
    graph.add_node("synthesis_agent",     run_synthesis_agent)

    graph.set_entry_point("fetch_pr")

    graph.add_conditional_edges(
        "fetch_pr",
        should_continue,
        {"continue": "security_agent", "abort": END}
    )

    graph.add_edge("security_agent",      "logic_agent")
    graph.add_edge("logic_agent",         "test_coverage_agent")
    graph.add_edge("test_coverage_agent", "documentation_agent")
    graph.add_edge("documentation_agent", "synthesis_agent")
    graph.add_edge("synthesis_agent",     END)

    return graph.compile()


review_graph = build_graph()