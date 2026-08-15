from langgraph.graph import StateGraph, START, END
from graph_state import PipelineState
from agent_requirements import fetch_github_issue, analyze_requirements
from agent_bug_investigation import investigate_bug
from agent_coding import propose_fix


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
    print("[Coding Assistant Agent] Proposing fix...")
    fix = propose_fix(state["issue_title"], state["requirements"], state["investigation"])
    needs_approval = fix["needs_human_review"] or fix["risk_level"] in ("medium", "high")
    return {"fix": fix, "needs_human_approval": needs_approval, "status": "fix_proposed"}


def route_after_requirements(state: PipelineState) -> str:
    """This function IS the orchestrator's routing decision."""
    if state["requirements"]["type"] == "bug":
        return "bug_investigation"
    else:
        return "coding"  # non-bugs skip straight to coding for now


def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("fetch_issue", fetch_issue_node)
    graph.add_node("requirements", requirements_node)
    graph.add_node("bug_investigation", bug_investigation_node)
    graph.add_node("coding", coding_node)

    graph.add_edge(START, "fetch_issue")
    graph.add_edge("fetch_issue", "requirements")

    # Conditional edge = the routing logic, now declared explicitly instead of buried in an if/else
    graph.add_conditional_edges(
        "requirements",
        route_after_requirements,
        {"bug_investigation": "bug_investigation", "coding": "coding"}
    )

    graph.add_edge("bug_investigation", "coding")
    graph.add_edge("coding", END)

    return graph.compile()