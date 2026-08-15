import json
import subprocess
import tempfile
import os
import sys
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_and_run_tests(issue_title: str, fix: dict, requirements: dict) -> dict:
    prompt = f"""You are a Testing agent. Write a SELF-CONTAINED Python pytest file that
demonstrates test-writing for this fix, without depending on any external module, class,
or import that isn't defined inside the test file itself.

Since the real fix is in {fix['language']} and there's no real codebase connected yet,
DO NOT import from any project module (no "from your_module import X", no "from app import Y").
Instead, define any needed function/class stub directly inside this same test file
(e.g. a small Python function that mimics the logic being validated), then write pytest
tests against that locally-defined stub. The file must be 100% runnable as-is with only
pytest as a dependency.

Issue: {issue_title}
Acceptance criteria: {json.dumps(requirements['acceptance_criteria'])}
Fix approach: {fix['proposed_approach']}

Respond ONLY with valid JSON in exactly this format, no other text:
{{
  "test_code": "complete, self-contained, runnable pytest file content as a string, use \\n for newlines, no external project imports, must actually pass",
  "test_summary": "one sentence describing what the tests check"
}}
"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    raw_text = response.choices[0].message.content
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
    result = json.loads(raw_text)

    with tempfile.NamedTemporaryFile(mode="w", suffix="_test.py", delete=False) as f:
        f.write(result["test_code"])
        test_file = f.name

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v"],
            capture_output=True, text=True, timeout=15
        )
        result["execution_output"] = proc.stdout + proc.stderr
        result["tests_passed"] = proc.returncode == 0
    except Exception as e:
        result["execution_output"] = str(e)
        result["tests_passed"] = False
    finally:
        os.unlink(test_file)

    return result