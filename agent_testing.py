import json
import subprocess
import tempfile
import os
import sys
from groq import Groq
from dotenv import load_dotenv
from llm_utils import safe_json_parse

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _generate_test_code(issue_title: str, fix: dict, requirements: dict, previous_error: str = None) -> dict:
    error_context = ""
    if previous_error:
        error_context = f"""
IMPORTANT: A previous attempt at this test file FAILED to run correctly, not because the
underlying logic was wrong, but because of a bug in the TEST CODE ITSELF (e.g. wrong mock
usage, wrong attribute access, syntax error, unescaped newline in a string). Here is the
failure output:

{previous_error}

Fix the test code so it is correct and runnable. Common issues to avoid: don't call methods
on lambdas that don't have those methods (e.g. don't call .write() on a plain lambda — use a
simple class with a real method, or a list that you .append() to instead), keep mocks simple,
and never put a raw line break inside a quoted string — use \\n instead.
"""

    prompt = f"""You are a Testing agent. Write a SELF-CONTAINED Python pytest file that
demonstrates test-writing for this fix, without depending on any external module, class,
or import that isn't defined inside the test file itself.

Since the real fix is in {fix['language']} and there's no real codebase connected yet,
DO NOT import from any project module. Define any needed function/class stub directly
inside this same test file, then write pytest tests against that locally-defined stub.
Keep any mock/stub objects SIMPLE — prefer plain classes with real methods over lambdas
standing in for objects with methods. CRITICAL: when writing string literals inside the
Python code, NEVER put an actual line break inside a single-quoted or double-quoted string
— always use the escape sequence \\n (backslash-n) instead. A raw newline inside quotes is
a Python syntax error. The file must be 100% runnable as-is with only pytest as a dependency.
{error_context}
Issue: {issue_title}
Acceptance criteria: {json.dumps(requirements['acceptance_criteria'])}
Fix approach: {fix['proposed_approach']}

Respond ONLY with valid JSON in exactly this format, no other text:
{{
  "test_code": "complete, self-contained, runnable pytest file content as a string, use \\\\n for newlines, no external project imports, must actually pass",
  "test_summary": "one sentence describing what the tests check"
}}
"""

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    raw_text = response.choices[0].message.content
    return safe_json_parse(raw_text, groq_client=groq_client)


def _run_pytest(test_code: str) -> tuple[str, bool]:
    with tempfile.NamedTemporaryFile(mode="w", suffix="_test.py", delete=False) as f:
        f.write(test_code)
        test_file = f.name

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v"],
            capture_output=True, text=True, timeout=15
        )
        output = proc.stdout + proc.stderr
        passed = proc.returncode == 0
    except Exception as e:
        output = str(e)
        passed = False
    finally:
        os.unlink(test_file)

    return output, passed


def generate_and_run_tests(issue_title: str, fix: dict, requirements: dict, max_attempts: int = 2) -> dict:
    result = None
    previous_error = None

    for attempt in range(1, max_attempts + 1):
        print(f"  [Testing Agent] Attempt {attempt}/{max_attempts}...", flush=True)
        result = _generate_test_code(issue_title, fix, requirements, previous_error)
        output, passed = _run_pytest(result["test_code"])
        result["execution_output"] = output
        result["tests_passed"] = passed
        result["attempts_used"] = attempt

        if passed:
            print(f"  [Testing Agent] Tests passed on attempt {attempt}.", flush=True)
            break
        else:
            print(f"  [Testing Agent] Tests failed on attempt {attempt}, retrying with feedback...", flush=True)
            previous_error = output

    return result