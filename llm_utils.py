import json
import re
import time


def _fix_invalid_escapes(text: str) -> str:
    """Fix backslashes that aren't valid JSON escape sequences by doubling them."""
    valid_escapes = set('"\\/bfnrtu')

    def replace_bad_escape(match):
        char = match.group(1)
        if char in valid_escapes:
            return match.group(0)
        return '\\\\' + char

    return re.sub(r'\\(.)', replace_bad_escape, text)


def safe_json_parse(raw_text: str, groq_client=None, retry_model: str = "openai/gpt-oss-20b") -> dict:
    """
    Robustly parse JSON from an LLM response. Handles common issues:
    markdown fences, trailing commas, invalid backslash escapes, unescaped newlines.
    If all else fails and a groq_client is provided, asks the LLM to fix its own output.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Received empty text to parse as JSON.")

    cleaned = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    fixed = re.sub(r",\s*([}\]])", r"\1", cleaned)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    escape_fixed = _fix_invalid_escapes(fixed)
    try:
        return json.loads(escape_fixed)
    except json.JSONDecodeError:
        pass

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
                temperature=0,
                reasoning_effort="low"
            )
            repaired = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            if repaired:
                return json.loads(repaired)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM output after all repair attempts: {cleaned[:300]}")


def call_llm_for_json(groq_client, model: str, prompt: str, temperature: float = 0,
                       max_tokens: int = 2000, max_retries: int = 2) -> dict:
    """
    Calls the LLM and parses JSON from its response, automatically retrying the
    ENTIRE API call (not just JSON repair) if the model returns an empty response.

    reasoning_effort='low' is critical here: gpt-oss models spend tokens on hidden
    chain-of-thought reasoning before writing the actual answer. Without capping this,
    reasoning can consume the entire max_tokens budget, leaving an empty content field.
    """
    last_error = None
    for attempt in range(1, max_retries + 1):
        response = groq_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort="low"
        )
        raw_text = response.choices[0].message.content

        if raw_text and raw_text.strip():
            try:
                return safe_json_parse(raw_text, groq_client=groq_client, retry_model=model)
            except ValueError as e:
                last_error = e
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                raise
        else:
            last_error = ValueError("LLM returned an empty response.")
            if attempt < max_retries:
                time.sleep(1)
                continue

    raise last_error