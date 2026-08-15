from agent_requirements import fetch_github_issue, analyze_requirements
from agent_bug_investigation import investigate_bug
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

    # --- Handoff decision (this is your orchestrator logic, done manually) ---
    if requirements["type"] == "bug":
        print("[Orchestrator] Type = bug -> handing off to Bug Investigation Agent\n")
        print("[Bug Investigation Agent] Investigating...")
        investigation = investigate_bug(issue["title"], issue["body"] or "", requirements)
        print(json.dumps(investigation, indent=2))
    else:
        print(f"[Orchestrator] Type = {requirements['type']} -> would route to Coding Agent (not built yet)")


if __name__ == "__main__":
    # microsoft/vscode tends to have detailed bug reports
    # Swap this issue number for any real one if this one doesn't exist/isn't a bug
    run_pipeline(owner="microsoft", repo="vscode", issue_number=200000)