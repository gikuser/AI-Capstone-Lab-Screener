# persistence_test.py

from langchain_core.messages import HumanMessage
from approval_logic import app

THREAD_ID = "student-session-001"

# --------------------------------------------------
# First Run
# --------------------------------------------------

print("\n--- FIRST RUN ---\n")

state = {
    "messages": [
        HumanMessage(
            content="Find the best ML engineer with NLP experience."
        )
    ],
    "research_done": False,
    "proposed_email": None,
    "approved": False,
    "research_steps": 0
}

result = app.invoke(
    state,
    config={"configurable": {"thread_id": THREAD_ID}}
)

for msg in result["messages"]:
    if hasattr(msg, "content"):
        print(msg.content)

print("\n--- STOP SCRIPT NOW ---\n")


# --------------------------------------------------
# Resume Execution
# --------------------------------------------------

print("\n--- RESUMING SESSION ---\n")

resumed = app.invoke(
    None,
    config={"configurable": {"thread_id": THREAD_ID}}
)

for msg in resumed["messages"]:
    if hasattr(msg, "content"):
        print(msg.content)



# HUMAN EDIT STEP (simulate approval UI)

edited_state = resumed

edited_state["proposed_email"] = """
Dear Candidate,

We were impressed by your NLP background.
We would like to invite you for a technical interview next week.

Best regards,
AI Lab Hiring Team
"""

# Approve and resume
final = app.invoke(
    edited_state,
    config={"configurable": {"thread_id": THREAD_ID}}
)

for msg in final["messages"]:
    if hasattr(msg, "content"):
        print(msg.content)
