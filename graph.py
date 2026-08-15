from langgraph.graph import StateGraph, START, END
from graph_state import PipelineState
from agent_requirements import fetch_github_issue, analyze_requirements
from agent_bug_investigation import investigate_bug
from agent_coding import propose_fix
from agent_code_review import review_code


def fetch_issue_node(state: PipelineState) -> dict:
    issue = fetch_github_issue(state["owner"], state["repo"], state["issue_number"])
    return {
        "issue_title": issue["title"],
        "issue_body": issue["body"] or "",
        "status": "issue_fetched"
    }


def requirements_node(state: PipelineState) -> dict:
    print("[Requirements Analysis Agent] Analyzing...")
    requirements = analyze_requirements(state["issue_title"], state["issue_body"])
    return {"requirements": requirements, "status": "requirements_done"}


def bug_investigation_node(state: PipelineState) -> dict:
    print("[Bug Investigation Agent] Investigating...")
    investigation = investigate_bug(state["issue_title"], state["issue_body"], state["requirements"])
    return {"investigation": investigation, "status": "investigation_done"}


def coding_node(state: PipelineState) -> dict:
    print(f"[Coding Assistant Agent] Proposing fix (attempt {state.get('revision_count', 0) + 1})...")
    fix = propose_fix(state["issue_title"], state["requirements"], state["investigation"])
    needs_approval = fix["needs_human_review"] or fix["risk_level"] in ("medium", "high")
    return {
        "fix": fix,
        "needs_human_approval": needs_approval,
        "status": "fix_proposed",
        "revision_count": state.get("revision_count", 0) + 1
    }


def review_node(state: PipelineState) -> dict:
    print("[Code Reviewer Agent] Reviewing...")
    review = review_code(state["issue_title"], state["fix"], state["requirements"])
    return {"review": review, "status": "review_done"}


def route_after_requirements(state: PipelineState) -> str:
    if state["requirements"]["type"] == "bug":
        return "bug_investigation"
    else:
        return "coding"


def route_after_review(state: PipelineState) -> str:
    """Reflection loop: send back to coding if rejected, up to 2 revisions max."""
    if state["review"]["approved"]:
        return "end"
    if state["revision_count"] >= 2:
        print("[Orchestrator] Max revisions reached, escalating to human.")
        return "end"
    print("[Orchestrator] Review rejected -> sending back to Coding Assistant\n")
    return "coding"


def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("fetch_issue", fetch_issue_node)
    graph.add_node("requirements", requirements_node)
    graph.add_node("bug_investigation", bug_investigation_node)
    graph.add_node("coding", coding_node)
    graph.add_node("review", review_node)

    graph.add_edge(START, "fetch_issue")
    graph.add_edge("fetch_issue", "requirements")

    graph.add_conditional_edges(
        "requirements",
        route_after_requirements,
        {"bug_investigation": "bug_investigation", "coding": "coding"}
    )

    graph.add_edge("bug_investigation", "coding")
    graph.add_edge("coding", "review")

    graph.add_conditional_edges(
        "review",
        route_after_review,
        {"coding": "coding", "end": END}
    )

    return graph.compile()