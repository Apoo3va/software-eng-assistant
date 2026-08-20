import json
from groq import Groq
from dotenv import load_dotenv
import os
from llm_utils import safe_json_parse
from llm_utils import call_llm_for_json

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_docs(issue_title: str, fix: dict, requirements: dict) -> dict:
    prompt = f"""You are a Documentation Writer agent.

Issue: {issue_title}
Summary: {requirements['summary']}
Fix approach: {fix['proposed_approach']}
Code ({fix['language']}):
{fix['code_snippet']}

Write documentation for this change. Respond ONLY with valid JSON in exactly this format, no other text:
{{
  "changelog_entry": "one line, changelog-style entry",
  "code_comments": "inline comments/docstring to add, as a string",
  "readme_snippet": "a short markdown snippet suitable for a README or PR description"
}}
"""
    return call_llm_for_json(groq_client, "openai/gpt-oss-20b", prompt)