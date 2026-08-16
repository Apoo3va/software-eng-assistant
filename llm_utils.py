import json
import re


def _fix_invalid_escapes(text: str) -> str:
    """Fix backslashes that aren't valid JSON escape sequences by doubling them."""
    valid_escapes = set('"\\/bfnrtu')

    def replace_bad_escape(match):
        char = match.group(1)
        if char in valid_escapes:
            return match.group(0)
        return '\\\\' + char

    return re.sub(r'\\(.)', replace_bad_escape, text)


def safe_json_parse(raw_text: str, groq_client=None, retry_model: str = "llama-3.3-70b-versatile") -> dict:
    """
    Robustly parse JSON from an LLM response. Handles common issues:
    markdown fences, trailing commas, invalid backslash escapes, unescaped newlines.
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

    # Attempt 3: fix invalid backslash escapes (common when code snippets contain paths/regex)
    escape_fixed = _fix_invalid_escapes(fixed)
    try:
        return json.loads(escape_fixed)
    except json.JSONDecodeError:
        pass

    # Attempt 4: ask the LLM to repair its own broken JSON
    if groq_client is not None:
        repair_prompt = f"""The following text was supposed to be valid JSON but has a syntax error.
Fix it and return ONLY the corrected valid JSON, nothing else, no markdown fences.
Pay special attention to backslashes inside string values (e.g. in code snippets or file
paths) — every backslash must be properly escaped as \\\\ in valid JSON:

{cleaned}
"""
        try:
            response = groq_client.chat.completions.create(
                model=retry_model,
                messages=[{"role": "user", "content": repair_prompt}],
                temperature=0
            )
            repaired = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM output after all repair attempts: {cleaned[:300]}")