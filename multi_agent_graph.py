# multi_agent_graph.py

from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from tools import search_resumes, calculate_match_score

# --------------------------------------------------
# Graph State
# --------------------------------------------------

class TeamState(TypedDict):
    messages: List[BaseMessage]
    research_done: bool


# --------------------------------------------------
# LLMs
# --------------------------------------------------

research_llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0
)

analysis_llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0
)

# Tool access ONLY for Research Agent
research_tools = [search_resumes, calculate_match_score]
research_llm = research_llm.bind_tools(research_tools)

# --------------------------------------------------
# Agent A: Resume Researcher
# --------------------------------------------------

def research_agent(state: TeamState):
    """
    Agent A gathers resume data and computes scores.
    """
    response = research_llm.invoke(state["messages"])

    # Signal completion explicitly
    done_signal = AIMessage(
        content="RESEARCH_COMPLETE: Resume data gathered and scored."
    )

    return {
        "messages": state["messages"] + [response, done_signal],
        "research_done": True
    }


# --------------------------------------------------
# Agent B: Hiring Analyst
# --------------------------------------------------

def analyst_agent(state: TeamState):
    """
    Agent B synthesizes findings into final recommendation.
    """
    response = analysis_llm.invoke([
        HumanMessage(
            content=(
                "You are a hiring analyst. Based ONLY on the research results "
                "provided, recommend the best candidate and explain why."
            )
        )
    ] + state["messages"])

    return {
        "messages": state["messages"] + [response],
        "research_done": True
    }


# --------------------------------------------------
# Router (Handover Logic)
# --------------------------------------------------

def router(state: TeamState):
    """
    Routes control from Researcher to Analyst once research is done.
    """
    if state.get("research_done"):
        return "analyst"

    return "research"


# --------------------------------------------------
# Graph Construction
# --------------------------------------------------

graph = StateGraph(TeamState)

graph.add_node("research", research_agent)
graph.add_node("analyst", analyst_agent)

graph.set_entry_point("research")

graph.add_conditional_edges(
    "research",
    router,
    {
        "analyst": "analyst",
        "research": "research"
    }
)

graph.add_edge("analyst", END)

app = graph.compile()
