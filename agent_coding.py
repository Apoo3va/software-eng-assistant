import json
from groq import Groq
from dotenv import load_dotenv
import os
from rag_retriever import retrieve_relevant_code
from llm_utils import call_llm_for_json

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def propose_fix(issue_title: str, requirements: dict, investigation: dict, owner: str, repo: str) -> dict:
    retrieved = retrieve_relevant_code(" ".join(investigation.get("suspected_files_or_areas", [])), owner, repo)
    context_block = "\n\n".join(
        f"--- {c['file']} ---\n{c['content']}" for c in retrieved
    ) if retrieved else "(No indexed code available for this repo yet — propose a general, illustrative fix.)"

    prompt = f"""You are a Coding Assistant agent for a software engineering assistant.

Issue: {issue_title}
Summary: {requirements['summary']}
Acceptance criteria: {json.dumps(requirements['acceptance_criteria'])}

Bug investigation found:
Likely root causes: {json.dumps(investigation['likely_root_causes'])}
Suspected areas: {json.dumps(investigation['suspected_files_or_areas'])}

Actual relevant code retrieved from the codebase (via RAG):
{context_block}

Based on this, propose a fix. Reference actual function/class names and file paths visible
in the retrieved code above when available.

Respond ONLY with valid JSON in exactly this format, no other text:
{{
  "proposed_approach": "one paragraph explaining the fix strategy",
  "code_snippet": "the actual illustrative code change, use \\n for newlines",
  "language": "python",
  "risk_level": "low" or "medium" or "high",
  "needs_human_review": true or false
}}
"""
    return call_llm_for_json(groq_client, "openai/gpt-oss-20b", prompt)