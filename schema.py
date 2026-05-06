from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    thread_id: str

class ChatResponse(BaseModel):
    response: str
    status: str
    thread_id: str
    approved: bool
    proposed_email: Optional[str] = None
