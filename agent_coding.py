import json
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def propose_fix(issue_title: str, requirements: dict, investigation: dict) -> dict:
    """Given requirements + bug investigation, propose a code fix."""
    prompt = f"""You are a Coding Assistant agent for a software engineering assistant.

Issue: {issue_title}
Summary: {requirements['summary']}
Acceptance criteria: {json.dumps(requirements['acceptance_criteria'])}

Bug investigation found:
Likely root causes: {json.dumps(investigation['likely_root_causes'])}
Suspected areas: {json.dumps(investigation['suspected_files_or_areas'])}

Propose a fix. Since you don't have direct access to the real codebase yet,
write a realistic, illustrative code snippet showing the kind of change needed,
in whatever language is appropriate for this project (infer from context, default to
a generic pseudocode-like snippet if unsure).

Respond ONLY with valid JSON in exactly this format, no other text:
{{
  "proposed_approach": "one paragraph explaining the fix strategy",
  "code_snippet": "the illustrative code, use \\n for newlines",
  "language": "the language used in code_snippet",
  "risk_level": "low" or "medium" or "high",
  "needs_human_review": true or false
}}
"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    raw_text = response.choices[0].message.content
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
    return json.loads(raw_text)