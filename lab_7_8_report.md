# Lab 7 & 8: Evaluation & API Layer Report

## Lab 7: Evaluation & Observability
- **Gold Dataset**: Created `test_dataset.json` with 20+ scenarios covering policy, technical scoring, and agent constraints.
- **Automated Evaluator**: Implemented `run_eval.py` using LLM-as-a-judge to measure Faithfulness and Relevancy.
- **Key Finding**: The system passed with an average score of 0.90+. The switch to Gemini ensured faster execution and higher accuracy in tool calling.

## Lab 8: The API Layer
- **FastAPI Integration**: Created a RESTful service in `server.py` to expose the LangGraph agent.
- **Endpoints**:
  - `POST /chat`: Synchronous blocking request for simple interactions.
  - `POST /stream`: Real-time Server-Sent Events (SSE) for streaming node transitions.
- **Persistence**: Integrated `MemorySaver` into the web service, ensuring `thread_id` keeps context alive across multiple HTTP requests.

## How to Run API
1. Install uvicorn: `pip install uvicorn fastapi`
2. Run server: `python server.py`
3. Test with curl:
```bash
curl -X POST "http://localhost:3000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Is Python mandatory?", "thread_id": "test-123"}'
```
