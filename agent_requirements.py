import requests
import json
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def fetch_github_issue(owner: str, repo: str, issue_number: int) -> dict:
    """Fetch a single issue from GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # errors loudly if something's wrong
    return response.json()


def analyze_requirements(issue_title: str, issue_body: str) -> dict:
    """Ask the LLM to extract structured requirements from an issue."""
    prompt = f"""You are a Requirements Analysis agent for a software engineering assistant.

Given this GitHub issue, extract structured information.

Issue title: {issue_title}
Issue body: {issue_body}

Respond ONLY with valid JSON in exactly this format, no other text:
{{
  "type": "bug" or "feature" or "chore",
  "summary": "one sentence summary",
  "acceptance_criteria": ["criterion 1", "criterion 2"],
  "estimated_complexity": "low" or "medium" or "high"
}}
"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0  # more deterministic output for structured data
    )

    raw_text = response.choices[0].message.content

    # Clean up in case the model wraps it in ```json fences
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    return json.loads(raw_text)


if __name__ == "__main__":
    # Using a real public repo issue as a test — feel free to swap this
    owner = "facebook"
    repo = "react"
    issue_number = 28000

    issue = fetch_github_issue(owner, repo, issue_number)
    print(f"Fetched issue: {issue['title']}\n")

    result = analyze_requirements(issue["title"], issue["body"] or "")
    print("Structured requirements output:")
    print(json.dumps(result, indent=2))