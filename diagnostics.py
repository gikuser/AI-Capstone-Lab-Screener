# 🧪 AI Lab Project: Diagnostic Test Suite

import io
from langchain_core.messages import HumanMessage
from tools import parse_pdf_resume, calculate_match_score
from approval_logic import app, research_agent, analyst_agent

def test_step(name):
    print(f"\n{'='*20}")
    print(f"RUNNING TEST: {name}")
    print(f"{'='*20}\n")

def run_diagnostics():
    # 1. Test PDF Parsing
    test_step("1. PDF Parsing")
    try:
        dummy_pdf_content = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 50 >>\nstream\nBT /F1 12 Tf 100 700 Td (Candidate: John Doe. Skills: Python, AI) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000059 00000 n\n0000000121 00000 n\n0000000188 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n288\n%%EOF"
        text = parse_pdf_resume.invoke({"file_bytes": dummy_pdf_content})
        print(f"✅ PDF parsed successfully. Content preview: {text[:50]}...")
    except Exception as e:
        print(f"❌ PDF Parsing Failed: {str(e)}")

    # 2. Test Tools
    test_step("2. Tools (Score)")
    try:
        score = calculate_match_score.invoke({"resume_text": "Python developer", "job_description": "Python"})
        print(f"✅ calculate_match_score returned: {score}")
    except Exception as e:
        print(f"❌ Tool Execution Failed: {str(e)}")

    # 3. Test Researcher Agent
    test_step("3. Researcher Agent")
    try:
        state = {
            "messages": [HumanMessage(content="Find a Python dev.")],
            "research_done": False,
            "research_steps": 0,
            "proposed_email": None,
            "approved": False
        }
        result = research_agent(state)
        print(f"✅ Researcher Agent responded. Done status: {result['research_done']}")
    except Exception as e:
        print(f"❌ Researcher Agent Failed: {str(e)}")

if __name__ == "__main__":
    run_diagnostics()
