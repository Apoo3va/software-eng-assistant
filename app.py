import streamlit as st
from graph import build_graph
from rag_indexer import build_index
from github_actions import submit_fix_as_pr
import json

st.set_page_config(page_title="AI Software Engineering Assistant", layout="wide")


@st.cache_resource
def ensure_rag_index():
    build_index()
    return True


with st.spinner("Setting up knowledge base (first run only, ~1-2 min)..."):
    ensure_rag_index()

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700;800&family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+JP:wght@400&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0A0E17 !important; }
code, pre, .stCode, [data-testid="stCodeBlock"] { font-family: 'JetBrains Mono', monospace !important; }

/* Hidden HUD background message */
.hud-bg {
    position: fixed; top: 0; left: 0; width: 200%; height: 200%;
    z-index: -1; pointer-events: none;
    font-family: 'Noto Sans JP', sans-serif;
    font-size: 13px; line-height: 2.4; letter-spacing: 0.3em;
    color: #00F0FF; opacity: 0.035;
    transform: rotate(-10deg) translate(-15%, -15%);
    white-space: pre-wrap; overflow: hidden;
}
@media (prefers-reduced-motion: no-preference) {
    .hud-bg { animation: drift 90s linear infinite; }
}
@keyframes drift { from { transform: rotate(-10deg) translate(-15%, -15%); } to { transform: rotate(-10deg) translate(-25%, -5%); } }

/* Title */
.hud-title {
    font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 1.9rem;
    color: #E8ECFF; letter-spacing: 0.03em;
    text-shadow: 0 0 12px rgba(0,240,255,0.35), 0 0 2px rgba(0,240,255,0.6);
    margin-bottom: 0.2rem;
}
.pipeline-title {
    font-family: 'Rajdhani', sans-serif; font-weight: 600;
    font-size: 0.8rem; color: #6B7394;
    text-transform: uppercase; letter-spacing: 0.12em;
    margin-bottom: 1rem;
}

