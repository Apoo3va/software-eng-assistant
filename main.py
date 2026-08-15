from agent_requirements import fetch_github_issue, analyze_requirements
from agent_bug_investigation import investigate_bug
from agent_coding import propose_fix
import json


def run_pipeline(owner: str, repo: str, issue_number: int):
    print(f"Fetching issue #{issue_number} from {owner}/{repo}...\n")
    issue = fetch_github_issue(owner, repo, issue_number)
    print(f"Issue: {issue['title']}\n")

    # --- Agent 1: Requirements Analysis ---
    print("[Requirements Analysis Agent] Analyzing...")
    requirements = analyze_requirements(issue["title"], issue["body"] or "")
    print(json.dumps(requirements, indent=2))
    print()

    # --- Orchestrator: route based on type ---
    if requirements["type"] == "bug":
        print("[Orchestrator] Type = bug -> Bug Investigation Agent\n")
        print("[Bug Investigation Agent] Investigating...")
        investigation = investigate_bug(issue["title"], issue["body"] or "", requirements)
        print(json.dumps(investigation, indent=2))
        print()

        print("[Orchestrator] Investigation done -> Coding Assistant Agent\n")
        print("[Coding Assistant Agent] Proposing fix...")
        fix = propose_fix(issue["title"], requirements, investigation)
        print(json.dumps(fix, indent=2))
        print()

        # --- Human approval gate ---
        if fix["needs_human_review"] or fix["risk_level"] in ("medium", "high"):
            print("[Orchestrator] HUMAN APPROVAL REQUIRED before this fix proceeds further.")
        else:
            print("[Orchestrator] Fix marked low-risk, would proceed to Testing Agent (not built yet).")

    else:
        print(f"[Orchestrator] Type = {requirements['type']} -> would route to Coding Agent directly (not built yet)")


if __name__ == "__main__":
    run_pipeline(owner="microsoft", repo="vscode", issue_number=200000)