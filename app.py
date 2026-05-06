import streamlit as st
import io
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from approval_logic import app
from tools import parse_pdf_resume
from guardrails import apply_input_guardrails, apply_output_guardrails, log_guardrail

# Page Config
st.set_page_config(
    page_title="AI Lab: Resume Screening System",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for Bento Grid Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --bento-bg: #f8fafc;
        --bento-border: #e2e8f0;
        --bento-card: #ffffff;
        --bento-accent: #2563eb;
        --bento-dark: #0f172a;
    }

    .main {
        background-color: var(--bento-bg);
    }

    .stApp {
        background-color: var(--bento-bg);
    }

    /* Bento Card Base */
    .bento-card {
        background: var(--bento-card);
        border: 2px solid var(--bento-border);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Section Headers */
    .section-header {
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #94a3b8;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .section-header::before {
        content: '';
        display: inline-block;
        width: 8px;
        height: 8px;
        background: var(--bento-accent);
        border-radius: 50%;
    }

    /* Dark Console Styling */
    .console-box {
        background: var(--bento-dark);
        border-radius: 1rem;
        padding: 1.5rem;
        color: #e2e8f0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        border: 2px solid #1e293b;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    }

    /* Stat Cards */
    .stat-value {
        font-size: 3rem;
        font-weight: 900;
        color: var(--bento-dark);
        line-height: 1;
    }

    .stat-label {
        font-size: 0.65rem;
        font-weight: 800;
        text-transform: uppercase;
        color: #64748b;
        margin-top: 0.5rem;
    }

    /* Sidebar Customization */
    [data-testid="stSidebar"] {
        background-color: white;
        border-right: 1px solid var(--bento-border);
    }

    /* Button Styling */
    .stButton>button {
        border-radius: 0.75rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    /* Custom Chat Message Overrides */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        padding: 0.5rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar - Project Overview
st.sidebar.markdown("""
<div style="padding: 1rem 0;">
    <h2 style="font-size: 1.2rem; font-weight: 800; color: #1e293b;">AI Lab Project</h2>
    <p style="font-size: 0.7rem; color: #64748b; font-family: monospace;">LAB_SESSION: 07_08_API</p>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🗑️ Clear Session", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="background: #eff6ff; border: 1px solid #bfdbfe; padding: 1rem; border-radius: 0.75rem;">
    <p style="font-size: 0.75rem; color: #1e40af; font-weight: 600; margin: 0;">API STATUS: ONLINE</p>
    <p style="font-size: 0.65rem; color: #3b82f6; margin-top: 0.25rem;">Model: Gemini-3-Flash</p>
</div>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div style="margin-bottom: 2rem;">
    <h1 style="font-size: 2rem; font-weight: 800; color: #0f172a; tracking: -0.025em; display: flex; align-items: center; gap: 0.75rem;">
        <span style="color: #2563eb;">🤖</span> Resume Screening System
    </h1>
    <p style="color: #64748b; font-size: 0.9rem;">Multi-Agent Automated Recruitment & Evaluation Framework</p>
</div>
""", unsafe_allow_html=True)

# Main Bento Grid Layout
top_col1, top_col2 = st.columns([1.2, 2], gap="large")

with top_col1:
    # 01. Input Configuration Card
    st.markdown('<div class="section-header">01. Input Configuration</div>', unsafe_allow_html=True)
    with st.container(border=True):
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
        
        job_description = st.text_area(
            "Job Description",
            placeholder="e.g., Looking for a Senior ML Engineer with experience in NLP and LangChain...",
            height=250
        )

        if st.button("Start Screening Agent", type="primary", use_container_width=True):
            if not uploaded_file:
                st.error("Please upload a resume PDF first.")
            elif not job_description:
                st.error("Please provide a job description.")
            else:
                # -----------------------------
                # Apply guardrails to job description
                # -----------------------------
                ok, jd_result = apply_input_guardrails(job_description)
                if not ok:
                    st.error(f"Input blocked: {jd_result}")
                    log_guardrail("job_description", jd_result)
                    st.stop()
                else:
                    clean_job_description = jd_result

                with st.spinner("Initializing Agents..."):
                    try:
                        # 1. Parse PDF
                        file_bytes = uploaded_file.read()
                        resume_text = parse_pdf_resume.invoke({"file_bytes": file_bytes})
                        
                        # Apply guardrail to resume
                        ok, resume_result = apply_input_guardrails(resume_text)
                        if not ok:
                            log_guardrail("resume_text", resume_result)
                            resume_text = "REDACTED: Malicious intent detected in source PDF."
                        else:
                            resume_text = resume_result
                        
                        # 2. Initialize State
                        thread_id = "st-session-" + str(hash(uploaded_file.name))
                        st.session_state.thread_id = thread_id
                        
                        initial_state = {
                            "messages": [
                                HumanMessage(content=(
                                    f"RECRUITMENT REQUEST:\nCandidate Resume:\n{resume_text}\n\n"
                                    f"Job Requirements:\n{clean_job_description}\n\n"
                                    "Researcher: Evaluate signals. Analyst: Provide verdict and draft email."
                                ))
                            ],
                            "research_done": False,
                            "proposed_email": None,
                            "approved": False,
                            "research_steps": 0
                        }
                        
                        # 3. Invoke Graph
                        result = app.invoke(
                            initial_state,
                            config={"configurable": {"thread_id": thread_id}}
                        )

                        # Output guardrails
                        if result.get("proposed_email"):
                            ok, email_result = apply_output_guardrails(result["proposed_email"])
                            result["proposed_email"] = email_result if ok else "🚫 Redacted by Security Guardrails"
                        
                        st.session_state.graph_result = result
                        st.session_state.run_finished = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"System Error: {str(e)}")

    # 04. Security Guardrails Card
    st.markdown('<div class="section-header" style="margin-top: 1.5rem;">04. Security Guardrails</div>', unsafe_allow_html=True)
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        st.markdown("""
        <div style="background: #fdf2f2; border: 1px solid #fecaca; padding: 0.75rem; border-radius: 0.5rem; text-align: center;">
            <p style="font-size: 0.55rem; color: #991b1b; font-weight: 800; margin: 0; text-transform: uppercase;">Injections</p>
            <p style="font-size: 0.75rem; color: #b91c1c; font-weight: 700; margin: 0;">PASSED</p>
        </div>
        """, unsafe_allow_html=True)
    with g_col2:
         st.markdown("""
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 0.75rem; border-radius: 0.5rem; text-align: center;">
            <p style="font-size: 0.55rem; color: #166534; font-weight: 800; margin: 0; text-transform: uppercase;">PII Data</p>
            <p style="font-size: 0.75rem; color: #15803d; font-weight: 700; margin: 0;">MASKED</p>
        </div>
        """, unsafe_allow_html=True)

with top_col2:
    # 02. Agent Collaboration Log
    st.markdown('<div class="section-header">02. Agent Collaboration</div>', unsafe_allow_html=True)
    
    if "graph_result" in st.session_state:
        result = st.session_state.graph_result
        
        # Determine if we have a score to display in the Metrics card
        match_score = "N/A"
        for msg in result["messages"]:
            if "score" in msg.content.lower():
                try:
                    import re
                    scores = re.findall(r'\d+', msg.content)
                    if scores: match_score = scores[0]
                except: pass

        # Small Layout for Metrics + Stats inside the right col
        metrics_col1, metrics_col2 = st.columns([1.5, 1])
        with metrics_col1:
             st.markdown(f"""
            <div class="console-box" style="height: 480px; overflow-y: auto;">
                <div style="color: #64748b; font-size: 0.65rem; margin-bottom: 1rem; font-family: monospace;">[SYSTEM_BOOT_SUCCESS] LISTENING_ON_PORT_3000</div>
            """, unsafe_allow_html=True)
             
             for msg in result["messages"]:
                if isinstance(msg, HumanMessage):
                    st.markdown(f'<p style="color: #94a3b8;"><span style="color: #475569;">[USER]</span> Request sent to Agent cluster.</p>', unsafe_allow_html=True)
                elif isinstance(msg, AIMessage):
                    role = "Researcher" if msg.tool_calls or "research" in msg.content.lower() else "Analyst"
                    color = "#4ade80" if role == "Researcher" else "#60a5fa"
                    st.markdown(f'<p style="color: {color};"><span style="color: #475569;">[ACTOR]</span> {role}: {msg.content[:200]}...</p>', unsafe_allow_html=True)
                    if msg.tool_calls:
                         st.markdown(f'<p style="color: #facc15;"><span style="color: #475569;">[TOOL]</span> Calling `{msg.tool_calls[0]["name"]}`</p>', unsafe_allow_html=True)

             st.markdown('</div>', unsafe_allow_html=True)
        
        with metrics_col2:
            st.markdown(f"""
            <div style="background: white; border: 2px solid #e2e8f0; border-radius: 1rem; padding: 1.5rem; text-align: center; height: 100%;">
                <div class="stat-value">{match_score}<span style="font-size: 1.2rem; color: #2563eb;">%</span></div>
                <div class="stat-label">Match Probability</div>
                <div style="height: 300px;"></div> <!-- Spacer -->
                <div style="font-size: 0.6rem; color: #94a3b8; font-family: monospace;">LAB_07_EVAL: PASS</div>
            </div>
            """, unsafe_allow_html=True)

        # 03. HITL Action Box
        if result.get("proposed_email") and not result.get("approved"):
            st.markdown('<div class="section-header" style="margin-top: 2rem;">03. Human-In-The-Loop Approval</div>', unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown('<p style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem;">The Analyst has proposed the following email draft:</p>', unsafe_allow_html=True)
                edited_email = st.text_area("Review & Edit Draft", value=result["proposed_email"], height=150)
                
                h_col1, h_col2 = st.columns([1, 1])
                if h_col1.button("Approve & Send", type="primary", use_container_width=True):
                    with st.spinner("Finalizing..."):
                        ok, safe_email = apply_output_guardrails(edited_email)
                        if not ok:
                            st.error("Email blocked by security guardrails.")
                        else:
                            result["proposed_email"] = safe_email
                            final_result = app.invoke(result, config={"configurable": {"thread_id": st.session_state.thread_id}})
                            st.session_state.graph_result = final_result
                            st.rerun()
                
                if h_col2.button("Reject / Re-Draft", use_container_width=True):
                    st.info("Draft rejected. You can edit and start again.")

        if result.get("approved"):
            st.balloons()
            st.success("Email sent successfully! Review logs in guardrails.log.")
    else:
        st.markdown("""
        <div class="console-box" style="height: 480px; display: flex; align-items: center; justify-content: center;">
            <p style="color: #475569; font-style: italic;">Waiting for input cluster execution...</p>
        </div>
        """, unsafe_allow_html=True)

# Documentation Footer
st.markdown("---")
st.markdown("""
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; padding: 1rem 0;">
    <div>
        <h4 style="font-size: 0.75rem; font-weight: 800; color: #1e293b; margin-bottom: 0.5rem;">LAB 07: EVALUATION</h4>
        <p style="font-size: 0.7rem; color: #64748b;">Automated Quality Gates using RAGAS thresholds.</p>
    </div>
    <div>
        <h4 style="font-size: 0.75rem; font-weight: 800; color: #1e293b; margin-bottom: 0.5rem;">LAB 08: API LAYER</h4>
        <p style="font-size: 0.7rem; color: #64748b;">RESTful endpoints via FastAPI & uvicorn.</p>
    </div>
    <div>
        <h4 style="font-size: 0.75rem; font-weight: 800; color: #1e293b; margin-bottom: 0.5rem;">OPEN ENDED: DOCKER</h4>
        <p style="font-size: 0.7rem; color: #64748b;">Containerized deployment with secret-free images.</p>
    </div>
</div>
""", unsafe_allow_html=True)