/* HUD corner-bracket frame */
.hud-frame {
    position: relative; border: 1px solid #1C2333; background: rgba(23,28,45,0.55);
    padding: 0.9rem 1.1rem; border-radius: 2px; margin-bottom: 1rem;
}
.hud-frame::before, .hud-frame::after,
.hud-frame .c2::before, .hud-frame .c2::after { content: ''; position: absolute; width: 10px; height: 10px; border-color: #00F0FF; }
.hud-frame::before { top: -1px; left: -1px; border-top: 2px solid #00F0FF; border-left: 2px solid #00F0FF; }
.hud-frame::after { bottom: -1px; right: -1px; border-bottom: 2px solid #00F0FF; border-right: 2px solid #00F0FF; }

.hud-title-wrap { font-family: 'JetBrains Mono', monospace; font-size: 1.05rem; color: #E8ECFF; }

.rail { display: flex; flex-direction: column; gap: 0; }
.rail-node { display: flex; align-items: flex-start; gap: 0.75rem; position: relative; padding-bottom: 1.5rem; }
.rail-node:last-child { padding-bottom: 0; }
.rail-dot {
    width: 12px; height: 12px; border-radius: 50%;
    border: 2px solid #1C2333; background: #10141F;
    flex-shrink: 0; margin-top: 2px; z-index: 1;
}
.rail-dot.pass { background: #00F0FF; border-color: #00F0FF; box-shadow: 0 0 8px rgba(0,240,255,0.6); }
.rail-dot.fail { background: #FF2E4A; border-color: #FF2E4A; box-shadow: 0 0 8px rgba(255,46,74,0.6); }
.rail-dot.pending { background: #7B61FF; border-color: #7B61FF; box-shadow: 0 0 8px rgba(123,97,255,0.6); }
.rail-line { position: absolute; left: 5px; top: 14px; bottom: -1.5rem; width: 2px; background: #1C2333; }
.rail-node:last-child .rail-line { display: none; }
.rail-label { font-family: 'Rajdhani', sans-serif; font-weight: 600; font-size: 0.9rem; color: #E8ECFF; letter-spacing: 0.03em; }
.rail-sub { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #6B7394; margin-top: 0.1rem; }

.status-badge {
    font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
    padding: 0.15rem 0.55rem; border-radius: 3px; display: inline-block;
    font-weight: 600; letter-spacing: 0.05em;
}
.status-pass { background: rgba(0,240,255,0.10); color: #00F0FF; border: 1px solid rgba(0,240,255,0.35); }
.status-fail { background: rgba(255,46,74,0.10); color: #FF2E4A; border: 1px solid rgba(255,46,74,0.35); }
.status-pending { background: rgba(123,97,255,0.10); color: #7B61FF; border: 1px solid rgba(123,97,255,0.35); }

button[kind="primary"] {
    background-color: #FF2E4A !important; border-color: #FF2E4A !important;
    font-family: 'Rajdhani', sans-serif !important; font-weight: 700 !important; letter-spacing: 0.05em !important;
    box-shadow: 0 0 14px rgba(255,46,74,0.4) !important;
}
button[kind="primary"]:hover { background-color: #ff1035 !important; border-color: #ff1035 !important; }
</style>

<div class="hud-bg">
バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち
バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち
バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち
バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち
バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち
バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち
バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち
バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち　バグ発見・自動修正・承認待ち
</div>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown("<div class='hud-title'> AI SOFTWARE ENGINEERING ASSISTANT</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='pipeline-title'>REQUIREMENTS → BUG INVESTIGATION (RAG) → CODING → "
    "REVIEW (REFLECTION) → TESTING (SELF-CORRECTING) + DOCS (PARALLEL) → GITHUB PR</div>",
    unsafe_allow_html=True
)

with st.sidebar:
    st.header("Target Issue")
    owner = st.text_input("Repo owner", value="pallets")
    repo = st.text_input("Repo name", value="click")
    issue_number = st.number_input("Issue number", value=3362, step=1)
    run_button = st.button("Run Pipeline", type="primary")

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
    try:
        with st.spinner("Running multi-agent pipeline..."):
            st.session_state.final_state = app.invoke(initial_state)
    except Exception as e:
        st.error(f"Pipeline failed: {e}")
        st.info("This can happen occasionally due to LLM output variability. Try clicking Run Pipeline again.")
        st.session_state.final_state = None

state = st.session_state.final_state

if state is None:
    st.info("Enter a repo + issue number in the sidebar and click **Run Pipeline** to start.")
else:
    st.markdown(
        f"<div class='hud-frame'><div class='hud-title-wrap'>{state['issue_title']}</div></div>",
        unsafe_allow_html=True
    )

    rail_col, content_col = st.columns([1, 3])

    requirements = state.get("requirements")
    investigation = state.get("investigation")
    fix = state.get("fix")
    review = state.get("review")
    test_results = state.get("test_results")
    docs = state.get("documentation")

    def node_status(done: bool, failed: bool = False) -> str:
        if failed:
            return "fail"
        return "pass" if done else "pending"

    nodes = [
        ("Requirements", node_status(requirements is not None), requirements.get("type") if requirements else ""),
        ("Bug Investigation", node_status(investigation is not None), investigation.get("confidence", "") if investigation else "skipped"),
        ("Coding", node_status(fix is not None), fix.get("risk_level", "") if fix else ""),
        ("Code Review", node_status(review is not None, failed=review is not None and not review["approved"]),
         "approved" if review and review["approved"] else ("rejected" if review else "")),
        ("Testing", node_status(test_results is not None, failed=test_results is not None and not test_results["tests_passed"]),
         f"{test_results.get('attempts_used', 1)} attempt(s)" if test_results else ""),
        ("Documentation", node_status(docs is not None), ""),
    ]

    with rail_col:
        st.markdown("<div class='pipeline-title'>PIPELINE</div>", unsafe_allow_html=True)
        rail_html = "<div class='hud-frame'><div class='rail'>"
        for label, status, sub in nodes:
            rail_html += (
                f"<div class='rail-node'>"
                f"<div style='position:relative;'>"
                f"<div class='rail-dot {status}'></div>"
                f"<div class='rail-line'></div>"
                f"</div>"
                f"<div>"
                f"<div class='rail-label'>{label}</div>"
                f"<div class='rail-sub'>{sub}</div>"
                f"</div>"
                f"</div>"
            )
        rail_html += "</div></div>"
        st.markdown(rail_html, unsafe_allow_html=True)

    with content_col:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Requirements", "Bug Investigation", "Fix", "Code Review", "Testing", "Documentation"
        ])

        with tab1:
            st.json(requirements)

        with tab2:
            if investigation:
                st.json(investigation)
            else:
                st.write("Not classified as a bug — investigation skipped.")

        with tab3:
            if fix:
                st.write("**Proposed approach:**")
                st.write(fix["proposed_approach"])
                st.markdown(
                    f"<span class='status-badge status-{'pass' if fix['risk_level']=='low' else 'pending'}'>"
                    f"{fix['risk_level'].upper()} RISK</span>",
                    unsafe_allow_html=True
                )
                st.code(fix["code_snippet"], language=fix["language"].lower())

        with tab4:
            if review:
                badge = "status-pass" if review["approved"] else "status-fail"
                label = "APPROVED" if review["approved"] else "REJECTED"
                st.markdown(f"<span class='status-badge {badge}'>{label}</span>", unsafe_allow_html=True)
                st.write(review["feedback"])
                if review["issues"]:
                    st.write("**Issues found:**")
                    for issue in review["issues"]:
                        st.write(f"- {issue}")

        with tab5:
            if test_results:
                badge = "status-pass" if test_results["tests_passed"] else "status-fail"
                label = "PASSED" if test_results["tests_passed"] else "FAILED"
                st.markdown(
                    f"<span class='status-badge {badge}'>{label}</span> "
                    f"&nbsp; attempts: {test_results.get('attempts_used', 1)}",
                    unsafe_allow_html=True
                )
                st.write(test_results["test_summary"])
                st.code(test_results["test_code"], language="python")
                with st.expander("Raw pytest output"):
                    st.code(test_results["execution_output"])

        with tab6:
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
                        st.success(f"Fix approved and PR opened!")
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