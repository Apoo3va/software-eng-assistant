import streamlit as st
from graph import build_graph
from rag_indexer import build_index
from github_actions import submit_fix_as_pr
import json

st.set_page_config(page_title="AI Software Engineering Assistant", layout="wide")

st.title("AI Software Engineering Assistant")
st.caption("Multi-agent system: Requirements → Bug Investigation (RAG) → Coding → Review (reflection loop) → Testing (self-correcting) + Documentation (parallel) → GitHub PR")

if "pipeline_running" not in st.session_state:
    st.session_state.pipeline_running = False
if "final_state" not in st.session_state:
    st.session_state.final_state = None

with st.sidebar:
    st.header("Target Issue")
    owner = st.text_input("Repo owner", value="pallets")
    repo = st.text_input("Repo name", value="click")
    issue_number = st.number_input("Issue number", value=3362, step=1)
    run_clicked = st.button(
        "Running..." if st.session_state.pipeline_running else "Run Pipeline",
        type="primary",
        disabled=st.session_state.pipeline_running
    )

if run_clicked and not st.session_state.pipeline_running:
    st.session_state.pipeline_running = True
    st.session_state.final_state = None
    st.rerun()

if st.session_state.pipeline_running and st.session_state.final_state is None:
    try:
        with st.spinner(f"Indexing {owner}/{repo} codebase for RAG (first time may take 1-2 min)..."):
            build_index(owner, repo)

        app = build_graph()
        initial_state = {
            "owner": owner,
            "repo": repo,
            "issue_number": int(issue_number),
            "revision_count": 0,
        }
        with st.spinner("Running multi-agent pipeline..."):
            st.session_state.final_state = app.invoke(initial_state)
        st.session_state.pipeline_running = False
        st.rerun()
    except Exception as e:
        st.session_state.pipeline_running = False
        st.error(f"Pipeline failed: {e}")
        st.info("This can happen occasionally due to LLM output variability or rate limits. Try clicking Run Pipeline again in a minute.")

state = st.session_state.final_state

if state is None:
    st.info("Enter any public repo owner/name + a real issue number in the sidebar, then click **Run Pipeline**.")
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

    if state.get("needs_human_approval"):
        st.warning("⚠️ HUMAN APPROVAL REQUIRED before this fix proceeds further.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Approve Fix"):
                with st.spinner("Creating branch, committing fix, opening PR on GitHub..."):
                    try:
                        pr_url = submit_fix_as_pr(
                            upstream_owner=state["owner"],
                            repo=state["repo"],
                            issue_number=state["issue_number"],
                            issue_title=state["issue_title"],
                            fix=state["fix"],
                            documentation=state["documentation"]
                        )
                        st.success("✅ Fix approved and PR opened!")
                        st.markdown(f"**[View PR on GitHub →]({pr_url})**")
                    except Exception as e:
                        st.error(f"Failed to create PR: {e}")
        with col2:
            if st.button("Reject Fix"):
                st.error("Fix rejected. Would route back to Coding Assistant for revision.")
    else:
        st.success("✅ Pipeline complete — fix marked low-risk, ready for auto-merge.")

    with st.expander("Full raw state (debug)"):
        st.json(state)