import streamlit as st
from graph import build_graph
import json

st.set_page_config(page_title="AI Software Engineering Assistant", layout="wide")

st.title("🔧 AI Software Engineering Assistant")
st.caption("Multi-agent system: Requirements → Bug Investigation (RAG) → Coding → Review (reflection loop) → Testing (self-correcting) + Documentation (parallel)")

with st.sidebar:
    st.header("Target Issue")
    owner = st.text_input("Repo owner", value="pallets")
    repo = st.text_input("Repo name", value="click")
    issue_number = st.number_input("Issue number", value=3362, step=1)
    run_button = st.button("🚀 Run Pipeline", type="primary")

if "final_state" not in st.session_state:
    st.session_state.final_state = None

if run_button:
    app = build_graph()
    initial_state = {
        "owner": owner,
        "repo": repo,
        "issue_number": int(issue_number),
        "revision_count": 0,
    }
    with st.spinner("Running multi-agent pipeline..."):
        st.session_state.final_state = app.invoke(initial_state)

state = st.session_state.final_state

if state is None:
    st.info("Enter a repo + issue number in the sidebar and click **Run Pipeline** to start.")
else:
    st.subheader(f"Issue: {state['issue_title']}")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Requirements", "Bug Investigation", "Fix", "Code Review", "Testing", "Documentation"
    ])

    with tab1:
        st.json(state.get("requirements"))

    with tab2:
        investigation = state.get("investigation")
        if investigation:
            st.json(investigation)
        else:
            st.write("Not classified as a bug — investigation skipped.")

    with tab3:
        fix = state.get("fix")
        if fix:
            st.write("**Proposed approach:**")
            st.write(fix["proposed_approach"])
            st.write(f"**Language:** {fix['language']} | **Risk:** {fix['risk_level']}")
            st.code(fix["code_snippet"], language=fix["language"].lower())

    with tab4:
        review = state.get("review")
        if review:
            status = "✅ Approved" if review["approved"] else "❌ Rejected"
            st.write(f"**{status}** (severity: {review['severity']})")
            st.write(review["feedback"])
            if review["issues"]:
                st.write("**Issues found:**")
                for issue in review["issues"]:
                    st.write(f"- {issue}")

    with tab5:
        test_results = state.get("test_results")
        if test_results:
            status = "✅ Passed" if test_results["tests_passed"] else "❌ Failed"
            st.write(f"**{status}** (attempts used: {test_results.get('attempts_used', 1)})")
            st.write(test_results["test_summary"])
            st.code(test_results["test_code"], language="python")
            with st.expander("Raw pytest output"):
                st.code(test_results["execution_output"])

    with tab6:
        docs = state.get("documentation")
        if docs:
            st.write("**Changelog entry:**")
            st.code(docs["changelog_entry"])
            st.write("**README snippet:**")
            st.markdown(docs["readme_snippet"])
            st.write("**Code comments:**")
            st.code(docs["code_comments"])

    st.divider()

    # Human approval gate
    if state.get("needs_human_approval"):
        st.warning("⚠️ HUMAN APPROVAL REQUIRED before this fix proceeds further.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve Fix"):
                st.success("Fix approved by human reviewer. (In a full system, this would trigger a PR.)")
        with col2:
            if st.button("❌ Reject Fix"):
                st.error("Fix rejected. Would route back to Coding Assistant for revision.")
    else:
        st.success("✅ Pipeline complete — fix marked low-risk, ready for auto-merge.")

    with st.expander("Full raw state (debug)"):
        st.json(state)