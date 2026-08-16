import requests
import os
import base64
import time
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


def get_authenticated_user() -> str:
    response = requests.get("https://api.github.com/user", headers=HEADERS)
    response.raise_for_status()
    return response.json()["login"]


def ensure_fork(owner: str, repo: str) -> str:
    """Fork the repo to the authenticated user's account if not already forked. Returns fork owner login."""
    username = get_authenticated_user()

    # Check if fork already exists
    check_url = f"https://api.github.com/repos/{username}/{repo}"
    check = requests.get(check_url, headers=HEADERS)
    if check.status_code == 200:
        print(f"[GitHub] Fork already exists: {username}/{repo}")
        return username

    # Create the fork
    fork_url = f"https://api.github.com/repos/{owner}/{repo}/forks"
    response = requests.post(fork_url, headers=HEADERS)
    response.raise_for_status()
    print(f"[GitHub] Forking {owner}/{repo} to {username}/{repo}...")

    # Forking is async on GitHub's side, poll until it's ready
    for _ in range(10):
        time.sleep(2)
        check = requests.get(check_url, headers=HEADERS)
        if check.status_code == 200:
            print(f"[GitHub] Fork ready: {username}/{repo}")
            return username

    raise TimeoutError("Fork did not become ready in time.")


def get_default_branch_sha(owner: str, repo: str, branch: str = "main") -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 404:
        # try 'master' as fallback
        url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/master"
        response = requests.get(url, headers=HEADERS)
        branch = "master"
    response.raise_for_status()
    return response.json()["object"]["sha"], branch


def create_branch(owner: str, repo: str, new_branch: str, from_sha: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
    payload = {"ref": f"refs/heads/{new_branch}", "sha": from_sha}
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 422:
        print(f"[GitHub] Branch {new_branch} already exists, reusing it.")
        return
    response.raise_for_status()
    print(f"[GitHub] Created branch: {new_branch}")


def commit_file(owner: str, repo: str, branch: str, file_path: str, content: str, commit_message: str):
    """Create or update a file on the given branch."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"

    # Check if file exists on this branch (need its sha to update)
    check = requests.get(url, headers=HEADERS, params={"ref": branch})
    sha = check.json().get("sha") if check.status_code == 200 else None

    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    print(f"[GitHub] Committed file: {file_path} on {branch}")


def open_pull_request(fork_owner: str, upstream_owner: str, repo: str, branch: str, base_branch: str,
                       title: str, body: str) -> str:
    """Open a PR from fork_owner:branch against fork_owner's own base_branch (safe, doesn't touch upstream)."""
    url = f"https://api.github.com/repos/{fork_owner}/{repo}/pulls"
    payload = {
        "title": title,
        "head": branch,
        "base": base_branch,
        "body": body
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    pr_data = response.json()
    print(f"[GitHub] Opened PR: {pr_data['html_url']}")
    return pr_data["html_url"]


def submit_fix_as_pr(upstream_owner: str, repo: str, issue_number: int, issue_title: str, fix: dict, documentation: dict) -> str:
    """
    Full flow: fork repo (if needed), create a branch, commit the fix as a file,
    open a real PR against the fork's own main branch. Returns the PR URL.
    """
    fork_owner = ensure_fork(upstream_owner, repo)
    base_sha, base_branch = get_default_branch_sha(fork_owner, repo)

    branch_name = f"ai-agent-fix-issue-{issue_number}-{int(time.time())}"
    create_branch(fork_owner, repo, branch_name, base_sha)

    # Commit the proposed fix as a new file (safe — doesn't overwrite real source files)
    file_path = f"ai_agent_fixes/issue_{issue_number}_fix.py"
    file_content = f'''"""
AI Software Engineering Assistant — Proposed Fix
Issue #{issue_number}: {issue_title}

{fix["proposed_approach"]}
"""

{fix["code_snippet"]}
'''
    commit_file(fork_owner, repo, branch_name, file_path, file_content,
                f"AI-proposed fix for issue #{issue_number}: {issue_title}")

    pr_title = f"[AI Agent] Fix for #{issue_number}: {issue_title}"
    pr_body = f"""## Automated fix proposal

**Original issue:** #{issue_number} - {issue_title}

**Approach:**
{fix["proposed_approach"]}

**Risk level:** {fix["risk_level"]}

**Changelog entry:**
{documentation["changelog_entry"]}

---
*This PR was generated by an AI multi-agent software engineering assistant, approved by a human reviewer before submission. This is a demonstration fix in `ai_agent_fixes/`, not a modification of the actual source files, since this targets a personal fork for portfolio/demo purposes.*
"""

    pr_url = open_pull_request(fork_owner, upstream_owner, repo, branch_name, base_branch, pr_title, pr_body)
    return pr_url