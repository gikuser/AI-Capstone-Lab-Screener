# approval_logic.py

from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from tools import calculate_match_score, search_hiring_guidelines

# --------------------------------------------------
# State Definition
# --------------------------------------------------

class HITLState(TypedDict):
    messages: List[BaseMessage]
    research_done: bool
    proposed_email: Optional[str]
    approved: bool
    research_steps: int


# --------------------------------------------------
# LLM Setup
# --------------------------------------------------

# Using Gemini 3 Flash for speed and efficiency in screening
research_llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0
).bind_tools([calculate_match_score, search_hiring_guidelines])

analysis_llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0
)


# --------------------------------------------------
# Agent A – Researcher
# Receives: resume text + job description
# Does: calls calculate_match_score ONCE, summarizes
# --------------------------------------------------

def research_agent(state: HITLState):
    steps = state.get("research_steps", 0)

    # Hard limit
    if steps >= 3:
        last_msgs = "\n".join(
            m.content for m in state["messages"] if hasattr(m, "content") and m.content
        )
        return {
            "messages": state["messages"] + [AIMessage(content=f"RESEARCH_COMPLETE: Evaluation results gathered. Proceeding to Analyst.")],
            "research_done": True,
            "research_steps": steps + 1
        }

    system_msg = SystemMessage(content=(
        "You are a technical Researcher for a hiring system. "
        "The user has provided a candidate's resume text and a job description. "
        "Steps: "
        "1. Optionally call search_hiring_guidelines to retrieve company policy context for the role. "
        "2. Call calculate_match_score ONCE with the resume_text and job_description. "
        "After gathering data, write a brief summary of the candidate's match considering the guidelines and then STOP."
    ))

    # Only pass the original user message (avoid confusing the model with its own previous attempts)
    response = research_llm.invoke([system_msg, state["messages"][0]])

    is_done = len(response.tool_calls) == 0

    return {
        "messages": state["messages"] + [response],
        "research_done": is_done,
        "research_steps": steps + 1
    }


# --------------------------------------------------
# Tool Executor Node (manually handle tool results)
# --------------------------------------------------

from langchain_core.messages import ToolMessage
import json

def tool_executor(state: HITLState):
    last_message = state["messages"][-1]
    tool_results = []

    for tool_call in last_message.tool_calls:
        args = tool_call["args"]
        if tool_call["name"] == "calculate_match_score":
            result = calculate_match_score.invoke(args)
            tool_results.append(
                ToolMessage(
                    content=json.dumps(result),
                    tool_call_id=tool_call["id"]
                )
            )
        elif tool_call["name"] == "search_hiring_guidelines":
            result = search_hiring_guidelines.invoke(args)
            tool_results.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                )
            )

    return {"messages": state["messages"] + tool_results}


# --------------------------------------------------
# Agent B – Analyst
# Receives: research summary + score
# Does: writes professional email (interview invite or rejection)
# --------------------------------------------------

def analyst_agent(state: HITLState):
    system_msg = SystemMessage(content=(
        "You are a senior Hiring Analyst. "
        "Review the candidate evaluation research. "
        "Write a short, professional email to the candidate: "
        "- If match score >= 40: invite them for an interview. "
        "- If match score < 40: politely inform them they did not meet requirements. "
        "Sign off as 'AI Hiring Team'. Output the email text only."
    ))

    response = analysis_llm.invoke([system_msg] + state["messages"])

    return {
        "messages": state["messages"] + [response],
        "proposed_email": response.content,
        "approved": False
    }


# --------------------------------------------------
# Send Email (simulated)
# --------------------------------------------------

def send_email_agent(state: HITLState):
    email_body = state["proposed_email"]
    confirmation = AIMessage(content=f"✅ EMAIL SENT SUCCESSFULLY:\n\n{email_body}")
    return {
        "messages": state["messages"] + [confirmation],
        "approved": True
    }


# --------------------------------------------------
# Router Logic
# --------------------------------------------------

def router(state: HITLState):
    last_message = state["messages"][-1]

    # If last AI message has tool calls, execute them
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"

    # If research is done or limit hit, go to analyst
    if state.get("research_done") or state.get("research_steps", 0) >= 3:
        return "analysis"

    # Otherwise, keep researching
    return "research"


# --------------------------------------------------
# Checkpointer (In-Memory)
# --------------------------------------------------

checkpointer = MemorySaver()


# --------------------------------------------------
# Graph Construction
# --------------------------------------------------

graph = StateGraph(HITLState)

graph.add_node("research", research_agent)
graph.add_node("tools", tool_executor)
graph.add_node("analysis", analyst_agent)
graph.add_node("send_email", send_email_agent)

graph.set_entry_point("research")

graph.add_conditional_edges(
    "research",
    router,
    {
        "tools": "tools",
        "research": "research",
        "analysis": "analysis",
    }
)

graph.add_edge("tools", "research")
graph.add_edge("analysis", "send_email")

app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["send_email"]
)
