from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from schema import ChatRequest, ChatResponse
from approval_logic import app as graph_app
from langchain_core.messages import HumanMessage
import json
import asyncio

app = FastAPI(title="Resume Screening API")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    \"\"\"
    Synchronous endpoint for agent interaction.
    \"\"\"
    try:
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "research_done": False,
            "proposed_email": None,
            "approved": False,
            "research_steps": 0
        }
        
        config = {"configurable": {"thread_id": request.thread_id}}
        result = graph_app.invoke(initial_state, config=config)
        
        last_msg = result["messages"][-1].content
        
        return ChatResponse(
            response=last_msg,
            status="success",
            thread_id=request.thread_id,
            approved=result.get("approved", False),
            proposed_email=result.get("proposed_email")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stream")
async def stream_endpoint(request: ChatRequest):
    \"\"\"
    Streaming endpoint using Server-Sent Events (SSE).
    \"\"\"
    async def event_generator():
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "research_done": False,
            "proposed_email": None,
            "approved": False,
            "research_steps": 0
        }
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # Use graph.astream for node-by-node updates
        async for event in graph_app.astream(initial_state, config=config):
            node_name = list(event.keys())[0]
            data = {
                "node": node_name,
                "content": str(event[node_name].get("messages", [""])[-1]) if "messages" in event[node_name] else "Processing..."
            }
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
