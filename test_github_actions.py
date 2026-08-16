from github_actions import submit_fix_as_pr

test_fix = {
    "proposed_approach": "Test fix to verify GitHub automation works end to end.",
    "code_snippet": "def example_fix():\n    return 'This is a test fix from the AI agent.'",
    "risk_level": "low"
}
test_docs = {
    "changelog_entry": "Test changelog entry"
}

pr_url = submit_fix_as_pr(
    upstream_owner="pallets",
    repo="click",
    issue_number=3362,
    issue_title="Test PR from AI agent pipeline",
    fix=test_fix,
    documentation=test_docs
)
print(f"\nDone! PR URL: {pr_url}")