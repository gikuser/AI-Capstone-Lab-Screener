# Project Requirements Document (PRD) - Resume Screening System

## 1. Problem Statement
The current recruitment process for technical roles involves manual screening of hundreds of resumes, leading to bottlenecks, inconsistent evaluations, and delayed feedback for candidates. Recruiters often miss qualified candidates due to high volume, and the coordination between technical researchers and hiring managers is fragmented.

## 2. User Personas
- **The Recruiter (Technical Researcher Agent)**: Focuses on extracting data, scoring candidates against keywords, and finding technical alignment.
- **The Hiring Manager (Hiring Analyst Agent)**: Focuses on senior-level decision making, draft communication, and final approval.
- **The HR Administrator (Real Human)**: The final decision maker who reviews the AI-generated proposals and approves external communications.

## 3. Success Metrics
- **Reduction in Time-to-Screen**: Target < 2 minutes per resume (from hours).
- **Candidate Match Accuracy**: 90% alignment between AI scores and manual reviewer scores.
- **Human Review Rate**: 100% of external emails must pass human review (Safety/HITL).

## 4. High-Level Architecture
- **Perceive**: PDF Parsing + Vector DB (FAISS for HR guidelines).
- **Reason**: LangGraph orchestration with Specialized Agents.
- **Execute**: Email drafting with Human-in-the-Loop approval.
