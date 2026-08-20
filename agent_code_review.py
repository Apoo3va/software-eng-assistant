import json
from groq import Groq
from dotenv import load_dotenv
import os
from llm_utils import safe_json_parse
from llm_utils import call_llm_for_json

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def review_code(issue_title: str, fix: dict, requirements: dict) -> dict:
    prompt = f"""You are a Code Reviewer agent.

Issue: {issue_title}
Acceptance criteria: {json.dumps(requirements['acceptance_criteria'])}

Proposed fix (language: {fix['language']}):
{fix['code_snippet']}

Approach explanation: {fix['proposed_approach']}

Review this fix. Respond ONLY with valid JSON in exactly this format, no other text:
{{
  "approved": true or false,
  "issues": ["issue 1", "issue 2"],
  "feedback": "one paragraph of feedback for the coder",
  "severity": "none" or "minor" or "major"
}}
"""
    return call_llm_for_json(groq_client, "openai/gpt-oss-20b", prompt)