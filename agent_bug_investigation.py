import json
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def investigate_bug(issue_title: str, issue_body: str, requirements: dict) -> dict:
    """Given a bug issue + the Requirements Agent's output, suggest likely causes."""
    prompt = f"""You are a Bug Investigation agent for a software engineering assistant.

A Requirements Analysis agent already classified this issue as a BUG with this summary:
{requirements['summary']}

Acceptance criteria for the fix:
{json.dumps(requirements['acceptance_criteria'])}

Full issue title: {issue_title}
Full issue body: {issue_body}

Based on this, respond ONLY with valid JSON in exactly this format, no other text:
{{
  "likely_root_causes": ["cause 1", "cause 2"],
  "suspected_files_or_areas": ["area/module name if guessable, else 'unknown - needs codebase access'"],
  "suggested_investigation_steps": ["step 1", "step 2"],
  "confidence": "low" or "medium" or "high"
}}
"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    raw_text = response.choices[0].message.content
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
    return json.loads(raw_text)