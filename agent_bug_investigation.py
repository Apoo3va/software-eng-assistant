import json
from groq import Groq
from dotenv import load_dotenv
import os
from rag_retriever import retrieve_relevant_code
from llm_utils import call_llm_for_json

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def investigate_bug(issue_title: str, issue_body: str, requirements: dict, owner: str, repo: str) -> dict:
    retrieved = retrieve_relevant_code(f"{issue_title} {requirements['summary']}", owner, repo)
    context_block = "\n\n".join(
        f"--- {c['file']} ---\n{c['content']}" for c in retrieved
    ) if retrieved else "(No indexed code available for this repo yet.)"

    prompt = f"""You are a Bug Investigation agent for a software engineering assistant.

A Requirements Analysis agent already classified this issue as a BUG with this summary:
{requirements['summary']}

Acceptance criteria for the fix:
{json.dumps(requirements['acceptance_criteria'])}

Full issue title: {issue_title}
Full issue body: {issue_body}

Here are the most relevant code chunks retrieved from the actual codebase (via RAG):
{context_block}

Based on the ACTUAL retrieved code above (not guesses), respond ONLY with valid JSON in
exactly this format, no other text:
{{
  "likely_root_causes": ["cause 1", "cause 2"],
  "suspected_files_or_areas": ["actual file path(s) from the retrieved chunks above, or a best guess if none were retrieved"],
  "suggested_investigation_steps": ["step 1", "step 2"],
  "confidence": "low" or "medium" or "high"
}}
"""
    return call_llm_for_json(groq_client, "openai/gpt-oss-20b", prompt)