import json
import re


def safe_json_parse(raw_text: str, groq_client=None, retry_model: str = "llama-3.3-70b-versatile") -> dict:
    """
    Robustly parse JSON from an LLM response. Handles common issues:
    markdown fences, trailing commas, unescaped newlines in strings.
    If all else fails and a groq_client is provided, asks the LLM to fix its own output.
    """
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Attempt 2: remove trailing commas before } or ]
    fixed = re.sub(r",\s*([}\]])", r"\1", cleaned)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Attempt 3: ask the LLM to repair its own broken JSON
    if groq_client is not None:
        repair_prompt = f"""The following text was supposed to be valid JSON but has a syntax error.
Fix it and return ONLY the corrected valid JSON, nothing else, no markdown fences:

{cleaned}
"""
        response = groq_client.chat.completions.create(
            model=retry_model,
            messages=[{"role": "user", "content": repair_prompt}],
            temperature=0
        )
        repaired = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        return json.loads(repaired)  # if this still fails, let it raise — nothing more we can do

    raise ValueError(f"Could not parse JSON from LLM output: {cleaned[:200]}")