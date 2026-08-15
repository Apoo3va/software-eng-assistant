import json
from groq import Groq
from dotenv import load_dotenv
import os
from rag_retriever import retrieve_relevant_code
from llm_utils import safe_json_parse

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def propose_fix(issue_title: str, requirements: dict, investigation: dict) -> dict:
    retrieved = retrieve_relevant_code(" ".join(investigation["suspected_files_or_areas"]))
    context_block = "\n\n".join(
        f"--- {c['file']} ---\n{c['content']}" for c in retrieved
    )

    prompt = f"""You are a Coding Assistant agent for a software engineering assistant.

Issue: {issue_title}
Summary: {requirements['summary']}
Acceptance criteria: {json.dumps(requirements['acceptance_criteria'])}

Bug investigation found:
Likely root causes: {json.dumps(investigation['likely_root_causes'])}
Suspected areas: {json.dumps(investigation['suspected_files_or_areas'])}

Actual relevant code retrieved from the codebase (via RAG):
{context_block}

Based on this REAL code, propose a fix. Reference actual function/class names and file
paths visible in the retrieved code above.

Respond ONLY with valid JSON in exactly this format, no other text:
{{
  "proposed_approach": "one paragraph explaining the fix strategy, referencing real code",
  "code_snippet": "the actual illustrative code change, use \\n for newlines",
  "language": "python",
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
    return safe_json_parse(raw_text, groq_client=groq_client)