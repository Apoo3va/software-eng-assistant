from graph import build_graph
import json

app = build_graph()

initial_state = {
    "owner": "pallets",
    "repo": "click",
    "issue_number": 3362,
    "revision_count": 0,
}

final_state = app.invoke(initial_state)

print("\n--- FINAL STATE ---")
print(json.dumps(final_state, indent=2, default=str))

if final_state.get("needs_human_approval"):
    print("\n[Orchestrator] HUMAN APPROVAL REQUIRED before this fix proceeds further.")
else:
    print("\n[Orchestrator] Fix marked low-risk, would proceed to Testing Agent (not built yet).")