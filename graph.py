from langgraph.graph import StateGraph, START, END
from graph_state import PipelineState
from agent_requirements import fetch_github_issue, analyze_requirements
from agent_bug_investigation import investigate_bug
from agent_coding import propose_fix
from agent_code_review import review_code
from agent_testing import generate_and_run_tests
from agent_documentation import generate_docs


def fetch_issue_node(state: PipelineState) -> dict:
    issue = fetch_github_issue(state["owner"], state["repo"], state["issue_number"])
    return {"issue_title": issue["title"], "issue_body": issue["body"] or "", "status": "issue_fetched"}


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
    investigation = state.get("investigation") or {
        "likely_root_causes": ["N/A - not classified as a bug, no investigation performed"],
        "suspected_files_or_areas": [state["requirements"]["summary"]]
    }
    fix = propose_fix(state["issue_title"], state["requirements"], investigation)
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


def testing_node(state: PipelineState) -> dict:
    print("[Testing Agent] Writing and running tests...")
    test_results = generate_and_run_tests(state["issue_title"], state["fix"], state["requirements"])
    return {"test_results": test_results}


def documentation_node(state: PipelineState) -> dict:
    print("[Documentation Writer Agent] Generating docs...")
    docs = generate_docs(state["issue_title"], state["fix"], state["requirements"])
    return {"documentation": docs}


def route_after_requirements(state: PipelineState) -> str:
    return "bug_investigation" if state["requirements"]["type"] == "bug" else "coding"


def route_after_review(state: PipelineState) -> str:
    if state["review"]["approved"]:
        return "approved"
    if state["revision_count"] >= 2:
        print("[Orchestrator] Max revisions reached, escalating to human.")
        return "approved"
    print("[Orchestrator] Review rejected -> sending back to Coding Assistant\n")
    return "coding"


def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("fetch_issue", fetch_issue_node)
    graph.add_node("requirements", requirements_node)
    graph.add_node("bug_investigation", bug_investigation_node)
    graph.add_node("coding", coding_node)
    graph.add_node("review", review_node)
    graph.add_node("testing", testing_node)
    graph.add_node("documentation", documentation_node)

    graph.add_edge(START, "fetch_issue")
    graph.add_edge("fetch_issue", "requirements")

    graph.add_conditional_edges(
        "requirements", route_after_requirements,
        {"bug_investigation": "bug_investigation", "coding": "coding"}
    )
    graph.add_edge("bug_investigation", "coding")
    graph.add_edge("coding", "review")

    graph.add_conditional_edges(
        "review", route_after_review,
        {"coding": "coding", "approved": "testing"}
    )

    graph.add_edge("review", "documentation")
    graph.add_edge("testing", END)
    graph.add_edge("documentation", END)

    return graph.compile()